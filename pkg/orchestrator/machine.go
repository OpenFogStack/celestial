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
	"context"
	"io"
	"math/rand"
	"net"
	"sync"
	"sync/atomic"
	"time"

	"github.com/pkg/errors"

	"github.com/firecracker-microvm/firecracker-go-sdk"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/commons"
)

type remoteMachine struct {
	host *host
}

type localmachine struct {
	active bool

	links map[string]*link

	name string

	// and some firecracker reference
	m               *firecracker.Machine
	drivePath       string
	kernelImagePath string
	htEnabled       bool
	memSizeMiB      uint64
	vCPUCount       uint64
	bandwidth       uint64
	bootparams      string
	outFile         io.Writer
	errFile         io.Writer
	initialized     bool

	// and some networking stuff
	tapName        string
	chainName      string
	ipBlockSet     string
	ip             string
	gateway        string
	mac            string
	hostInterface  string
	nextHandle     int64
	netInitialized bool

	sync.RWMutex
}

type machine struct {
	isLocal bool

	*remoteMachine
	*localmachine

	id        id
	address   net.IP
	network   *net.IPNet
	bandwidth uint64
	name      string
}

// GetGSTID returns the ID of a ground station machine.
func (o *Orchestrator) GetGSTID(name string) (uint64, error) {

	m, err := o.getGSTMachineByName(name)

	if err != nil {
		return 0, errors.WithStack(err)
	}

	return uint64(m.id), nil
}

func (o *Orchestrator) getMachine(m commons.MachineID) (*machine, error) {
	s, ok := o.shells[shellid(m.Shell)]

	if !ok {
		return nil, errors.Errorf("unknown shell: %d", m.Shell)
	}

	s.RLock()
	machine, ok := s.machines[id(m.ID)]
	s.RUnlock()

	if !ok {
		return nil, errors.Errorf("unknown machine: %d in shell %d", m.ID, m.Shell)
	}

	return machine, nil
}

func (o *Orchestrator) getGSTMachineByName(name string) (*machine, error) {
	o.gstLock.RLock()
	machine, ok := o.groundstations[name]
	o.gstLock.RUnlock()

	if !ok {
		return nil, errors.Errorf("unknown groundstation: %s", name)
	}

	return machine, nil
}

// setInactive pauses a firecracker microVM.
func (o *Orchestrator) setInactive(m *localmachine) error {

	m.active = false

	if !m.initialized {
		return nil
	}

	c, cancel := context.WithCancel(context.Background())
	defer cancel()

	err := m.m.PauseVM(c)

	return errors.WithStack(err)
}

// setActive resumes a firecracker microVM.
func (o *Orchestrator) setActive(m *localmachine) error {

	m.active = true

	if !m.initialized {
		err := m.initialize()

		return errors.WithStack(err)
	}

	c, cancel := context.WithCancel(context.Background())
	defer cancel()

	err := m.m.ResumeVM(c)

	return errors.WithStack(err)
}

// CreateMachine creates a new firecracker microVM.
func (o *Orchestrator) CreateMachine(m commons.MachineID, vCPUCount uint64, memSizeMiB uint64, htEnabled bool, bootparams string, kernel string, rootfs string, bandwidth uint64, active bool) error {

	atomic.AddInt64(&o.outstanding, 1)
	defer atomic.AddInt64(&o.outstanding, -1)

	// check if that shell even exists
	s, ok := o.shells[shellid(m.Shell)]

	if !ok {
		return errors.Errorf("unknown shell: %d", m.Shell)
	}

	// check if the machine exists already
	s.RLock()
	if _, ok := s.machines[id(m.ID)]; ok {
		s.RUnlock()
		return errors.Errorf("machine exists already: %d in in shell %d", m.ID, m.Shell)
	}
	s.RUnlock()

	machine := &machine{
		isLocal: true,
		localmachine: &localmachine{
			active:         active,
			links:          make(map[string]*link),
			m:              nil,
			initialized:    false,
			netInitialized: false,
			tapName:        "",
			nextHandle:     0,
			RWMutex:        sync.RWMutex{},
		},
		bandwidth: bandwidth,
		name:      m.Name,
	}

	machine.Lock()
	defer machine.Unlock()

	// create the machine
	err := machine.create(m.ID, m.Shell, m.Name, vCPUCount, memSizeMiB, htEnabled, bandwidth, kernel, rootfs, bootparams, o.networkInterface)

	if err != nil {
		return errors.WithStack(err)
	}

	if m.Shell == -1 {
		o.gstLock.Lock()
		o.groundstations[m.Name] = machine
		o.gstLock.Unlock()
	}

	s.Lock()
	s.machines[id(m.ID)] = machine
	s.Unlock()

	err = o.registerLocal(m.ID, m.Shell, m.Name)

	if err != nil {
		return errors.WithStack(err)
	}

	if active || o.eager {

		// proposal: don't overload the machine at the beginning
		time.Sleep(time.Duration(rand.Intn(o.initDelay)) * time.Second)

		log.Debugf("initializing machine: %d %d %s %v", m.ID, m.Shell, m.Name, active)

		err := machine.localmachine.initialize()

		if err != nil {
			log.Errorf("%+v\n", err)
			// return errors.WithStack(err)
		}

		if !active {
			return o.setInactive(machine.localmachine)
		}
	}

	atomic.AddUint64(&o.created, 1)
	log.Debugf("%d machines created, %d machines outstanding", o.created, o.outstanding)

	return nil
}

// ModifyMachine pauses or resumes a firecracker microVM.
func (o *Orchestrator) ModifyMachine(m commons.MachineID, active bool) error {

	log.Debugf("modifying machine: %d %d %s %v", m.ID, m.Shell, m.Name, active)

	machine, err := o.getMachine(m)

	if err != nil {
		return errors.WithStack(err)
	}

	if !machine.isLocal {
		return errors.Errorf("cannot modify machine %v, is not local", m)
	}

	machine.localmachine.Lock()
	defer machine.localmachine.Unlock()

	if machine.localmachine.active && !active {
		log.Infof("Setting machine %d in shell %d to: inactive", m.ID, m.Shell)
		return o.setInactive(machine.localmachine)
	}

	if !machine.localmachine.active && active {
		log.Infof("Setting machine %d in shell %d to: active", m.ID, m.Shell)
		return o.setActive(machine.localmachine)
	}

	return nil
}
