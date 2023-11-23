package orchestrator2

import "net"

type VirtualizationBackend interface {
	RegisterMachine(machine MachineID, name string, host Host, config MachineConfig) error
	BlockLink(source MachineID, target MachineID) error
	UnblockLink(source MachineID, target MachineID) error
	SetLatency(source MachineID, target MachineID, latency uint32) error
	SetBandwidth(source MachineID, target MachineID, bandwidth uint64) error
	StopMachine(machine MachineID) error
	StartMachine(machine MachineID) error
	GetIPAddress(id MachineID) (net.IPNet, error)
	ResolveIPAddress(ip net.IP) (MachineID, error)
	Stop() error
}
