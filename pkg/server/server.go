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

package server

import (
	"context"
	"os"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/peer"
	"github.com/OpenFogStack/celestial/proto/celestial"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type PeeringBackend interface {
	Register(host orchestrator.Host) (string, string, error)
	InitPeering(map[orchestrator.Host]peer.HostInfo) error
	Stop() error
}

// Server handles grpc requests.
type Server struct {
	o  *orchestrator.Orchestrator
	pb PeeringBackend
}

// New creates a new Server for grpc requests.
func New(o *orchestrator.Orchestrator, pb PeeringBackend) *Server {
	return &Server{
		o:  o,
		pb: pb,
	}
}

func (s *Server) Stop(_ context.Context, _ *celestial.Empty) (*celestial.Empty, error) {
	err := s.o.Stop()
	if err != nil {
		return nil, err
	}

	s.o = nil
	s.pb = nil

	go func() {
		time.Sleep(5 * time.Second)
		log.Debugf("stopping backend")
		os.Exit(0)
	}()

	return &celestial.Empty{}, nil
}

func (s *Server) Register(_ context.Context, request *celestial.RegisterRequest) (*celestial.RegisterResponse, error) {
	cpus, ram, err := s.o.GetResources()

	if err != nil {
		return nil, err
	}

	peerPublicKey, peerListenAddr, err := s.pb.Register(orchestrator.Host(request.Host))

	if err != nil {
		return nil, err
	}

	return &celestial.RegisterResponse{
		AvailableCpus:  cpus,
		AvailableRam:   ram,
		PeerPublicKey:  peerPublicKey,
		PeerListenAddr: peerListenAddr,
	}, nil
}

func (s *Server) Init(_ context.Context, request *celestial.InitRequest) (*celestial.Empty, error) {
	machineList := make(map[orchestrator.MachineID]orchestrator.MachineConfig)
	machineHosts := make(map[orchestrator.MachineID]orchestrator.Host)

	for _, machine := range request.Machines {
		id := orchestrator.MachineID{
			Group: uint8(machine.Id.Group),
			Id:    machine.Id.Id,
		}

		machineList[id] = orchestrator.MachineConfig{
			VCPUCount:  uint8(machine.Config.VcpuCount),
			RAM:        machine.Config.Ram,
			DiskSize:   machine.Config.DiskSize,
			DiskImage:  machine.Config.RootImage,
			Kernel:     machine.Config.Kernel,
			BootParams: machine.Config.BootParameters,
		}

		machineHosts[id] = orchestrator.Host(machine.Host)
	}

	machineNames := make(map[orchestrator.MachineID]string)

	for _, machine := range request.Machines {
		if machine.Id.Name != nil {
			machineNames[orchestrator.MachineID{
				Group: uint8(machine.Id.Group),
				Id:    machine.Id.Id,
			}] = *machine.Id.Name
		}
	}

	hostList := make(map[orchestrator.Host]peer.HostInfo)

	for _, host := range request.Hosts {
		hostList[orchestrator.Host(host.Id)] = peer.HostInfo{
			Addr:      host.PeerListenAddr,
			PublicKey: host.PeerPublicKey,
		}
	}

	err := s.pb.InitPeering(hostList)

	if err != nil {
		return nil, err
	}

	err = s.o.Initialize(machineList, machineHosts, machineNames)

	if err != nil {
		return nil, err
	}

	return &celestial.Empty{}, nil
}

func (s *Server) Update(_ context.Context, request *celestial.UpdateRequest) (*celestial.Empty, error) {

	ns := make(orchestrator.NetworkState)

	for _, n := range request.NetworkDiffs {
		id := orchestrator.MachineID{
			Group: uint8(n.Id.Group),
			Id:    n.Id.Id,
		}

		ns[id] = make(map[orchestrator.MachineID]*orchestrator.Link)

		for _, l := range n.Links {
			target := orchestrator.MachineID{
				Group: uint8(l.Target.Group),
				Id:    l.Target.Id,
			}

			//log.Debugf("link from %s to %s: %v", id.String(), target.String(), l)

			if l.Blocked {
				ns[id][target] = &orchestrator.Link{
					Blocked: true,
				}
				continue
			}

			ns[id][target] = &orchestrator.Link{
				Latency:   l.Latency,
				Bandwidth: l.Bandwidth,
				Blocked:   false,
				Next: orchestrator.MachineID{
					Group: uint8(l.Next.Group),
					Id:    l.Next.Id,
				},
			}
		}
	}

	ms := make(map[orchestrator.MachineID]orchestrator.MachineState)

	for _, m := range request.MachineDiffs {
		id := orchestrator.MachineID{
			Group: uint8(m.Id.Group),
			Id:    m.Id.Id,
		}

		switch m.Active {
		case celestial.VMState_VM_STATE_ACTIVE:
			ms[id] = orchestrator.ACTIVE
		case celestial.VMState_VM_STATE_STOPPED:
			ms[id] = orchestrator.STOPPED
		}
	}

	err := s.o.Update(&orchestrator.State{
		NetworkState:  ns,
		MachinesState: ms,
	})

	if err != nil {
		return nil, err
	}

	return &celestial.Empty{}, nil
}
