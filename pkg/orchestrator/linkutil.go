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
	"fmt"
	"os/exec"
	"strconv"
	"sync/atomic"

	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
)

func createQDisc(tapName string) (int64, error) {
	// remove old stuff first
	err := removeRootQDisc(tapName, true)

	if err != nil {
		return 0, errors.WithStack(err)
	}

	// tc qdisc add dev [TAP_NAME] root handle 1: htb default 1 r2q 1
	cmd := exec.Command(TC, "qdisc", "add", "dev", tapName, "root", "handle", "1:", "htb", "default", "1", "r2q", "1")

	if out, err := cmd.CombinedOutput(); err != nil {
		return 0, errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc class add dev [TAP_NAME] parent 1: classid 1:1 htb rate [DEFAULTRATE] quantum 1514

	cmd = exec.Command(TC, "class", "add", "dev", tapName, "parent", "1:", "classid", "1:1", "htb", "rate", DEFAULTRATE, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return 0, errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// return starting index for delays
	return 1, nil
}

func createLink(tapName string, index int64, a string, b string) error {
	log.Debugf("creating link for tap %s from a %s to b %s with index %d", tapName, a, b, index)

	// tc class add dev [TAP_NAME] parent 1: classid 1:[INDEX] htb rate [DEFAULTRATE] quantum 1514

	cmd := exec.Command(TC, "class", "add", "dev", tapName, "parent", "1:", "classid", fmt.Sprintf("1:%d", index), "htb", "rate", DEFAULTRATE, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc qdisc add dev [TAP_NAME] parent 1:[INDEX] handle [INDEX]: netem delay 0.0ms limit 1000000

	cmd = exec.Command(TC, "qdisc", "add", "dev", tapName, "parent", fmt.Sprintf("1:%d", index), "handle", fmt.Sprintf("%d:", index), "netem", "delay", "0.0", "limit", "1000000")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// yes its required to set "src" as "dest_net" and "dst" as "source_net", this is intentional
	// removing the "match ip dst [SOURCE_NET]" filter as it wouldn't do anything: there is only one network on this tap anyway
	// tc filter add dev [TAP_NAME] protocol ip parent 1: prio [INDEX] u32 match ip src [DEST_NET] classid 1:[INDEX]

	cmd = exec.Command(TC, "filter", "add", "dev", tapName, "protocol", "ip", "parent", "1:", "prio", strconv.Itoa(int(index)), "u32", "match", "ip", "src", b, "classid", fmt.Sprintf("1:%d", index))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func updateDelay(tapName string, index int64, delay float64, bandwidth int) error {

	log.Debugf("updating delay for tap %s with index %d, delay %.2f, bandwidth %d", tapName, index, delay, bandwidth)

	rate := fmt.Sprintf("%d.0kbit", bandwidth)

	// tc class change dev [TAP_NAME] parent 1: classid 1:[INDEX] htb rate [RATE] quantum 1514

	cmd := exec.Command(TC, "class", "change", "dev", tapName, "parent", "1:", "classid", fmt.Sprintf("1:%d", index), "htb", "rate", rate, "quantum", "1514")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc qdisc change dev [TAP_NAME] parent 1:[INDEX] handle [INDEX]: netem delay [DELAY].0ms limit 1000000

	cmd = exec.Command(TC, "qdisc", "change", "dev", tapName, "parent", fmt.Sprintf("1:%d", index), "handle", fmt.Sprintf("%d:", index), "netem", "delay", fmt.Sprintf("%.1fms", delay), "limit", "1000000")

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func removeLink(tapName string, index int64) error {

	// unfortunately cannot remove filter because there is no way to specify a specific filter
	// tc filter del dev [TAP_NAME] protocol ip parent 1: prio [INDEX]

	cmd := exec.Command(TC, "filter", "del", "dev", tapName, "protocol", "ip", "parent", "1:", "prio", strconv.Itoa(int(index)))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc qdisc del dev [TAP_NAME] parent 1:[INDEX] handle [INDEX]:

	cmd = exec.Command(TC, "qdisc", "del", "dev", tapName, "parent", fmt.Sprintf("1:%d", index), "handle", fmt.Sprintf("%d:", index))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	// tc class del dev [TAP_NAME] parent 1: classid 1:[INDEX]

	cmd = exec.Command(TC, "class", "del", "dev", tapName, "parent", "1:", "classid", fmt.Sprintf("1:%d", index))

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil

}

func blockLink(ipBlockSet string, b string) error {

	// ipset add [IP_BLOCK_SET] [TARGET_NETWORK]
	cmd := exec.Command(IPSET, "add", ipBlockSet, b)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func unblockLink(ipBlockSet string, b string) error {

	// ipset add [IP_BLOCK_SET] [TARGET_NETWORK]
	cmd := exec.Command(IPSET, "del", ipBlockSet, b)

	if out, err := cmd.CombinedOutput(); err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}
	return nil
}

func removeRootQDisc(tapName string, allowFail bool) error {
	// tc qdisc del dev [TAP_NAME] root
	cmd := exec.Command(TC, "qdisc", "del", "dev", tapName, "root")

	if out, err := cmd.CombinedOutput(); !allowFail && err != nil {
		return errors.Wrapf(err, "%#v: output: %s", cmd.Args, out)
	}

	return nil
}

func (o *Orchestrator) modifyLink(source *machine, target *machine, latency float64, bandwidth uint64) error {
	if !source.isLocal {
		return errors.Errorf("machine %d is not local", source.id)
	}

	l, ok := source.links[target.network.String()]

	if !ok {

		l = &link{
			sourceNet:   source.network.String(),
			targetNet:   target.network.String(),
			latency:     latency,
			bandwidth:   bandwidth,
			blocked:     false,
			initialized: false,
		}

		log.Debugf("adding link for source %s, latency %.1f, bandwidth %d", source.tapName, l.latency, l.bandwidth)

		source.links[target.network.String()] = l

		if source.netInitialized {

			handle := atomic.AddInt64(&source.nextHandle, 1)

			l.handle = source.nextHandle
			source.nextHandle = handle
		}
	}

	l.latency = latency
	l.bandwidth = bandwidth

	if source.netInitialized {

		if !l.initialized {
			err := createLink(source.tapName, l.handle, l.sourceNet, l.targetNet)
			l.initialized = true

			if err != nil {
				return errors.WithStack(err)
			}
		}

		if l.blocked {
			err := unblockLink(source.ipBlockSet, l.targetNet)

			if err != nil {
				return errors.WithStack(err)
			}
		}

		log.Debugf("updating %d (%s) to %d (%s) to %.1fms %d", source.id, l.sourceNet, target.id, l.targetNet, l.latency, l.bandwidth)
		err := updateDelay(source.tapName, l.handle, l.latency, int(l.bandwidth))

		if err != nil {
			return errors.WithStack(err)
		}
	}

	l.blocked = false

	return nil

}

func (o *Orchestrator) removeLink(source *machine, target *machine) error {
	if !source.isLocal {
		return errors.Errorf("machine %d is not local", source.id)
	}

	l, ok := source.links[target.network.String()]

	if !ok {

		l = &link{
			sourceNet:   source.network.String(),
			targetNet:   target.network.String(),
			latency:     MAXLATENCY,
			bandwidth:   MINBANDWIDTH,
			initialized: false,
		}

		log.Debugf("adding link for source %s, latency %.1f, bandwidth %d", source.tapName, l.latency, l.bandwidth)

		source.links[target.network.String()] = l

		if source.netInitialized {

			handle := atomic.AddInt64(&source.nextHandle, 1)

			l.handle = handle
		}
	}

	l.latency = MAXLATENCY
	l.bandwidth = MINBANDWIDTH

	if source.netInitialized {
		log.Debugf("updating %d (%s) to %d (%s) to block", source.id, l.sourceNet, target.id, l.targetNet)

		if l.initialized {
			err := removeLink(source.tapName, l.handle)
			if err != nil {
				return errors.WithStack(err)
			}
			l.initialized = false
		}

		if !l.blocked {
			err := blockLink(source.ipBlockSet, l.targetNet)

			l.blocked = true

			if err != nil {
				return errors.WithStack(err)
			}
		}

	}

	return nil

}
