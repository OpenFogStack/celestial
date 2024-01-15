package orchestrator

import "fmt"

type MachineState uint8

const (
	STOPPED MachineState = iota
	ACTIVE
)

const defaultLatency = 0
const defaultBandwidth = 1000_000_000

type Link struct {
	// Blocked is true if the link is blocked
	Blocked bool
	// Latency in microseconds
	Latency uint32
	// Bandwidth in bytes per second
	Bandwidth uint64

	// used for path reconstruction
	Next MachineID
}

type MachineID struct {
	// is 0 for ground stations
	Group uint8
	Id    uint32
}

func (m MachineID) String() string {
	return fmt.Sprintf("%d.%d", m.Group, m.Id)
}

func (m MachineID) lt(b MachineID) bool {
	return m.Group < b.Group || (m.Group == b.Group && m.Id < b.Id)
}

type Host uint8

type NetworkState map[MachineID]map[MachineID]*Link

type MachinesState map[MachineID]MachineState

type State struct {
	NetworkState
	MachinesState
}

type ISL struct {
	// Latency in microseconds
	Latency uint32
	// Bandwidth in bytes per second
	Bandwidth uint64
}

type machine struct {
	name   string
	Host   Host
	config MachineConfig
}

type MachineConfig struct {
	VCPUCount uint8
	// RAM in bytes
	RAM uint64
	// DiskSize in bytes
	DiskSize uint64
	// DiskImage is the path to the disk image
	DiskImage string
	// Kernel is the path to the kernel
	Kernel string
	// BootParams are the additional boot parameters
	BootParams []string
}
