/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, version 3.
*
* This program is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
**/

package orchestrator

import (
	"context"
	"fmt"
	"io"
	"io/fs"
	"math/rand"
	"net"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"sync/atomic"
	"syscall"

	"github.com/pkg/errors"

	"github.com/firecracker-microvm/firecracker-go-sdk"
	"github.com/firecracker-microvm/firecracker-go-sdk/client/models"
	log "github.com/sirupsen/logrus"
)

func makeMachineID(shell int64, id uint64) string {

	return fmt.Sprintf("%d-%d", shell, id)
}

func prepareRootFS(rootFS string, machineID string) (string, error) {
	targetFile := fmt.Sprintf("%s-ce%s", rootFS, machineID)

	sourceFileStat, err := os.Stat(rootFS)
	if err != nil {
		return targetFile, errors.WithStack(err)
	}

	if !sourceFileStat.Mode().IsRegular() {
		return targetFile, errors.Errorf("%s is not a regular file", rootFS)
	}

	source, err := os.Open(rootFS)

	if err != nil {
		return targetFile, errors.WithStack(err)
	}

	defer func(source *os.File) {
		err := source.Close()
		if err != nil {
			log.Error(err.Error())
		}
	}(source)

	destination, err := os.Create(targetFile)

	if err != nil {
		return targetFile, errors.WithStack(err)
	}

	defer func(destination *os.File) {
		err := destination.Close()
		if err != nil {
			log.Error(err.Error())
		}
	}(destination)

	_, err = io.Copy(destination, source)

	return targetFile, errors.WithStack(err)
}

func getFirecrackerProcessRunner(socketPath string, outFile io.Writer, errFile io.Writer) (firecracker.Opt, error) {
	// from https://github.com/firecracker-microvm/firectl

	firecrackerBinary, err := exec.LookPath("firecracker")
	if err != nil {
		return nil, errors.WithStack(err)
	}

	finfo, err := os.Stat(firecrackerBinary)
	if os.IsNotExist(err) {
		return nil, errors.Errorf("binary %q does not exist: %v", firecrackerBinary, err)
	}

	if err != nil {
		return nil, errors.Errorf("failed to stat binary, %q: %v", firecrackerBinary, err)
	}

	if finfo.IsDir() {
		return nil, errors.Errorf("binary, %q, is a directory", firecrackerBinary)
	} else if finfo.Mode()&0111 == 0 {
		return nil, errors.Errorf("binary, %q, is not executable. Check permissions of binary", firecrackerBinary)
	}

	return firecracker.WithProcessRunner(firecracker.VMCommandBuilder{}.
		WithBin(firecrackerBinary).
		WithSocketPath(socketPath).
		WithStdout(outFile).
		WithStderr(errFile).
		Build(context.Background())), nil
}

func (lm *localmachine) initialize() error {

	err := createNetworkDevice(lm.gateway, lm.tapName, lm.chainName, lm.ipBlockSet, lm.hostInterface)

	if err != nil {
		return errors.WithStack(err)
	}

	nextHandle, err := createQDisc(lm.tapName)

	if err != nil {
		return errors.WithStack(err)
	}

	lm.nextHandle = nextHandle
	lm.netInitialized = true

	networkInterfaces, err := getFirecrackerNetworkInterfaces(lm.ip, lm.gateway, lm.mac, lm.tapName)

	if err != nil {
		return errors.WithStack(err)
	}

	drive, err := prepareRootFS(path.Join(FCROOTPATH, lm.drivePath), lm.name)

	if err != nil {
		return errors.WithStack(err)
	}

	outFile, errFile, err := getFileWriters(lm.name)

	if err != nil {
		return errors.WithStack(err)
	}

	lm.outFile = outFile
	lm.errFile = errFile

	socketPath := getSocketPath(lm.name)

	err = os.Remove(socketPath)
	if err != nil {
		// continue
		var pathError *fs.PathError
		if errors.As(err, &pathError) {
			if pathError.Err != syscall.ENOENT {
				log.Errorf("Error removing old socket path: %s", err.Error())
			}
		} else {
			log.Errorf("Error removing old socket path: %s", err.Error())
		}
	}

	firecrackerProcessRunner, err := getFirecrackerProcessRunner(socketPath, lm.outFile, lm.errFile)

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := firecracker.NewMachine(context.Background(), firecracker.Config{
		SocketPath:      socketPath,
		KernelImagePath: path.Join(FCROOTPATH, lm.kernelImagePath),
		KernelArgs:      "console=ttyS0 noapic reboot=k panic=1 pci=off tsc=reliable quiet ipv6.disable=1 nomodules rw" + lm.bootparams,
		Drives: []models.Drive{{
			DriveID:      firecracker.String("1"),
			PathOnHost:   firecracker.String(drive),
			IsRootDevice: firecracker.Bool(true),
			IsReadOnly:   firecracker.Bool(false),
		}},
		MachineCfg: models.MachineConfiguration{
			HtEnabled:  firecracker.Bool(lm.htEnabled),
			MemSizeMib: firecracker.Int64(int64(lm.memSizeMiB)),
			VcpuCount:  firecracker.Int64(int64(lm.vCPUCount)),
		},
		NetworkInterfaces: networkInterfaces,
		LogLevel:          "Debug",
	}, firecrackerProcessRunner)

	if err != nil {
		return errors.WithStack(err)
	}

	lm.m = m

	lm.initialized = true

	log.Infof("Successfully created machine %s!", lm.name)

	// init all links
	for _, l := range lm.links {

		nextHandle := atomic.AddInt64(&lm.nextHandle, 1)

		l.handle = nextHandle

		if !l.blocked {

			err := createLink(lm.tapName, l.handle, l.sourceNet, l.targetNet)
			l.initialized = true

			if err != nil {
				return errors.WithStack(err)
			}

			err = updateDelay(lm.tapName, l.handle, l.latency, int(l.bandwidth))

			if err != nil {
				return errors.WithStack(err)
			}
		} else {
			err := blockLink(lm.ipBlockSet, l.targetNet)

			if err != nil {
				return errors.WithStack(err)
			}
		}
	}

	log.Infof("Successfully initialized %d network links for machine %s!", len(lm.links), lm.name)

	err = m.Start(context.Background())

	if err != nil {
		return errors.WithStack(err)
	}

	log.Infof("Successfully started machine %s!", lm.name)

	return nil
}

