//go:build linux && amd64

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

package main

import (
	"context"
	"net"
	"os/exec"
	"strconv"
	"strings"
	"testing"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/pkg/server"
	"github.com/OpenFogStack/celestial/proto/celestial"
)

const (
	rootfs = "ssh.img"
	kernel = "vmlinux.bin"
	key    = "id_ed255119"
)

var o *orchestrator.Orchestrator
var s *server.Server

var ips = []*net.IP{{10, 0, 0, 2}, {10, 0, 0, 6}}

func TestMain(m *testing.M) {
	log.SetLevel(log.DebugLevel)

	log.Debug("preparing integration test")
	initDelay := 1
	networkInterface := "ens4"
	var err error

	log.Debug("initializing orchestrator")

	o, err = orchestrator.New(false, initDelay, networkInterface, true)

	if err != nil {
		panic(err)
	}

	log.Debug("initializing server")

	s = server.New(o)

	// init
	_, err = s.Init(context.Background(), &celestial.InitRequest{
		Database:     false,
		DatabaseHost: "",
		Shellcount:   1,
		Shells: []*celestial.Shell{{
			Id:     0,
			Planes: 1,
		}}})

	if err != nil {
		panic(err)
	}

	log.Debug("initializing remotes")

	_, err = s.InitRemotes(context.Background(), &celestial.InitRemotesRequest{
		Index:       0,
		Remotehosts: []*celestial.RemoteHost{},
	})

	if err != nil {
		panic(err)
	}

	log.Debug("starting peering")

	_, err = s.StartPeering(context.Background(), &celestial.Empty{})

	if err != nil {
		panic(err)
	}

	log.Debug("starting server")

	m.Run()
}

func TestCreate(t *testing.T) {
	for i := 0; i < 2; i++ {
		_, err := s.CreateMachine(context.Background(), &celestial.CreateMachineRequest{
			Machine: &celestial.Machine{
				Shell: 0,
				Id:    uint64(i),
			},
			Firecrackerconfig: &celestial.FirecrackerConfig{
				Vcpu:       1,
				Mem:        128,
				Ht:         false,
				Disk:       1024,
				Kernel:     kernel,
				Rootfs:     rootfs,
				Bootparams: "random.trust_cpu=on",
			},
			Networkconfig: &celestial.NetworkConfig{
				Bandwidth: 1000,
			},
			Status: true,
		})

		if err != nil {
			t.Error(err)
		}
	}

	// wait 10 seconds
	log.Debugf("waiting 10 seconds before checking if machines are reachable")
	time.Sleep(10 * time.Second)

	// check if machines are actually reachable
	for i := 0; i < 2; i++ {
		// retry this 10 times
		var out []byte
		var err error
		for j := 0; j < 10; j++ {
			// run SSH command:
			// ssh root@[ip] echo "hello world"
			c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[i].String(), "echo", "hello world")

			out, err = c.CombinedOutput()

			if err == nil {
				log.Debugf("machine %d is reachable after %d tries", i, j)
				break
			}
			log.Debugf("machine %d is not reachable after %d tries, waiting 2 seconds", i, j)
			time.Sleep(2 * time.Second)
		}

		if err != nil {
			log.Debug(string(out))
			t.Error(err)
		}

	}
}

// check what happens if we set a machine to inactive
func TestModify(t *testing.T) {
	_, err := s.ModifyMachine(context.Background(), &celestial.ModifyMachineRequest{
		Machine: &celestial.Machine{
			Shell: 0,
			Id:    0,
		},
		Status: false,
	})

	if err != nil {
		t.Error(err)
	}

	// check if machine is actually unreachable
	// run SSH command:
	// ssh root@[ip] echo "hello world"
	c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[0].String(), "echo", "hello world")

	out, err := c.CombinedOutput()
	if err == nil {
		log.Debug(string(out))
		t.Error("machine is reachable")
	}
	log.Debugf("machine is not reachable: %s", err.Error())

	// set the machine to active again
	_, err = s.ModifyMachine(context.Background(), &celestial.ModifyMachineRequest{
		Machine: &celestial.Machine{
			Shell: 0,
			Id:    0,
		},
		Status: true,
	})

	if err != nil {
		t.Error(err)
	}

	// check if machines are actually reachable
	// retry this 10 times

	for j := 0; j < 10; j++ {
		// run SSH command:
		// ssh root@[ip] echo "hello world"
		c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[0].String(), "echo", "hello world")

		out, err = c.CombinedOutput()

		if err == nil {
			log.Debugf("machine A is reachable after %d tries", j)
			break
		}
		log.Debugf("machine A is not reachable after %d tries, waiting 2 seconds", j)
		time.Sleep(2 * time.Second)
	}

	if err != nil {
		log.Debugf(string(out))
		t.Error(err)
	}

}

