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
	"fmt"
	"os/exec"
	"sync"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

func checkCommands() (err error) {
	IPTABLES_BIN, err = exec.LookPath("iptables")

	if err != nil {
		return err
	}

	IP_BIN, err = exec.LookPath("ip")

	if err != nil {
		return err
	}

	SYSCTL_BIN, err = exec.LookPath("sysctl")

	if err != nil {
		return err
	}

	DD_BIN, err = exec.LookPath("dd")

	if err != nil {
		return err
	}

	MKFS_BIN, err = exec.LookPath("mkfs.ext4")

	if err != nil {
		return err
	}

	return nil
}

// New creates a new virt backend.
func New(hostInterface string, initDelay uint64, pb PeeringBackend, neb NetworkEmulationBackend) (*Virt, error) {

	err := checkCommands()

	if err != nil {
		return nil, err
	}

	v := &Virt{
		hostInterface: hostInterface,
		initDelay:     initDelay,
		pb:            pb,
		neb:           neb,
		machines:      make(map[orchestrator.MachineID]*machine),
	}

	err = v.initHost()

	if err != nil {
		return nil, err
	}

	return v, nil
}

// RegisterMachine registers a machine with the virt backend. If the machine is on a remote host, it will be routed there.
func (v *Virt) RegisterMachine(id orchestrator.MachineID, name string, host orchestrator.Host, config orchestrator.MachineConfig) error {

	if name != "" {
		name = fmt.Sprintf("gst-%s", name)
	}

	if name == "" {
		name = fmt.Sprintf("%d-%d", id.Group, id.Id)
	}

	n, err := getNet(id)

	if err != nil {
		return err
	}

	m := &machine{
		name:    name,
		network: n,
	}

	// if the machine is on a remote host, we need to route there
	ownHost, err := v.pb.GetHostID()

	if err != nil {
		return err
	}

	if uint8(host) != ownHost {
		return v.route(m, host)
	}

	err = v.register(id, m, config)

	if err != nil {
		return err
	}

	v.Lock()
	v.machines[id] = m
	v.Unlock()

	return nil
}

// BlockLink blocks the link between two machines using the network emulation backend.
func (v *Virt) BlockLink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[source]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.blocklink(source, target)
}

// UnblockLink unblocks the link between two machines using the network emulation backend.
func (v *Virt) UnblockLink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[source]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.unblocklink(source, target)
}

// SetLatency sets the latency between two machines using the network emulation backend.
func (v *Virt) SetLatency(source orchestrator.MachineID, target orchestrator.MachineID, latency uint32) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[source]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.setlatency(source, target, latency)
}

// SetBandwidth sets the bandwidth between two machines using the network emulation backend.
func (v *Virt) SetBandwidth(source orchestrator.MachineID, target orchestrator.MachineID, bandwidth uint64) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[source]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.setbandwidth(source, target, bandwidth)
}

func (v *Virt) StopMachine(machine orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[machine]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.transition(machine, STOPPED)
}

func (v *Virt) StartMachine(machine orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	v.RLock()
	_, ok := v.machines[machine]
	defer v.RUnlock()
	if !ok {
		return nil
	}

	return v.transition(machine, STARTED)
}

func (v *Virt) Stop() error {
	log.Debugf("stopping %d machines", len(v.machines))
	var wg sync.WaitGroup
	for m := range v.machines {
		wg.Add(1)
		go func(id orchestrator.MachineID) {
			defer wg.Done()
			err := v.transition(id, KILLED)

			if err != nil {
				log.Error(err)
			}
		}(m)
	}
	wg.Wait()
	v.Lock()
	defer v.Unlock()

	log.Debug("stopping netem backend")
	err := v.neb.Stop()

	if err != nil {
		return err
	}

	log.Debug("stopping peering backend")
	err = v.pb.Stop()

	if err != nil {
		return err
	}

	log.Debug("removing network devices")

	for _, m := range v.machines {
		err := m.removeNetwork()

		if err != nil {
			return err
		}
	}

	return nil
}
