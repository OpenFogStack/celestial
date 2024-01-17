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

	host Host

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
	progress := 0
	for m := range o.machines {
		o.State.MachinesState[m] = STOPPED

		err := o.virt.RegisterMachine(m, o.machines[m].name, o.machines[m].Host, o.machines[m].config)
		if err != nil {
			return errors.WithStack(err)
		}

		progress++

		if progress%10 == 0 {
			log.Debugf("machine init progress: %d/%d", progress, len(o.machines))
		}
	}
	log.Debugf("machine init progress: %d/%d", progress, len(o.machines))

	log.Debugf("starting link init")

	// init networking
	// by default, all links are blocked
	var wg sync.WaitGroup
	var e error
	progress2 := atomic.Uint32{}

	start := time.Now()

	for m := range o.machines {
		o.State.NetworkState[m] = make(map[MachineID]*Link)

		wg.Add(1)
		go func(source MachineID) {
			defer wg.Done()
			//log.Debugf("blocking all links from %s", source)

			for otherMachine := range o.machines {
				// exclude self
				if source == otherMachine {
					continue
				}

				//log.Debugf("blocking link %s -> %s", source, otherMachine)
				err := o.virt.BlockLink(source, otherMachine)
				if err != nil {
					e = errors.WithStack(err)
				}

				o.State.NetworkState[source][otherMachine] = &Link{
					// likely better to have all links blocked at the beginning
					Blocked: true,
				}

				// progress
				progress2.Add(1)
			}
			//log.Debugf("done blocking all links from %s", source)

		}(m)
	}

	shown := 0
	total := len(o.machines) * (len(o.machines) - 1)
	for state := 0; state < total; state = int(progress2.Load()) {
		if state > shown && state%100 == 0 {
			log.Debugf("link init progress: %d/%d", progress2.Load(), total)
			shown = state
		}
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}

	log.Debugf("done blocking all links in %s", time.Since(start))

	o.initialized = true

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

	var wg sync.WaitGroup
	var e error

	for m, ls := range s.NetworkState {
		wg.Add(1)
		go func(source MachineID, links map[MachineID]*Link) {
			defer wg.Done()
			for target, l := range links {
				if l.Blocked && !o.State.NetworkState[source][target].Blocked {
					log.Debugf("blocking link %s -> %s", source, target)
					err := o.virt.BlockLink(source, target)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Blocked = true
				}

				if !l.Blocked && o.State.NetworkState[source][target].Blocked {
					log.Debugf("unblocking link %s -> %s", source, target)
					err := o.virt.UnblockLink(source, target)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Blocked = false
				}

				if l.Blocked {
					continue
				}

				log.Debugf("updating link %s -> %s", source, target)
				if l.Next != o.State.NetworkState[source][target].Next {
					log.Debugf("setting next hop %s -> %s to %s ", source, target, l.Next)
					o.State.NetworkState[source][target].Next = l.Next
				}

				if l.Latency != o.State.NetworkState[source][target].Latency {
					log.Debugf("changing latency %s -> %s from %d to %d", source, target, l.Latency, o.State.NetworkState[source][target].Latency)
					err := o.virt.SetLatency(source, target, l.Latency)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Latency = l.Latency
				}

				if l.Bandwidth != o.State.NetworkState[source][target].Bandwidth {
					log.Debugf("setting bandwidth %s -> %s to %d", source, target, l.Bandwidth)
					err := o.virt.SetBandwidth(source, target, l.Bandwidth)
					if err != nil {
						e = errors.WithStack(err)
					}
					o.State.NetworkState[source][target].Bandwidth = l.Bandwidth
				}
			}
		}(m, ls)
	}

	wg.Wait()
	if e != nil {
		return errors.WithStack(e)
	}

	// 2. update all the machines
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

	return nil
}
