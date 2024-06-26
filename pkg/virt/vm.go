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
	"context"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

func (v *Virt) transition(id orchestrator.MachineID, state state) error {
	v.RLock()
	m := v.machines[id]
	v.RUnlock()

	if m.state == state {
		return nil
	}

	switch state {
	case STOPPED:
		switch m.state {
		case STARTED:
			err := suspendMachine(m)
			if err != nil {
				return err
			}
			m.state = STOPPED
			return nil
		case REGISTERED:
			// not started yet, so nothing to do
			// but keep it as registered only, so that it can be started if it ever transitions to STARTED
			return nil
		default:
			log.Tracef("cannot transition %s from %d to %d", id, m.state, state)
		}
	case STARTED:
		switch m.state {
		case REGISTERED:
			err := startMachine(m)
			if err != nil {
				return err
			}
			m.state = STARTED
			return nil

		case STOPPED:
			err := resumeMachine(m)
			if err != nil {
				return err
			}
			m.state = STARTED
			return nil
		default:
			log.Tracef("cannot transition %s from %d to %d", id, m.state, state)
		}
	case REGISTERED:
		return errors.Errorf("cannot transition to REGISTERED")
	case KILLED:
		switch m.state {
		case STARTED:
			err := killMachine(m)
			if err != nil {
				return err
			}
			return nil
		case STOPPED:
			err := killMachine(m)
			if err != nil {
				return err
			}
			return nil
		default:
			log.Tracef("cannot transition %s from %d to %d", id, m.state, state)
		}
	}
	return nil
}

func (v *Virt) register(id orchestrator.MachineID, m *machine, config orchestrator.MachineConfig) error {

	m.state = REGISTERED
	m.vcpucount = config.VCPUCount
	m.ram = config.RAM
	m.disksize = config.DiskSize
	m.diskimage = config.DiskImage
	m.kernel = config.Kernel
	m.bootparams = config.BootParams

	// create the network

	err := m.createNetwork()

	if err != nil {
		return err
	}

	err = v.neb.Register(id, m.network.tap)

	if err != nil {
		return err
	}

	return nil
}

func killMachine(m *machine) error {
	log.Trace("Killing machine ", m.name)

	err := m.vm.StopVMM()

	if err != nil {
		return err
	}

	log.Trace("Killed machine ", m.name)

	return nil
}

func suspendMachine(m *machine) error {
	log.Trace("Suspending machine ", m.name)
	return m.vm.PauseVM(context.Background())
}

func resumeMachine(m *machine) error {
	log.Trace("Resuming machine ", m.name)
	return m.vm.ResumeVM(context.Background())
}

func startMachine(m *machine) error {
	log.Trace("Starting machine ", m.name)
	// perform init tasks
	err := m.initialize()

	if err != nil {
		return err
	}

	return m.vm.Start(context.Background())
}