func (m *machine) create(i uint64, shell int64, name string, vCPUCount uint64, memSizeMiB uint64, htEnabled bool, bandwidth uint64, kernelImagePath string, drivePath string, bootparams string, hostInterface string) error {
	log.Infof("Creating machine %d with %d vcpus, %d MiB memory, ht=%t", i, vCPUCount, memSizeMiB, htEnabled)

	if name == "" {
		name = makeMachineID(shell, i)
	}

	m.localmachine.name = name

	ip, gateway, mac, tapName, chainName, ipBlockSet, err := getIPAddressMACAndTapName(shell, i)

	if err != nil {
		return errors.WithStack(err)
	}

	m.localmachine.ip = ip
	m.localmachine.gateway = gateway
	m.localmachine.mac = mac

	m.localmachine.tapName = tapName
	m.localmachine.chainName = chainName
	m.localmachine.ipBlockSet = ipBlockSet

	addr, network, err := net.ParseCIDR(ip)

	if err != nil {
		return errors.WithStack(err)
	}

	m.id = id(i)
	m.address = addr
	m.network = network

	m.localmachine.hostInterface = hostInterface

	m.localmachine.drivePath = drivePath
	m.localmachine.kernelImagePath = kernelImagePath
	m.localmachine.htEnabled = htEnabled
	m.localmachine.memSizeMiB = memSizeMiB
	m.localmachine.vCPUCount = vCPUCount
	m.localmachine.bandwidth = bandwidth
	m.localmachine.bootparams = bootparams

	log.Infof("Machine %d will get MAC %s, tap %s, and IP %s with Gateway %s", i, mac, tapName, ip, gateway)

	return nil
}

// checkExistsAndDir returns true if path exists and is a Dir
func checkExistsAndDir(path string) bool {
	// empty
	if path == "" {
		return false
	}
	// does it exist?
	if info, err := os.Stat(path); err == nil {
		// is it a directory?
		return info.IsDir()
	}
	return false
}

// getFileWriters creates files for stdout and stderr of the firecracker
// microVM so that we can log its output.
func getFileWriters(id string) (io.Writer, io.Writer, error) {

	if _, err := os.Stat(FCOUTFILEPATH); os.IsNotExist(err) {
		err = os.Mkdir(FCOUTFILEPATH, fs.FileMode(0755))
		if err != nil {
			return nil, nil, err
		}
	}

	outPath := filepath.Join(FCOUTFILEPATH, strings.Join([]string{
		"out",
		id},
		"-",
	))

	errPath := filepath.Join(FCOUTFILEPATH, strings.Join([]string{
		"err",
		id},
		"-",
	))

	outFile, err := os.Create(outPath)

	if err != nil {
		return nil, nil, errors.WithStack(err)
	}

	errFile, err := os.Create(errPath)

	if err != nil {
		return nil, nil, errors.WithStack(err)
	}

	return outFile, errFile, nil

}

// getSocketPath provides a randomized socket path by building a unique filename
// and searching for the existence of directories {$HOME, os.TempDir()} and returning
// the path with the first directory joined with the unique filename. If we
// can't find a good path panics.
func getSocketPath(id string) string {
	filename := strings.Join([]string{
		".firecracker.sock",
		strconv.Itoa(os.Getpid()),
		id,
		strconv.Itoa(rand.Intn(1000))},
		"-",
	)
	var dir string
	if d := os.Getenv("HOME"); checkExistsAndDir(d) {
		dir = d
	} else if checkExistsAndDir(os.TempDir()) {
		dir = os.TempDir()
	} else {
		panic("Unable to find a location for firecracker socket. 'It's not going to do any good to land on mars if we're stupid.' --Ray Bradbury")
	}

	return filepath.Join(dir, filename)
}