// check what happens when we adapt the network latency between the machines
func TestModifyLinks(t *testing.T) {
	_, err := s.ModifyLinks(context.Background(), &celestial.ModifyLinksRequest{
		A: &celestial.Machine{
			Shell: 0,
			Id:    0,
		},
		Modify: []*celestial.ModifyLinkRequest{
			{
				B: &celestial.Machine{
					Shell: 0,
					Id:    1,
				},
				Latency:   100,
				Bandwidth: 10000,
			},
		},
		Remove: []*celestial.RemoveLinkRequest{},
	})

	if err != nil {
		t.Error(err)
	}

	_, err = s.ModifyLinks(context.Background(), &celestial.ModifyLinksRequest{
		A: &celestial.Machine{
			Shell: 0,
			Id:    1,
		},
		Modify: []*celestial.ModifyLinkRequest{
			{
				B: &celestial.Machine{
					Shell: 0,
					Id:    0,
				},
				Latency:   100,
				Bandwidth: 10000,
			},
		},
		Remove: []*celestial.RemoveLinkRequest{},
	})

	if err != nil {
		t.Error(err)
	}

	// check if latency is actually set
	// run ping over SSH command:
	// ssh root@[ip1] ping -c 1 [ip2]
	c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[0].String(), "ping", "-c", "1", ips[1].String())

	out, err := c.CombinedOutput()
	if err != nil {
		log.Debug(string(out))
		t.Error(err)
	}

	// check that latency is as expected (2*100)
	latency := -1
	for _, line := range strings.Split(string(out), "\n") {
		if strings.Contains(line, "time=") {
			latency, err = strconv.Atoi(strings.Split(line, "=")[1])
			if err != nil {
				t.Error(err)
			}
		}
	}

	if latency != -1 {
		t.Error("latency from A to B could not be determined")
	}

	// latency should not be out of a 5% range
	if latency < 190 || latency > 210 {
		t.Errorf("latency from A to B is not as expected: %d instead of %d", latency, 200)
	}

	// check on the other side
	// ssh root@[ip2] ping -c 1 [ip1]
	c = exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[1].String(), "ping", "-c", "1", ips[0].String())

	out, err = c.CombinedOutput()
	if err != nil {
		log.Debug(string(out))
		t.Error(err)
	}

	latency = -1
	for _, line := range strings.Split(string(out), "\n") {
		if strings.Contains(line, "time=") {
			latency, err = strconv.Atoi(strings.Split(line, "=")[1])
			if err != nil {
				t.Error(err)
			}
		}
	}

	if latency != -1 {
		t.Error("latency from B to A could not be determined")
	}

	// latency should not be out of a 5% range
	if latency < 190 || latency > 210 {
		t.Errorf("latency from B to A is not as expected: %d instead of %d", latency, 200)
	}

}

// check that blocking a link works
func TestBlockLink(t *testing.T) {
	_, err := s.ModifyLinks(context.Background(), &celestial.ModifyLinksRequest{
		A: &celestial.Machine{
			Shell: 0,
			Id:    0,
		},
		Modify: []*celestial.ModifyLinkRequest{},
		Remove: []*celestial.RemoveLinkRequest{
			{
				B: &celestial.Machine{
					Shell: 0,
					Id:    1,
				},
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	_, err = s.ModifyLinks(context.Background(), &celestial.ModifyLinksRequest{
		A: &celestial.Machine{
			Shell: 0,
			Id:    1,
		},
		Modify: []*celestial.ModifyLinkRequest{},
		Remove: []*celestial.RemoveLinkRequest{
			{
				B: &celestial.Machine{
					Shell: 0,
					Id:    0,
				},
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	// check if latency is actually set
	// run ping over SSH command:
	// ssh root@[ip1] ping -c 1 [ip2]
	c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[0].String(), "ping", "-c", "1", ips[1].String())

	out, err := c.CombinedOutput()
	if err != nil {
		log.Debug(string(out))
		t.Error(err)
	}

	// parse output to check that host is unreachable
	unreachableAtoB := false
	for _, line := range strings.Split(string(out), "\n") {
		if strings.Contains(line, "host unreachable") {
			unreachableAtoB = true
		}
	}

	if !unreachableAtoB {
		t.Error("host B is reachable from host A")
	}

	// check on the other side
	// ssh root@[ip2] ping -c 1 [ip1]
	c = exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+ips[1].String(), "ping", "-c", "1", ips[0].String())

	out, err = c.CombinedOutput()
	if err != nil {
		log.Debug(string(out))
		t.Error(err)
	}

	// parse output to check that host is unreachable
	unreachableBtoA := false
	for _, line := range strings.Split(string(out), "\n") {
		if strings.Contains(line, "host unreachable") {
			unreachableBtoA = true
		}
	}

	if !unreachableBtoA {
		t.Error("host A is reachable from host B")
	}
}
