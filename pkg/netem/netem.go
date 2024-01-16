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
	blocked   bool
	latency   uint32
	bandwidth uint64

	// tc specific
	tcIndex uint16
}

type vm struct {
	netIf string

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

func New() *Netem {

	err := checkCommands()

	if err != nil {
		panic(err)
	}

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

	v := &vm{
		netIf: netIf,
		links: make(map[ipnet]*link),
	}

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

func (n *Netem) SetBandwidth(source orchestrator.MachineID, target net.IPNet, bandwidth uint64) error {

	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.updateBandwidth(target, bandwidth)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].bandwidth = bandwidth

	return nil
}

func (n *Netem) SetLatency(source orchestrator.MachineID, target net.IPNet, latency uint32) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

	err := n.checkLink(source, target)

	if err != nil {
		return err
	}

	err = v.updateDelay(target, latency)

	if err != nil {
		return err
	}

	n.vms[source].links[fromIPNet(target)].latency = latency

	return nil
}

func (n *Netem) UnblockLink(source orchestrator.MachineID, target net.IPNet) error {
	v, ok := n.vms[source]

	if !ok {
		return errors.Errorf("machine %d-%d does not exist", source.Group, source.Id)
	}

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
