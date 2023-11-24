package virt

import (
	"net"

	"github.com/firecracker-microvm/firecracker-go-sdk"

	orchestrator "github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

type state uint8

const (
	REGISTERED state = iota
	STARTED
	STOPPED
	KILLED
)

const HOST_INTERFACE = "ens4"
const NAMESERVER = "1.1.1.1"
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

type Virt struct {
	hostInterface string
	initDelay     uint64 // ignored
	pb            PeeringBackend
	neb           NetworkEmulationBackend

	machines map[orchestrator.MachineID]*machine
}

type PeeringBackend interface {
	GetHostID() (uint8, error)
	Route(network net.IPNet, host orchestrator.Host) error
}

type NetworkEmulationBackend interface {
	Register(id orchestrator.MachineID, tap string) error
	SetBandwidth(source orchestrator.MachineID, target net.IPNet, bandwidth uint64) error
	SetLatency(source orchestrator.MachineID, target net.IPNet, latency uint32) error
	UnblockLink(source orchestrator.MachineID, target net.IPNet) error
	BlockLink(source orchestrator.MachineID, target net.IPNet) error
}
