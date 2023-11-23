package orchestrator2

import (
	"runtime"

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
	for m := range o.machines {
		o.State.MachinesState[m] = STOPPED

		err := o.virt.RegisterMachine(m, o.machines[m].name, o.machines[m].Host, o.machines[m].config)
		if err != nil {
			return errors.WithStack(err)
		}
	}

	// init networking
	// by default, all links are blocked
	for m := range o.machines {
		o.State.NetworkState[m] = make(map[MachineID]*Link)

		for otherMachine := range o.machines {
			// exclude self
			if m == otherMachine {
				continue
			}

			log.Debug("blocking link ", m, " -> ", otherMachine)

			err := o.virt.BlockLink(m, otherMachine)
			if err != nil {
				return errors.WithStack(err)
			}
			o.State.NetworkState[m][otherMachine] = &Link{
				// likely better to have all links blocked at the beginning
				Blocked:   true,
				Latency:   defaultLatency,
				Bandwidth: defaultBandwidth,
			}
		}
	}

	o.initialized = true

	return nil
}

func (o *Orchestrator) Stop() error {
	err := o.virt.Stop()
	if err != nil {
		return errors.WithStack(err)
	}

	return nil
}

func (o *Orchestrator) Update(s *State) error {
	// run the update procedure and apply changes

	// 1. update all the links
	for m, ls := range s.NetworkState {
		for target, l := range ls {
			if l.Blocked && !o.State.NetworkState[m][target].Blocked {
				log.Debug("blocking link ", m, " -> ", target)
				err := o.virt.BlockLink(m, target)
				if err != nil {
					return errors.WithStack(err)
				}
				o.State.NetworkState[m][target].Blocked = true
				continue
			}

			if !l.Blocked && o.State.NetworkState[m][target].Blocked {
				log.Debug("unblocking link ", m, " -> ", target)
				err := o.virt.UnblockLink(m, target)
				if err != nil {
					return errors.WithStack(err)
				}
				o.State.NetworkState[m][target].Blocked = false
			}

			if l.Latency != o.State.NetworkState[m][target].Latency {
				log.Debug("setting latency ", m, " -> ", target, " to ", l.Latency)
				err := o.virt.SetLatency(m, target, l.Latency)
				if err != nil {
					return errors.WithStack(err)
				}
				o.State.NetworkState[m][target].Latency = l.Latency
			}

			if l.Bandwidth != o.State.NetworkState[m][target].Bandwidth {
				log.Debug("setting bandwidth ", m, " -> ", target, " to ", l.Bandwidth)
				err := o.virt.SetBandwidth(m, target, l.Bandwidth)
				if err != nil {
					return errors.WithStack(err)
				}
				o.State.NetworkState[m][target].Bandwidth = l.Bandwidth
			}
		}
	}

	// 2. update all the machines
	for m, state := range s.MachinesState {
		if state == STOPPED && o.State.MachinesState[m] == ACTIVE {
			// stop machine
			err := o.virt.StopMachine(m)
			if err != nil {
				return errors.WithStack(err)
			}
			o.State.MachinesState[m] = STOPPED
			continue
		}

		if state == ACTIVE && o.State.MachinesState[m] == STOPPED {
			// start machine
			err := o.virt.StartMachine(m)
			if err != nil {
				return errors.WithStack(err)
			}
			o.State.MachinesState[m] = ACTIVE
			continue
		}
	}

	return nil
}
