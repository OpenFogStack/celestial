package virt

import (
	"context"
	"fmt"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	orchestrator "github.com/OpenFogStack/celestial/pkg/orchestrator2"
)

func (v *Virt) transition(id orchestrator.MachineID, state state) error {
	if v.machines[id].state == state {
		return nil
	}

	switch state {
	case STOPPED:
		switch v.machines[id].state {
		case STARTED:
			err := v.suspendMachine(v.machines[id])
			if err != nil {
				return err
			}
			v.machines[id].state = STOPPED
			return nil
		case REGISTERED:
			// not started yet, so nothing to do
			// but keep it as registered only, so that it can be started if it ever transitions to STARTED
			return nil
		}
	case STARTED:
		switch v.machines[id].state {
		case REGISTERED:
			err := v.startMachine(v.machines[id])
			if err != nil {
				return err
			}
			v.machines[id].state = STARTED
			return nil

		case STOPPED:
			err := v.resumeMachine(v.machines[id])
			if err != nil {
				return err
			}
			v.machines[id].state = STARTED
			return nil
		}
	case REGISTERED:
		return errors.Errorf("cannot transition to REGISTERED")
	case KILLED:
		switch v.machines[id].state {
		case STARTED:
			err := v.killMachine(v.machines[id])
			if err != nil {
				return err
			}
			return nil
		case STOPPED:
			err := v.killMachine(v.machines[id])
			if err != nil {
				return err
			}
			return nil
		}
	}
	return nil
}

func (v *Virt) register(id orchestrator.MachineID, name string, config orchestrator.MachineConfig) (*machine, error) {

	if name != "" {
		name = fmt.Sprintf("gst-%s", name)
	}

	if name == "" {
		name = fmt.Sprintf("%d-%d", id.Group, id.Id)
	}

	m := &machine{
		name:       name,
		state:      REGISTERED,
		vcpucount:  config.VCPUCount,
		ram:        config.RAM,
		disksize:   config.DiskSize,
		diskimage:  config.DiskImage,
		kernel:     config.Kernel,
		bootparams: config.BootParams,
	}

	// create the network
	n, err := getNet(id)

	if err != nil {
		return nil, err
	}

	m.network = n

	err = m.createNetwork()

	if err != nil {
		return nil, err
	}

	err = v.neb.Register(id, m.network.tap)

	if err != nil {
		return nil, err
	}

	return m, nil
}

func (v *Virt) killMachine(m *machine) error {
	log.Debug("Killing machine ", m.name)
	return m.vm.StopVMM()
}

func (v *Virt) suspendMachine(m *machine) error {
	log.Debug("Suspending machine ", m.name)
	return m.vm.PauseVM(context.Background())
}

func (v *Virt) resumeMachine(m *machine) error {
	log.Debug("Resuming machine ", m.name)
	return m.vm.ResumeVM(context.Background())
}

func (v *Virt) startMachine(m *machine) error {
	log.Debug("Starting machine ", m.name)
	// perform init tasks
	err := m.initialize()

	if err != nil {
		return err
	}

	return m.vm.Start(context.Background())
}
