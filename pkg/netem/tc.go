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
	"fmt"
	"net"
	"os/exec"
	"strconv"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

const DEFAULTRATE = "10.0Gbps"

func getBaseNet(ipNet net.IPNet) *net.IPNet {
	// get the base network

	return &net.IPNet{
		IP:   ipNet.IP.Mask(ipNet.Mask),
		Mask: ipNet.Mask,
	}
}

func (v *vm) configureTC() error {
	// remove old stuff first
	// tc qdisc del dev [TAP_NAME] root
	cmd := exec.Command(TC_BIN, "qdisc", "del", "dev", v.netIf, "root")
	_ = cmd.Run()

	// tc qdisc add dev [TAP_NAME] root handle 1: htb default 1 r2q 1
	cmd = exec.Command(TC_BIN, "qdisc", "add", "dev", v.netIf, "root", "handle", "1:", "htb", "default", "1", "r2q", "1")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc class add dev [TAP_NAME] parent 1: classid 1:1 htb rate [DEFAULTRATE] quantum 1514

	cmd = exec.Command(TC_BIN, "class", "add", "dev", v.netIf, "parent", "1:", "classid", "1:1", "htb", "rate", DEFAULTRATE, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	v.handle = 1

	return nil
}

func (v *vm) removeTC() error {
	// remove old stuff first
	// tc qdisc del dev [TAP_NAME] root
	cmd := exec.Command(TC_BIN, "qdisc", "del", "dev", v.netIf, "root")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (v *vm) createQDisc(target net.IPNet) (uint16, error) {
	// this would be better to do atomically, but it's 16 bit...
	v.handle = v.handle + 1

	// tc class add dev [TAP_NAME] parent 1: classid 1:[INDEX] htb rate [DEFAULTRATE] quantum 1514
	cmd := exec.Command(TC_BIN, "class", "add", "dev", v.netIf, "parent", "1:", "classid", fmt.Sprintf("1:%d", v.handle), "htb", "rate", DEFAULTRATE, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return 0, errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc qdisc add dev [TAP_NAME] parent 1:[INDEX] handle [INDEX]: netem delay 0.0ms limit 1000000
	cmd = exec.Command(TC_BIN, "qdisc", "add", "dev", v.netIf, "parent", fmt.Sprintf("1:%d", v.handle), "handle", fmt.Sprintf("%d:", v.handle), "netem", "delay", "0.0", "limit", "1000000")

	if out, err := cmd.CombinedOutput(); err != nil {
		return 0, errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// yes its required to set "src" as "dest_net" and "dst" as "source_net", this is intentional
	// removing the "match ip dst [SOURCE_NET]" filter as it wouldn't do anything: there is only one network on this tap anyway
	// tc filter add dev [TAP_NAME] protocol ip parent 1: prio [INDEX] u32 match ip src [DEST_NET] classid 1:[INDEX]
	// thank god everything is symmetrical
	cmd = exec.Command(TC_BIN, "filter", "add", "dev", v.netIf, "protocol", "ip", "parent", "1:", "prio", strconv.Itoa(int(v.handle)), "u32", "match", "ip", "src", getBaseNet(target).String(), "classid", fmt.Sprintf("1:%d", v.handle))

	if out, err := cmd.CombinedOutput(); err != nil {
		return 0, errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return v.handle, nil
}

func (v *vm) updateDelay(target net.IPNet, delayUs uint32) error {

	log.Tracef("updating delay on %s for %s to %d", v.netIf, target.String(), delayUs)

	// get the index
	l, ok := v.links[fromIPNet(target)]

	if !ok {
		return errors.Errorf("unknown link %s", target.String())
	}

	// convert to milliseconds
	// x.y ms
	x := delayUs / 1000
	y := delayUs % 1000 / 10 // ignore the last digit, netem is not that accurate anyway

	// tc qdisc change dev [TAP_NAME] parent 1:[INDEX] handle [INDEX]: netem delay [DELAY].0ms limit 1000000
	cmd := exec.Command(TC_BIN, "qdisc", "change", "dev", v.netIf, "parent", fmt.Sprintf("1:%d", l.tcIndex), "handle", fmt.Sprintf("%d:", l.tcIndex), "netem", "delay", fmt.Sprintf("%d.%dms", x, y), "limit", "1000000")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (v *vm) updateBandwidth(target net.IPNet, bandwidthKbps uint64) error {

	log.Tracef("updating bandwidth on %s for %s to %d", v.netIf, target.String(), bandwidthKbps)

	// get the index
	l, ok := v.links[fromIPNet(target)]

	if !ok {
		return errors.Errorf("unknown link %s", target.String())
	}

	rate := fmt.Sprintf("%d.0kbit", bandwidthKbps)

	// tc class change dev [TAP_NAME] parent 1: classid 1:[INDEX] htb rate [RATE] quantum 1514
	cmd := exec.Command(TC_BIN, "class", "change", "dev", v.netIf, "parent", "1:", "classid", fmt.Sprintf("1:%d", l.tcIndex), "htb", "rate", rate, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}
