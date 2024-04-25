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

package netem

import (
	"net"
	"os/exec"
	"sync"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type link struct {
	blocked       bool
	latencyUs     uint32
	bandwidthKbps uint64

	// tc specific
	tcIndex uint16
}

type vm struct {
	netIf string

	// no concurrent modifications allowed
	sync.Mutex

	// ipset specific configuration
	chainName  string
	ipBlockSet string

	// tc specific configuration
	handle uint16

	links map[ipnet]*link
}

var (
	IPTABLES_BIN string
	IPSET_BIN    string
	TC_BIN       string
)

func checkCommands() (err error) {
	IPTABLES_BIN, err = exec.LookPath("iptables")

	if err != nil {
		return err
	}

	IPSET_BIN, err = exec.LookPath("ipset")

	if err != nil {
		return err
	}

	TC_BIN, err = exec.LookPath("tc")

	if err != nil {
		return err
	}

	return nil
}

type Netem struct {
	vms map[orchestrator.MachineID]*vm
}

func init() {
	err := checkCommands()

	if err != nil {
		panic(err)
	}
}

func New() *Netem {
	return &Netem{
		vms: make(map[orchestrator.MachineID]*vm),
	}
}

func (n *Netem) Stop() error {
	// remove all machine stuff
	log.Debugf("Removing all netem stuff")

	wg := sync.WaitGroup{}
	var e error

	for _, v := range n.vms {
		wg.Add(1)
		go func(v *vm) {
			defer wg.Done()
			// remove ipset
			err := v.removeIPSet()

			if err != nil {
				e = errors.WithStack(err)
			}

			// remove tc
			err = v.removeTC()

			if err != nil {
				e = errors.WithStack(err)
			}
		}(v)
	}

	wg.Wait()
	if e != nil {
		return e
	}

	return nil
}

func (n *Netem) Register(id orchestrator.MachineID, netIf string) error {
	// executed when a new machine is registered
	// necessary to add to our list and prepare everything that needs to run once

	// check that machine does not already exist
	if _, ok := n.vms[id]; ok {
		return errors.Errorf("machine %d-%d already exists", id.Group, id.Id)
	}

	log.Tracef("registering machine %d-%d", id.Group, id.Id)

	v := &vm{
		netIf: netIf,
		links: make(map[ipnet]*link),
	}

	v.Lock()
	defer v.Unlock()

	// create ipset for this machine
	err := v.configureIPSet(id)

	if err != nil {
		return err
	}

	// create things for tc
	err = v.configureTC()

	if err != nil {
		return err
	}

	n.vms[id] = v

	return nil
}

func (n *Netem) checkLink(source orchestrator.MachineID, target net.IPNet) error {
	// check that a link exists between source and target
	// if not, create it
	if _, ok := n.vms[source].links[fromIPNet(target)]; ok {
		// exists, all fine!
		return nil
	}

	index, err := n.vms[source].createQDisc(target)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)] = &link{tcIndex: index}

	return nil
}

func (n *Netem) SetBandwidth(source orchestrator.MachineID, target net.IPNet, bandwidthKbps uint64) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	v.Lock()
	defer v.Unlock()

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.updateBandwidth(target, bandwidthKbps)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].bandwidthKbps = bandwidthKbps

	return nil
}

func (n *Netem) SetLatency(source orchestrator.MachineID, target net.IPNet, latencyUs uint32) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	v.Lock()
	defer v.Unlock()

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.updateDelay(target, latencyUs)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].latencyUs = latencyUs

	return nil
}

func (n *Netem) UnblockLink(source orchestrator.MachineID, target net.IPNet) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	v.Lock()
	defer v.Unlock()

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.unblockNet(target)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].blocked = false

	return nil
}

func (n *Netem) BlockLink(source orchestrator.MachineID, target net.IPNet) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	v.Lock()
	defer v.Unlock()

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.blockNet(target)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].blocked = true

	return nil
}
