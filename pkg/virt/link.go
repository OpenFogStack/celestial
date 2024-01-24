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

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
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
