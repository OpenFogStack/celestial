/*
* This file is part of Celestial (https://github.com/OpenFogStack/celestial).
* Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
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

package virt

import (
	"net"
	"sync"

	"github.com/firecracker-microvm/firecracker-go-sdk"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type state uint8

const (
	REGISTERED state = iota
	STARTED
	STOPPED
	KILLED
)

const HOST_INTERFACE = "ens4"
const GUESTINTERFACE = "eth0"
const ROOTPATH = "/celestial"
const OUTPUTPATH = "/celestial/out"

var (
	IPTABLES_BIN string
	IP_BIN       string
	SYSCTL_BIN   string
	DD_BIN       string
	MKFS_BIN     string
)

type network struct {
	ip      net.IPNet
	gateway net.IPNet
	network net.IPNet
	mac     net.HardwareAddr
	tap     string
}

type machine struct {
	name string

	state state

	vcpucount  uint8
	ram        uint64
	disksize   uint64
	diskimage  string
	kernel     string
	bootparams []string

	network network

	vm *firecracker.Machine
}

// Virt provides virtualization functionality using firecracker.
type Virt struct {
	hostInterface string
	initDelay     uint64 // ignored
	pb            PeeringBackend
	neb           NetworkEmulationBackend

	machines map[orchestrator.MachineID]*machine
	sync.RWMutex
}

// PeeringBackend is the interface for the peering backend.
type PeeringBackend interface {
	GetHostID() (uint8, error)
	Route(network net.IPNet, host orchestrator.Host) error
	Stop() error
}

// NetworkEmulationBackend is the interface for the network emulation backend.
type NetworkEmulationBackend interface {
	Register(id orchestrator.MachineID, tap string) error
	SetBandwidth(source orchestrator.MachineID, target net.IPNet, bandwidth uint64) error
	SetLatency(source orchestrator.MachineID, target net.IPNet, latency uint32) error
	UnblockLink(source orchestrator.MachineID, target net.IPNet) error
	BlockLink(source orchestrator.MachineID, target net.IPNet) error
	Stop() error
}
