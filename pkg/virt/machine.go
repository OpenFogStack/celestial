package virt

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
	"syscall"

	"github.com/firecracker-microvm/firecracker-go-sdk"
	"github.com/firecracker-microvm/firecracker-go-sdk/client/models"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

func (m *machine) createNetwork() error {
	// remove old network tap if exists
	// don't care about errors here
	_ = removeNetworkDevice(m.network.tap, HOST_INTERFACE)

	// create new network tap
	err := createNetworkDevice(m.network.gateway, m.network.tap, HOST_INTERFACE)

	if err != nil {
		return err
	}

	return nil
}

func (m *machine) removeNetwork() error {
	// remove old network tap if exists
	// don't care about errors here
	_ = removeNetworkDevice(m.network.tap, HOST_INTERFACE)

	return nil
}

func (m *machine) initialize() error {
	// create the network config for our firecracker vm
	fcNetworkConfig := []firecracker.NetworkInterface{
		{
			StaticConfiguration: &firecracker.StaticNetworkConfiguration{
				MacAddress:  m.network.mac.String(),
				HostDevName: m.network.tap,
				IPConfiguration: &firecracker.IPConfiguration{
					IPAddr: net.IPNet{
						IP:   m.network.ip.IP,
						Mask: m.network.ip.Mask,
					},
					Gateway:     m.network.gateway.IP,
					Nameservers: []string{m.network.gateway.IP.String()},
					IfName:      GUESTINTERFACE,
				},
			},
		},
	}

	// prepare our root file system
	overlay := path.Join(ROOTPATH, fmt.Sprintf("ce%s.ext4", m.name))

	// dd if=/dev/zero of=[TARGET_OVERLAY_FILE] conv=sparse bs=1M count=[DISK_SIZE]
	cmd := exec.Command(DD_BIN, "if=/dev/zero", fmt.Sprintf("of=%s", overlay), "conv=sparse", "bs=1M", fmt.Sprintf("count=%d", m.disksize))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// mkfs.ext4 [TARGET_OVERLAY_FILE]
	cmd = exec.Command(MKFS_BIN, overlay)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	outPath := filepath.Join(OUTPUTPATH, fmt.Sprintf("%s.out", m.name))

	errPath := filepath.Join(OUTPUTPATH, fmt.Sprintf("%s.err", m.name))

	outFile, err := os.Create(outPath)

	if err != nil {
		return errors.WithStack(err)
	}

	errFile, err := os.Create(errPath)

	if err != nil {
		return errors.WithStack(err)
	}

	socketPath := getSocketPath(m.name)

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

	firecrackerProcessRunner, err := getFirecrackerProcessRunner(socketPath, outFile, errFile)

	if err != nil {
		return errors.WithStack(err)
	}

	loglevel := "DEBUG"

	switch log.GetLevel() {
	case log.DebugLevel:
		loglevel = "DEBUG"
	case log.InfoLevel:
		loglevel = "INFO"
	case log.ErrorLevel:
		loglevel = "ERROR"
	default:
		loglevel = "DEBUG"
	}

	// magic!
	bootparams := "init=/sbin/ceinit ro console=ttyS0 noapic reboot=k panic=1 random.trust_cpu=on pci=off tsc=reliable quiet ipv6.disable=1 nomodule overlay_root=vdb"

	for _, param := range m.bootparams {
		bootparams += " " + param
	}

	vm, err := firecracker.NewMachine(context.Background(), firecracker.Config{
		SocketPath:      socketPath,
		KernelImagePath: path.Join(ROOTPATH, m.kernel),
		KernelArgs:      bootparams,
		Drives: []models.Drive{
			{
				DriveID:      firecracker.String("root"),
				PathOnHost:   firecracker.String(path.Join(ROOTPATH, m.diskimage)),
				IsRootDevice: firecracker.Bool(true),
				IsReadOnly:   firecracker.Bool(true),
			},
			{
				DriveID:      firecracker.String("overlay"),
				PathOnHost:   firecracker.String(overlay),
				IsRootDevice: firecracker.Bool(false),
				IsReadOnly:   firecracker.Bool(false),
			},
		},
		MachineCfg: models.MachineConfiguration{
			MemSizeMib: firecracker.Int64(int64(m.ram)),
			VcpuCount:  firecracker.Int64(int64(m.vcpucount)),
		},
		LogLevel:          loglevel,
		NetworkInterfaces: fcNetworkConfig,
	}, firecrackerProcessRunner)

	if err != nil {
		return errors.WithStack(err)
	}

	m.vm = vm

	return nil
}

// getSocketPath provides a randomized socket path by building a unique filename
// and searching for the existence of directories {$HOME, os.TempDir()} and returning
// the path with the first directory joined with the unique filename. If we
// can't find a good path panics.
// This must have been copied from somewhere else, but I have no idea where.
func getSocketPath(id string) string {
	filename := strings.Join([]string{
		".firecracker.sock",
		strconv.Itoa(os.Getpid()),
		id,
		strconv.Itoa(rand.Intn(1000))},
		"-",
	)

	dir := os.TempDir()

	return filepath.Join(dir, filename)
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
