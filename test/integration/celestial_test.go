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
	"os"
	"os/exec"
	"strconv"
	"strings"
	"testing"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/netem"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/pkg/peer"
	"github.com/OpenFogStack/celestial/pkg/server"
	"github.com/OpenFogStack/celestial/pkg/virt"
	"github.com/OpenFogStack/celestial/proto/celestial"
)

const (
	rootfs = "ssh.img"
	kernel = "vmlinux.bin"
	key    = "id_ed25519"

	TEST_PEER_WGPORT      = 3000
	TEST_PEER_WGINTERFACE = "wg0"
	TEST_PEER_MASK        = "/26"
	TEST_PEER_KEYPATH     = "/celestial/privatekey"
	TEST_IF               = "ens4"
	TEST_INIT_DELAY       = 15
)

var o *orchestrator.Orchestrator
var s *server.Server

type m struct {
	id    int
	group int
	ip    *net.IP
}

var vms = []m{
	{
		id:    0,
		group: 1,
		ip:    &net.IP{10, 1, 0, 2},
	},
	{
		id:    1,
		group: 1,
		ip:    &net.IP{10, 1, 0, 6},
	},
}

func TestMain(m *testing.M) {
	log.SetLevel(log.DebugLevel)

	log.Debug("preparing integration test")

	pb, err := peer.New(TEST_PEER_MASK, TEST_PEER_KEYPATH, TEST_PEER_WGINTERFACE, TEST_PEER_WGPORT)

	if err != nil {
		panic(err)
	}

	neb := netem.New()

	vb, err := virt.New(TEST_IF, TEST_INIT_DELAY, pb, neb)

	if err != nil {
		panic(err)
	}

	log.Debug("creating orchestrator")

	o = orchestrator.New(vb)

	if err != nil {
		panic(err)
	}

	log.Debug("initializing server")

	s = server.New(o, pb)

	// init
	_, err = s.Register(context.Background(), &celestial.RegisterRequest{
		Host: 0,
	})

	if err != nil {
		panic(err)
	}

	log.Debug("initializing orchestrator")

	machines := make([]*celestial.Machine, len(vms))

	for i, vm := range vms {
		machines[i] = &celestial.Machine{
			Id: &celestial.MachineID{
				Group: uint32(vm.group),
				Id:    uint32(vm.id),
			},
			Host: 0,
			Config: &celestial.MachineConfig{
				Vcpucount: 1,
				Ram:       128,
				Disksize:  1024,
				Image:     rootfs,
				Kernel:    kernel,
			},
		}
	}

	_, err = s.Init(context.Background(), &celestial.InitRequest{
		Hosts: []*celestial.Host{
			{
				Id: 0,
			},
		},
		Machines: machines,
	})

	if err != nil {
		panic(err)
	}

	log.Debug("starting tests")

	status := m.Run()

	//uncomment this to wait for interrupt
	//s := make(chan os.Signal, 1)
	//signal.Notify(s, os.Interrupt)
	//
	//log.Info("waiting for interrupt")
	//<-s

	// run cleanup
	log.Debug("cleaning up")
	err = o.Stop()

	if err != nil {
		panic(err)
	}

	log.Debug("exiting")
	os.Exit(status)
}

func TestStart(t *testing.T) {

	machines := make([]*celestial.MachineState, len(vms))

	for i, vm := range vms {
		machines[i] = &celestial.MachineState{
			Id: &celestial.MachineID{
				Group: uint32(vm.group),
				Id:    uint32(vm.id),
			},
			Active: celestial.VMState_ACTIVE,
		}
	}

	_, err := s.Update(context.Background(), &celestial.UpdateRequest{
		Machinestates: machines,
	})

	if err != nil {
		t.Error(err)
	}

	if err != nil {
		log.Debug(err)
		t.Error(err)
	}

	// check if machines are actually reachable
	for _, vm := range vms {
		// retry this 10 times
		var out []byte
		for j := 0; j < 10; j++ {
			// run SSH command:
			// ssh root@[ip] echo "hello world"
			c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=1", "root@"+vm.ip.String(), "echo", "hello world")

			out, err = c.CombinedOutput()

			if err == nil {
				log.Debugf("machine %d is reachable after %d tries", vm.id, j)
				break
			}

			log.Debugf("machine %d is not reachable after %d tries, waiting 2 seconds", vm.id, j)
			time.Sleep(2 * time.Second)
		}

		if err != nil {
			log.Debug(string(out))
			t.Error(err)
		}

	}
}

