package orchestrator2

import (
	"net"

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
	Source    MachineID
	Target    MachineID
	Latency   uint32
	Bandwidth uint64
}

type PathInfo struct {
	Source    MachineID
	Target    MachineID
	Latency   uint32
	Bandwidth uint64
	Segments  []SegmentInfo
}

func (o *Orchestrator) InfoGetIPAddressByID(id MachineID) (net.IP, error) {
	ip, err := o.virt.GetIPAddress(id)

	if err != nil {
		return net.IP{}, errors.Wrap(err, "could not get IP address")
	}

	return ip.IP, nil
}

func (o *Orchestrator) InfoGetIPAddressByName(name string) (net.IP, error) {
	id, ok := o.machineNames[name]

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
		Groups: make([]GroupInfo, 0, len(g)),
	}

	for group := range g {
		c.Groups = append(c.Groups, GroupInfo{
			Group: group,
			Nodes: make([]NodeInfo, 0, len(g[group])),
		})

		for _, node := range g[group] {
			c.Groups[group].Nodes = append(c.Groups[group].Nodes, node)
		}
	}

	return c, nil
}

func (o *Orchestrator) InfoGetGroup(group uint8) (GroupInfo, error) {
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
		Nodes: make([]NodeInfo, 0, len(g)),
	}

	for _, node := range g {
		c.Nodes = append(c.Nodes, node)
	}

	return c, nil
}

func (o *Orchestrator) InfoGetNodeByID(id MachineID) (NodeInfo, error) {
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

	name := o.machines[id].name

	if name == "" {
		return "", errors.Errorf("machine with id %s does not have a name", id)
	}

	return name, nil
}

func (o *Orchestrator) InfoGetNodeByName(name string) (NodeInfo, error) {
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
	return path(source, destination, o.State.NetworkState)
}
