package virt

import "github.com/OpenFogStack/celestial/pkg/orchestrator"

func (v *Virt) route(id orchestrator.MachineID, host orchestrator.Host) error {
	return v.pb.Route(v.machines[id].network.ip, host)
}
