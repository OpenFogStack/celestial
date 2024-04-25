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

package orchestrator

import (
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	"github.com/pbnjay/memory"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

type Orchestrator struct {
	// State is the description of the desired state of the emulation (as determined by simulation)
	State

	machines     map[MachineID]*machine
	machineNames map[string]MachineID

	virt VirtualizationBackend

	initialized bool
}

func New(vb VirtualizationBackend) *Orchestrator {
	return &Orchestrator{
		virt: vb,
	}
}

func (o *Orchestrator) GetResources() (availcpus uint32, availram uint64, err error) {
	return uint32(runtime.NumCPU()), memory.TotalMemory(), nil
}

func (o *Orchestrator) Initialize(machineList map[MachineID]MachineConfig, machineHosts map[MachineID]Host, machineNames map[MachineID]string) error {
	if o.initialized {
		return errors.Errorf("orchestrator already initialized")
	}

	log.Debugf("initializing orchestrator with %d machines", len(machineList))

	o.machines = make(map[MachineID]*machine)
	o.machineNames = make(map[string]MachineID)

	for m, config := range machineList {
		o.machines[m] = &machine{
			name:   machineNames[m],
			config: config,
		}

		if machineNames[m] != "" {
			o.machineNames[machineNames[m]] = m
		}
	}

	for m, host := range machineHosts {
		o.machines[m].Host = host
	}

	for m, name := range machineNames {
		o.machines[m].name = name
	}

	// init state
	o.State = State{
		NetworkState:  make(NetworkState),
		MachinesState: make(MachinesState),
	}

	// register all machines
	var wg sync.WaitGroup
	var e error
	progressMachines := atomic.Uint32{}

	for m := range o.machines {
		wg.Add(1)
		go func(mid MachineID, mmachine *machine) {
			defer wg.Done()
			err := o.virt.RegisterMachine(mid, mmachine.name, mmachine.Host, mmachine.config)

			if err != nil {
				e = errors.WithStack(err)
			}

			progressMachines.Add(1)
		}(m, o.machines[m])

		o.State.MachinesState[m] = STOPPED
	}

	shown := 0
	total := len(o.machines)
	for state := 0; state < total; state = int(progressMachines.Load()) {
		if state > shown && state%100 == 0 {
			log.Debugf("machine init progress: %d/%d", progressMachines.Load(), total)
			shown = state
		}
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}

	log.Debugf("starting link init")

	// init networking
	// by default, all links are blocked
	wg = sync.WaitGroup{}
	e = nil
	progressLinks := atomic.Uint32{}

	start := time.Now()

	for m := range o.machines {
		o.State.NetworkState[m] = make(map[MachineID]*Link)

		wg.Add(1)
		go func(source MachineID, links map[MachineID]*Link) {
			defer wg.Done()
			//log.Tracef("blocking all links from %s", source)

			for otherMachine := range o.machines {
				// exclude self
				if source == otherMachine {
					continue
				}

				//log.Tracef("blocking link %s -> %s", source, otherMachine)
				err := o.virt.BlockLink(source, otherMachine)
				if err != nil {
					e = errors.WithStack(err)
				}

				links[otherMachine] = &Link{
					// likely better to have all links blocked at the beginning
					Blocked: true,
				}

				// progress
				progressLinks.Add(1)
			}
			//log.Tracef("done blocking all links from %s", source)

		}(m, o.State.NetworkState[m])
	}

	shown = 0
	total = len(o.machines) * (len(o.machines) - 1)
	for state := 0; state < total; state = int(progressLinks.Load()) {
		if state > shown && state%100 == 0 {
			log.Debugf("link init progress: %d/%d", progressLinks.Load(), total)
			shown = state
		}
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}

	log.Debugf("done blocking all links in %s", time.Since(start))

	o.initialized = true

	log.Info("orchestrator initialized")

	return nil
}

func (o *Orchestrator) Stop() error {
	log.Debugf("stopping orchestrator")
	err := o.virt.Stop()
	if err != nil {
		log.Error(err.Error())
		return errors.WithStack(err)
	}

	return nil
}

func (o *Orchestrator) Update(s *State) error {
	// run the update procedure and apply changes

	// 1. update all the links
	linkUpdateStart := time.Now()
	var wg sync.WaitGroup
	var e error

	for m, ls := range s.NetworkState {
		wg.Add(1)
		go func(source MachineID, links map[MachineID]*Link) {
			defer wg.Done()
			for target, l := range links {
				if l.Blocked && !o.State.NetworkState[source][target].Blocked {
					log.Tracef("blocking link %s -> %s", source, target)
					err := o.virt.BlockLink(source, target)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Blocked = true
				}

				if !l.Blocked && o.State.NetworkState[source][target].Blocked {
					log.Tracef("unblocking link %s -> %s", source, target)
					err := o.virt.UnblockLink(source, target)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Blocked = false
				}

				if l.Blocked {
					continue
				}

				log.Tracef("updating link %s -> %s", source, target)
				if l.Next != o.State.NetworkState[source][target].Next {
					log.Tracef("setting next hop %s -> %s to %s ", source, target, l.Next)
					o.State.NetworkState[source][target].Next = l.Next
				}

				if l.LatencyUs != o.State.NetworkState[source][target].LatencyUs {
					log.Tracef("changing latency %s -> %s from %d to %d", source, target, l.LatencyUs, o.State.NetworkState[source][target].LatencyUs)
					err := o.virt.SetLatency(source, target, l.LatencyUs)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].LatencyUs = l.LatencyUs
				}

				if l.BandwidthKbps != o.State.NetworkState[source][target].BandwidthKbps {
					log.Tracef("setting bandwidth %s -> %s to %d", source, target, l.BandwidthKbps)
					err := o.virt.SetBandwidth(source, target, l.BandwidthKbps)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].BandwidthKbps = l.BandwidthKbps
				}
			}
		}(m, ls)
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}

	log.Debugf("link update took %s", time.Since(linkUpdateStart))

	// 2. update all the machines
	machineUpdateStart := time.Now()
	wg = sync.WaitGroup{}
	e = nil

	for m, state := range s.MachinesState {
		if state == STOPPED && o.State.MachinesState[m] == ACTIVE {
			wg.Add(1)
			go func(machine MachineID) {
				defer wg.Done()
				// stop machine
				err := o.virt.StopMachine(machine)
				if err != nil {
					e = errors.WithStack(err)
				}
			}(m)
			o.State.MachinesState[m] = STOPPED
			continue
		}

		if state == ACTIVE && o.State.MachinesState[m] == STOPPED {
			wg.Add(1)
			go func(machine MachineID) {
				defer wg.Done()
				// start machine
				err := o.virt.StartMachine(machine)
				if err != nil {
					e = errors.WithStack(err)
				}
			}(m)
			o.State.MachinesState[m] = ACTIVE
			continue
		}
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}
	log.Debugf("machine update took %s", time.Since(machineUpdateStart))

	log.Info("orchestrator updated")

	return nil
}
