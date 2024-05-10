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
	"net"
	"strings"

	"github.com/pkg/errors"
)

type NodeIDInfo struct {
	ID   MachineID
	Name string
}

type NodeInfo struct {
	ID     NodeIDInfo
	Active bool
}

type GroupInfo struct {
	Group uint8
	Nodes []NodeInfo
}

type ConstellationInfo struct {
	Groups []GroupInfo
}

type SegmentInfo struct {
	Source        MachineID
	Target        MachineID
	LatencyUs     uint32
	BandwidthKbps uint64
}

type PathInfo struct {
	Source        MachineID
	Target        MachineID
	LatencyUs     uint32
	BandwidthKbps uint64
	Segments      []SegmentInfo
	Blocked       bool
}

func (o *Orchestrator) InfoGetIPAddressByID(id MachineID) (net.IP, error) {
	if !o.initialized {
		return nil, errors.New("orchestrator not initialized")
	}

	ip, err := o.virt.GetIPAddress(id)

	if err != nil {
		return net.IP{}, errors.Wrap(err, "could not get IP address")
	}

	return ip.IP, nil
}

func (o *Orchestrator) InfoGetIPAddressByName(name string) (net.IP, error) {
	var id MachineID
	ok := false

	for m, i := range o.machineNames {
		if strings.EqualFold(m, name) {
			id = i
			ok = true
		}
	}

	if !ok {
		return net.IP{}, errors.Errorf("machine with name %s not found", name)
	}

	ip, err := o.virt.GetIPAddress(id)

	if err != nil {
		return net.IP{}, errors.Wrap(err, "could not get IP address")
	}

	return ip.IP, nil
}

func (o *Orchestrator) InfoGetNodeByIP(ip net.IP) (NodeInfo, error) {
	if !o.initialized {
		return NodeInfo{}, errors.New("orchestrator not initialized")
	}

	id, err := o.virt.ResolveIPAddress(ip)

	if err != nil {
		return NodeInfo{}, err
	}

	n := NodeInfo{
		ID: NodeIDInfo{
			ID:   id,
			Name: "",
		},
	}

	if o.machines[id].name != "" {
		n.ID.Name = o.machines[id].name
	}

	if o.State.MachinesState[id] == ACTIVE {
		n.Active = true
	}

	return n, nil
}

func (o *Orchestrator) InfoGetConstellation() (ConstellationInfo, error) {
	if !o.initialized {
		return ConstellationInfo{}, errors.New("orchestrator not initialized")
	}

	g := make(map[uint8]map[uint32]NodeInfo)

	for m := range o.machines {
		if _, ok := g[m.Group]; !ok {
			g[m.Group] = make(map[uint32]NodeInfo)
		}

		n := NodeInfo{
			ID: NodeIDInfo{
				ID:   m,
				Name: o.machines[m].name,
			},
		}

		if o.State.MachinesState[m] == ACTIVE {
			n.Active = true
		}

		g[m.Group][m.Id] = n
	}

	c := ConstellationInfo{
		Groups: make([]GroupInfo, len(g)),
	}

	for i, group := range g {
		c.Groups[i] = GroupInfo{
			Group: i,
			Nodes: make([]NodeInfo, len(group)),
		}

		for j, node := range group {
			c.Groups[i].Nodes[j] = node
		}
	}

	return c, nil
}

func (o *Orchestrator) InfoGetGroup(group uint8) (GroupInfo, error) {
	if !o.initialized {
		return GroupInfo{}, errors.New("orchestrator not initialized")
	}

	g := make(map[uint32]NodeInfo)

	for m := range o.machines {
		if m.Group != group {
			continue
		}

		n := NodeInfo{
			ID: NodeIDInfo{
				ID:   m,
				Name: o.machines[m].name,
			},
		}

		if o.State.MachinesState[m] == ACTIVE {
			n.Active = true
		}

		g[m.Id] = n
	}

	c := GroupInfo{
		Group: group,
		Nodes: make([]NodeInfo, len(g)),
	}

	for i := range c.Nodes {
		c.Nodes[i] = g[uint32(i)]
	}

	return c, nil
}

func (o *Orchestrator) InfoGetNodeByID(id MachineID) (NodeInfo, error) {
	if !o.initialized {
		return NodeInfo{}, errors.New("orchestrator not initialized")
	}

	n := NodeInfo{
		ID: NodeIDInfo{
			ID:   id,
			Name: "",
		},
	}

	if o.machines[id].name != "" {
		n.ID.Name = o.machines[id].name
	}

	if o.State.MachinesState[id] == ACTIVE {
		n.Active = true
	}

	return n, nil
}

func (o *Orchestrator) InfoGetNodeNameByID(id MachineID) (string, error) {
	if !o.initialized {
		return "", errors.New("orchestrator not initialized")
	}

	name := o.machines[id].name

	if name == "" {
		return "", errors.Errorf("machine with id %s does not have a name", id)
	}

	return name, nil
}

func (o *Orchestrator) InfoGetNodeByName(name string) (NodeInfo, error) {
	if !o.initialized {
		return NodeInfo{}, errors.New("orchestrator not initialized")
	}

	id, ok := o.machineNames[name]

	if !ok {
		return NodeInfo{}, errors.Errorf("machine with name %s not found", name)
	}

	n := NodeInfo{
		ID: NodeIDInfo{
			ID:   id,
			Name: name,
		},
	}

	if o.State.MachinesState[id] == ACTIVE {
		n.Active = true
	}

	return n, nil
}

func (o *Orchestrator) InfoGetPath(source, destination MachineID) (PathInfo, error) {
	if !o.initialized {
		return PathInfo{}, errors.New("orchestrator not initialized")
	}

	return path(source, destination, o.State.NetworkState)
}
