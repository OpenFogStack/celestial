package virt

import (
	"net"

	orchestrator "github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

func (v *Virt) getNetwork(id orchestrator.MachineID) (net.IPNet, error) {
	n, err := getNet(id)
	if err != nil {
		return net.IPNet{}, err
	}

	return n.ip, nil
}

func (v *Virt) setbandwidth(source orchestrator.MachineID, target orchestrator.MachineID, bandwidth uint64) error {
	n, err := v.getNetwork(target)
	if err != nil {
		return err
	}
	return v.neb.SetBandwidth(source, n, bandwidth)
}

func (v *Virt) setlatency(source orchestrator.MachineID, target orchestrator.MachineID, latency uint32) error {
	n, err := v.getNetwork(target)
	if err != nil {
		return err
	}
	return v.neb.SetLatency(source, n, latency)
}

func (v *Virt) unblocklink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	n, err := v.getNetwork(target)
	if err != nil {
		return err
	}
	return v.neb.UnblockLink(source, n)
}
func (v *Virt) blocklink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	n, err := v.getNetwork(target)
	if err != nil {
		return err
	}
	return v.neb.BlockLink(source, n)
}