// check that the correct IPs have been assigned
func TestIPs(t *testing.T) {
	for _, vm := range vms {
		assigned, err := o.InfoGetIPAddressByID(orchestrator.MachineID{
			Group: uint8(vm.group),
			Id:    uint32(vm.id),
		})

		if err != nil {
			t.Error(err)
		}

		if !assigned.Equal(*vm.ip) {
			t.Errorf("machine %d has wrong IP %s instead of %s", vm.id, assigned.String(), vm.ip.String())
		}
	}
}

// check that we can resolve ip to correct id
func TestResolve(t *testing.T) {
	for _, vm := range vms {
		id, err := o.InfoGetNodeByIP(*vm.ip)

		if err != nil {
			t.Error(err)
		}

		if id.ID.ID.Id != uint32(vm.id) {
			t.Errorf("machine %d has wrong ID %d instead of %d", vm.id, id.ID.ID.Id, vm.id)
		}

		if id.ID.ID.Group != uint8(vm.group) {
			t.Errorf("machine %d has wrong group %d instead of %d", vm.id, id.ID.ID.Group, 1)
		}
	}
}

// check what happens if we set a machine to inactive
func TestModify(t *testing.T) {
	v := 0

	_, err := s.Update(context.Background(), &celestial.UpdateRequest{
		Machinestates: []*celestial.MachineState{
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[v].group),
					Id:    uint32(vms[v].id),
				},
				Active: celestial.VMState_STOPPED,
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	log.Debug("machine set to unreachable, checking if it worked...")

	// check if machine is actually unreachable
	// run SSH command:
	// ssh root@[ip] echo "hello world"
	c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=1", "root@"+vms[v].ip.String(), "echo", "hello world")

	out, err := c.CombinedOutput()
	if err == nil {
		log.Debug(string(out))
		t.Error("machine is reachable")
	}

	log.Debugf("machine is not reachable")

	_, err = s.Update(context.Background(), &celestial.UpdateRequest{
		Machinestates: []*celestial.MachineState{
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[v].group),
					Id:    uint32(vms[v].id),
				},
				Active: celestial.VMState_ACTIVE,
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	if err != nil {
		t.Error(err)
	}

	// check if machines are actually reachable again
	// retry this 10 times

	for j := 0; j < 10; j++ {
		// run SSH command:
		// ssh root@[ip] echo "hello world"
		c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+vms[v].ip.String(), "echo", "hello world")

		out, err = c.CombinedOutput()

		if err == nil {
			log.Debugf("machine A is reachable after %d tries", j)
			break
		}

		log.Debugf("machine A is reachable after %d tries, waiting 2 seconds", j)
		time.Sleep(2 * time.Second)
	}

	if err != nil {
		log.Debugf(string(out))
		t.Error(err)
	}

}

// check what happens when we adapt the network latency between the machines
func testModifyLinks(t *testing.T, A int, B int, latency int) {
	_, err := s.Update(context.Background(), &celestial.UpdateRequest{
		Networkstates: []*celestial.NetworkState{
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[A].group),
					Id:    uint32(vms[A].id),
				},
				Links: []*celestial.Link{
					{
						Target: &celestial.MachineID{
							Group: uint32(vms[B].group),
							Id:    uint32(vms[B].id),
						},
						Latency:   uint32(latency * 1000), // convert to microseconds
						Bandwidth: 10000,
						Next: &celestial.MachineID{
							Group: uint32(vms[B].group),
							Id:    uint32(vms[B].id),
						},
					},
				},
			},
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[B].group),
					Id:    uint32(vms[B].id),
				},
				Links: []*celestial.Link{
					{
						Target: &celestial.MachineID{
							Group: uint32(vms[A].group),
							Id:    uint32(vms[A].id),
						},
						Latency:   uint32(latency * 1000), // convert to microseconds
						Bandwidth: 10000,
						Next: &celestial.MachineID{
							Group: uint32(vms[A].group),
							Id:    uint32(vms[A].id),
						},
					},
				},
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	x := func(A, B int) {
		// check if latency is actually set
		// run ping over SSH command:
		// ssh root@[ip1] ping -c 1 [ip2]
		c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+vms[A].ip.String(), "ping", "-c", "1", vms[B].ip.String())

		out, err := c.CombinedOutput()
		if err != nil {
			log.Debug(string(out))
			t.Error(err)
		}

		// check that latency is as expected (2*latency)
		// parse output of this form:
		//     PING 10.0.0.6 (10.0.0.6): 56 data bytes
		//     64 bytes from 10.0.0.6: seq=0 ttl=63 time=201.149 ms

		measured := -1.0
		for _, line := range strings.Split(string(out), "\n") {
			if strings.Contains(line, "time=") {
				p := strings.Split(strings.Split(line, "=")[3], " ")[0]
				log.Debugf("parsed latency %s", p)
				measured, err = strconv.ParseFloat(p, 64)
				if err != nil {
					t.Error(err)
				}
			}
		}

		if latency == -1 {
			t.Errorf("latency from %d to %d could not be determined", vms[A].id, vms[B].id)
		}

		// latency should not be out of a 5% range
		minlatency := float64(latency*2) * 0.95
		maxlatency := float64(latency*2) * 1.05
		if measured < minlatency || measured > maxlatency {
			t.Errorf("latency from %d to %d is not as expected: %.2f instead of %d", vms[A].id, vms[B].id, measured, latency*2)
		}
	}

	x(A, B)
	x(B, A)

}

