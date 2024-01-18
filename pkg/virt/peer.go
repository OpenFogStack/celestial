package virt

import "github.com/OpenFogStack/celestial/pkg/orchestrator"

func (v *Virt) route(m *machine, host orchestrator.Host) error {
	return v.pb.Route(m.network.network, host)
}
