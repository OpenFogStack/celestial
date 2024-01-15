package virt

import (
	"os/exec"

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

func (v *Virt) RegisterMachine(id orchestrator.MachineID, name string, host orchestrator.Host, config orchestrator.MachineConfig) error {
	// if the machine is on a remote host, we need to route there
	ownHost, err := v.pb.GetHostID()

	if err != nil {
		return err
	}

	if uint8(host) != ownHost {
		return v.route(id, host)
	}

	m, err := v.register(id, name, config)

	if err != nil {
		return err
	}

	v.machines[id] = m

	return nil
}

func (v *Virt) BlockLink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[source]; !ok {
		return nil
	}

	return v.blocklink(source, target)
}

func (v *Virt) UnblockLink(source orchestrator.MachineID, target orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[source]; !ok {
		return nil
	}

	return v.unblocklink(source, target)
}

func (v *Virt) SetLatency(source orchestrator.MachineID, target orchestrator.MachineID, latency uint32) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[source]; !ok {
		return nil
	}

	return v.setlatency(source, target, latency)
}

func (v *Virt) SetBandwidth(source orchestrator.MachineID, target orchestrator.MachineID, bandwidth uint64) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[source]; !ok {
		return nil
	}

	return v.setbandwidth(source, target, bandwidth)
}

func (v *Virt) StopMachine(machine orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[machine]; !ok {
		return nil
	}

	return v.transition(machine, STOPPED)
}

func (v *Virt) StartMachine(machine orchestrator.MachineID) error {
	// check that the source machine is on this host, otherwise discard
	if _, ok := v.machines[machine]; !ok {
		return nil
	}

	return v.transition(machine, STARTED)
}

func (v *Virt) Stop() error {
	log.Debugf("stopping %d machines", len(v.machines))
	for m := range v.machines {
		err := v.transition(m, KILLED)

		if err != nil {
			return err
		}
	}

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
