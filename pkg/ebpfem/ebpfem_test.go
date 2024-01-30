//go:build linux && amd64
// +build linux,amd64

/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2024 Soeren Becker, Nils Japke, Tobias Pfandzelter, The
* OpenFogStack Team.
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

package ebpfem

import (
	"fmt"
	"net"
	"os/exec"
	"testing"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

const (
	HOST_IF = "ens4"
)

func TestMain(m *testing.M) {
	log.SetLevel(log.DebugLevel)

	m.Run()
}

func TestBasic(t *testing.T) {
	id := orchestrator.MachineID{
		Group: 1,
		Id:    1,
	}

	gateway := net.IPNet{
		IP:   net.IPv4(10, 1, 0, 1),
		Mask: net.IPv4Mask(255, 255, 255, 252),
	}

	tap := "test-1-1"

	e := New()

	// remove old network device (if it exists)
	// ip link del [TAP_NAME]

	cmd := exec.Command("ip", "link", "del", tap)

	if _, err := cmd.CombinedOutput(); err != nil {
		// ignore
	}

	// iptables -D FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command("iptables", "-D", "FORWARD", "-i", tap, "-o", HOST_IF, "-j", "ACCEPT")

	if _, err := cmd.CombinedOutput(); err != nil {
		// ignore
	}

	// create a tap device

	// ip tuntap add [TAP_NAME] mode tap

	cmd = exec.Command("ip", "tuntap", "add", tap, "mode", "tap")

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)

	}

	// set up proxy ARP
	// sysctl -w net.ipv4.conf.[TAP_NAME].proxy_arp=1
	cmd = exec.Command("sysctl", "-w", fmt.Sprintf("net.ipv4.conf.%s.proxy_arp=1", tap))

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)

	}

	// disable ipv6
	// sysctl -w net.ipv6.conf.[TAP_NAME].disable_ipv6=1
	cmd = exec.Command("sysctl", "-w", fmt.Sprintf("net.ipv6.conf.%s.disable_ipv6=1", tap))

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)

	}

	// ip addr add [IP_ADDRESS] dev [TAP_NAME]

	cmd = exec.Command("ip", "addr", "add", gateway.String(), "dev", tap)

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)
	}

	// ip link set [TAP_NAME] up

	cmd = exec.Command("ip", "link", "set", tap, "up")

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)

	}

	// iptables -A FORWARD -i [TAP_NAME] -o [HOSTINTERFACE] -j ACCEPT

	cmd = exec.Command("iptables", "-A", "FORWARD", "-i", tap, "-o", HOST_IF, "-j", "ACCEPT")

	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%#v: output: %s", cmd.Args, out)

	}

	log.Tracef("created tap %s", tap)
	log.Debug("starting ebpf stuff")

	// create a new machine with ebpfem
	err := e.Register(id, tap)

	if err != nil {
		t.Fatalf("error registering machine: %s", errors.WithStack(err))
	}

	// try to block a link
	target := net.IPNet{
		IP:   net.IPv4(10, 1, 0, 4),
		Mask: net.IPv4Mask(255, 255, 255, 252),
	}

	err = e.SetBandwidth(id, target, 100)

	if err != nil {
		t.Fatalf("error setting bandwidth: %s", errors.WithStack(err))
	}

	err = e.SetLatency(id, target, 100)

	if err != nil {
		t.Fatalf("error setting latency: %s", errors.WithStack(err))
	}

	err = e.BlockLink(id, target)

	if err != nil {
		t.Fatalf("error blocking link: %s", errors.WithStack(err))
	}
}