func TestModifyLinks(t *testing.T) {
	A, B := 0, 1
	testModifyLinks(t, A, B, 100)
	testModifyLinks(t, A, B, 200)
	testModifyLinks(t, A, B, 300)
	testModifyLinks(t, A, B, 400)
}

// check that blocking a link works
func TestBlockLink(t *testing.T) {
	A := 0
	B := 1

	_, err := s.Update(context.Background(), &celestial.UpdateRequest{
		Networkstates: []*celestial.NetworkState{
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[A].group),
					Id:    uint32(vms[A].id),
				},
				Links: []*celestial.Link{
					{
						Target: &celestial.MachineID{
							Group: uint32(vms[B].group),
							Id:    uint32(vms[B].id),
						},
						Blocked: true,
					},
				},
			},
			{
				Id: &celestial.MachineID{
					Group: uint32(vms[B].group),
					Id:    uint32(vms[B].id),
				},
				Links: []*celestial.Link{
					{
						Target: &celestial.MachineID{
							Group: uint32(vms[A].group),
							Id:    uint32(vms[A].id),
						},
						Blocked: true,
					},
				},
			},
		},
	})

	if err != nil {
		t.Error(err)
	}

	x := func(A, B int) {
		// check if latency is actually set
		// run ping over SSH command:
		// ssh root@[ip1] ping -c 1 [ip2]
		c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+vms[A].ip.String(), "ping", "-c", "1", vms[B].ip.String())

		out, err := c.CombinedOutput()
		// ignore error, should fail!
		if err == nil {
			log.Debug(string(out))
			t.Errorf("host %d is reachable from host %d", B, A)
		}

		// parse output to check that host is unreachable
		unreachable := false
		for _, line := range strings.Split(string(out), "\n") {
			if strings.Contains(line, "Network unreachable") || strings.Contains(line, "100% packet loss") {
				unreachable = true
			}
		}

		if !unreachable {
			t.Errorf("host %d is reachable from host %d", B, A)
		}
	}

	x(A, B)
	x(B, A)
}

func TestDNS(t *testing.T) {
	// try modifying the DNS settings on the machine
	// need to get the gateway address of the machine
	A := 0
	gateway := net.IP{10, 1, 0, 1}

	// write the gateway ip into /etc/resolv.conf on the machine
	c := exec.Command("ssh", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "root@"+vms[A].ip.String(), "echo", "nameserver", gateway.String(), ">", "/etc/resolv.conf")

	out, err := c.CombinedOutput()

	if err != nil {
		log.Debug(string(out))
		t.Error(err)
	}
}
