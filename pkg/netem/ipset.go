package netem

import (
	"fmt"
	"net"
	"os/exec"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

func (v *vm) configureIPSet(id orchestrator.MachineID) error {
	// come up with a chain name and ip blockset name
	v.chainName = fmt.Sprintf("CT-%d-%d", id.Group, id.Id)

	v.ipBlockSet = fmt.Sprintf("CT-%d-%d-bl", id.Group, id.Id)

	// remove old stuff, but ignore any errors
	// adding the -w flag to iptables makes it wait for the lock
	// there have been some reported issues with this, but it seems to work fine for us
	// iptables -w -D FORWARD -i [TAP_NAME] -j [CHAIN_NAME]
	cmd := exec.Command(IPTABLES_BIN, "-w", "-D", "FORWARD", "-i", v.netIf, "-j", v.chainName)
	_ = cmd.Run()

	// iptables -w -F [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-w", "-F", v.chainName)
	_ = cmd.Run()

	// iptables -w -X [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-w", "-X", v.chainName)
	_ = cmd.Run()

	// ipset destroy [IP_BLOCK_SET]
	cmd = exec.Command(IPSET_BIN, "destroy", v.ipBlockSet)
	_ = cmd.Run()

	// create new stuff
	// iptables -w -N [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-w", "-N", v.chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -A FORWARD -i [TAP_NAME] -j [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-w", "-A", "FORWARD", "-i", v.netIf, "-j", v.chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ipset create [IP_BLOCK_SET] hash:ip netmask 30 TODO: make this configurable
	cmd = exec.Command(IPSET_BIN, "create", v.ipBlockSet, "hash:ip", "netmask", "30")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -w -A [CHAIN_NAME] -m set --match-set [IP_BLOCK_SET] dst -j REJECT --reject-with icmp-net-unreachable
	cmd = exec.Command(IPTABLES_BIN, "-w", "-A", v.chainName, "-m", "set", "--match-set", v.ipBlockSet, "dst", "-j", "REJECT", "--reject-with", "icmp-net-unreachable")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}
	return nil
}

func (v *vm) removeIPSet() error {
	log.Debugf("Removing ipset for %s", v.netIf)
	// iptables -D FORWARD -i [TAP_NAME] -j [CHAIN_NAME]
	cmd := exec.Command(IPTABLES_BIN, "-D", "FORWARD", "-i", v.netIf, "-j", v.chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// iptables -F [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-F", v.chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}
	// iptables -X [CHAIN_NAME]
	cmd = exec.Command(IPTABLES_BIN, "-X", v.chainName)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// ipset destroy [IP_BLOCK_SET]
	cmd = exec.Command(IPSET_BIN, "destroy", v.ipBlockSet)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (v *vm) blockNet(target net.IPNet) error {

	//log.Debug("blocking ", target.String(), " in ", v.ipBlockSet)
	// ipset add [IP_BLOCK_SET] [TARGET_NETWORK] -exist
	cmd := exec.Command(IPSET_BIN, "add", v.ipBlockSet, target.String(), "-exist")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (v *vm) unblockNet(target net.IPNet) error {

	log.Debug("unblocking ", target.String(), " in ", v.ipBlockSet)
	// ipset del [IP_BLOCK_SET] [TARGET_NETWORK]
	cmd := exec.Command(IPSET_BIN, "del", v.ipBlockSet, target.String())

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}
	return nil
}

//
//func (v *vm) configureIPSet(id orchestrator.MachineID) error {
//	// come up with a chain name and ip blockset name
//	v.chainName = fmt.Sprintf("CT-%d-%d", id.Group, id.Id)
//
//	v.ipBlockSet = fmt.Sprintf("CT-%d-%d-bl", id.Group, id.Id)
//
//	// remove old stuff, but ignore any errors
//	// iptables -D FORWARD -i [TAP_NAME] -j [CHAIN_NAME]
//	cmd := exec.Command(IPTABLES_BIN, "-D", "FORWARD", "-i", v.netIf, "-j", v.chainName)
//	_ = cmd.Run()
//
//	// iptables -F [CHAIN_NAME]
//	cmd = exec.Command(IPTABLES_BIN, "-F", v.chainName)
//	_ = cmd.Run()
//
//	// iptables -X [CHAIN_NAME]
//	cmd = exec.Command(IPTABLES_BIN, "-X", v.chainName)
//	_ = cmd.Run()
//
//	// ipset destroy [IP_BLOCK_SET]
//	cmd = exec.Command(IPSET_BIN, "destroy", v.ipBlockSet)
//	_ = cmd.Run()
//
//	// create new stuff
//	// iptables -N [CHAIN_NAME]
//	cmd = exec.Command(IPTABLES_BIN, "-N", v.chainName)
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//
//	// iptables -A FORWARD -i [TAP_NAME] -j [CHAIN_NAME]
//	cmd = exec.Command(IPTABLES_BIN, "-A", "FORWARD", "-i", v.netIf, "-j", v.chainName)
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//
//	// ipset create [IP_BLOCK_SET] bitmap:ip range 10.0.0.0/8 netmask 30 TODO: make this configurable
//	cmd = exec.Command(IPSET_BIN, "create", v.ipBlockSet, "bitmap:ip", "range", "10.0.0.0/8", "netmask", "30")
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//
//	// iptables -A [CHAIN_NAME] -m set --match-set [IP_BLOCK_SET] dst -j REJECT --reject-with icmp-net-unreachable
//	cmd = exec.Command(IPTABLES_BIN, "-A", v.chainName, "-m", "set", "--match-set", v.ipBlockSet, "dst", "-j", "REJECT", "--reject-with", "icmp-net-unreachable")
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//	return nil
//}
//
//func (v *vm) blockNet(target net.IPNet) error {
//
//	log.Debug("blocking ", target.String(), " in ", v.ipBlockSet)
//	// ipset add [IP_BLOCK_SET] [TARGET_NETWORK]
//	cmd := exec.Command(IPSET_BIN, "add", v.ipBlockSet, target.String())
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//
//	return nil
//}
//
//func (v *vm) unblockNet(target net.IPNet) error {
//
//	log.Debug("unblocking ", target.String(), " in ", v.ipBlockSet)
//	// ipset del [IP_BLOCK_SET] [TARGET_NETWORK]
//	cmd := exec.Command(IPSET_BIN, "del", v.ipBlockSet, target.String())
//
//	if out, err := cmd.CombinedOutput(); err != nil {
//		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
//	}
//	return nil
//}
