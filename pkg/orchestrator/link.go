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

package orchestrator

import (
	"github.com/pkg/errors"

	"github.com/OpenFogStack/celestial/pkg/commons"
)

// LockForLink locks a machine for link modification.
func (o *Orchestrator) LockForLink(a commons.MachineID) error {
	machineA, err := o.getMachine(a)

	if err != nil {
		return errors.WithStack(err)
	}

	machineA.Lock()

	return nil
}

// UnlockForLink unlocks a machine for link modification.
func (o *Orchestrator) UnlockForLink(a commons.MachineID) error {
	machineA, err := o.getMachine(a)

	if err != nil {
		return errors.WithStack(err)
	}

	machineA.Unlock()

	return nil
}

// RemoveLink removes a link from two firecracker microVMs. It assumes that LockForLink is called before.
func (o *Orchestrator) RemoveLink(a commons.MachineID, b commons.MachineID) error {
	machineA, err := o.getMachine(a)

	if err != nil {
		return errors.WithStack(err)
	}

	machineB, err := o.getMachine(b)

	if err != nil {
		return errors.WithStack(err)
	}

	if err := o.removeLink(machineA, machineB); err != nil {
		return errors.WithStack(err)
	}

	return nil
}

// ModifyLink modifies the latency (in ms) of the links between two firecracker microVMs. It assumes that LockForLink is called before.
func (o *Orchestrator) ModifyLink(a commons.MachineID, b commons.MachineID, latency float64, bandwidth uint64) error {
	machineA, err := o.getMachine(a)

	if err != nil {
		return errors.WithStack(err)
	}

	machineB, err := o.getMachine(b)

	if err != nil {
		return errors.WithStack(err)
	}

	if !machineB.isLocal {
		latency -= machineB.remoteMachine.host.latency
	}

	if err := o.modifyLink(machineA, machineB, latency, bandwidth); err != nil {
		return errors.WithStack(err)
	}

	return nil
}
