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

package server

import (
	"context"
	"runtime"

	"github.com/pkg/errors"

	"github.com/pbnjay/memory"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/commons"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/proto/celestial"
)

// Server handles grpc requests.
type Server struct {
	o *orchestrator.Orchestrator
}

// New creates a new Server for grpc requests.
func New(o *orchestrator.Orchestrator) *Server {
	return &Server{o: o}
}

func (s *Server) InitRemotes(_ context.Context, request *celestial.InitRemotesRequest) (*celestial.Empty, error) {
	log.Debugf("Setting peer ID to %d", request.Index)
	err := s.o.SetPeerID(request.Index)

	if err != nil {
		log.Errorf("%+v\n", err)
		return nil, errors.WithStack(err)
	}

	addr := make([]string, len(request.Remotehosts))

	for i := range request.Remotehosts {
		addr[request.Remotehosts[i].Index] = request.Remotehosts[i].Addr
	}

	log.Debug("Initializing remotes")
	err = s.o.InitRemotes(addr)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &celestial.Empty{}, errors.WithStack(err)
}

func (s *Server) StartPeering(_ context.Context, _ *celestial.Empty) (*celestial.Empty, error) {
	err := s.o.StartPeering()

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &celestial.Empty{}, errors.WithStack(err)
}

// GetHostInfo handles GetHostInfo grpc requests.
func (s *Server) GetHostInfo(_ context.Context, _ *celestial.Empty) (*celestial.HostInfo, error) {

	log.Info("Server: received GetHostInfo request")

	return &celestial.HostInfo{
		Cpu: uint64(runtime.NumCPU()),
		Mem: memory.TotalMemory(),
	}, nil
}

func (s *Server) HostReady(_ context.Context, _ *celestial.Empty) (*celestial.ReadyInfo, error) {
	ready, created := s.o.Ready()
	return &celestial.ReadyInfo{
		Ready:   ready,
		Created: created,
	}, nil
}

// Init handles Init grpc requests.
func (s *Server) Init(_ context.Context, r *celestial.InitRequest) (*celestial.Empty, error) {

	log.Infof("Server: received Init for database: useDB: %v, host: %s", r.Database, r.DatabaseHost)

	if r.Database {
		err := s.o.InitDB(r.DatabaseHost)
		if err != nil {
			log.Errorf("%+v\n", err)
			return nil, errors.WithStack(err)
		}
	}

	log.Infof("Server: received Init request for %d shells", r.Shellcount)

	shells := make([]commons.Shell, 0, len(r.Shells))

	for _, shell := range r.Shells {
		shells = append(shells, commons.Shell{
			ShellID: shell.Id,
			Planes:  shell.Planes,
		})
	}

	err := s.o.InitShells(shells)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &celestial.Empty{}, errors.WithStack(err)
}

// CreateMachine handles CreateMachine grpc requests.
func (s *Server) CreateMachine(_ context.Context, r *celestial.CreateMachineRequest) (*celestial.Empty, error) {

	log.Infof("Server: received CreateMachine request for machine %#v with config %#v, status: %v", r.Machine, r.Firecrackerconfig, r.Status)

	if !s.o.Initialized {
		return nil, errors.New("host is not yet initialized")
	}

	err := s.o.CreateMachine(commons.MachineID{
		Shell: r.Machine.Shell,
		ID:    r.Machine.Id,
		Name:  r.Machine.Name,
	}, r.Firecrackerconfig.Vcpu, r.Firecrackerconfig.Mem, r.Firecrackerconfig.Ht, r.Firecrackerconfig.Disk, r.Firecrackerconfig.Bootparams, r.Firecrackerconfig.Kernel, r.Firecrackerconfig.Rootfs, r.Networkconfig.Bandwidth, r.Status)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &celestial.Empty{}, errors.WithStack(err)
}

// ModifyMachine handles ModifyMachine grpc requests.
func (s *Server) ModifyMachine(_ context.Context, r *celestial.ModifyMachineRequest) (*celestial.Empty, error) {

	log.Infof("Server: received ModifyMachine request for machine %s to status %t", r.Machine.String(), r.Status)

	if !s.o.Initialized {
		return nil, errors.New("host is not yet initialized")
	}

	err := s.o.ModifyMachine(commons.MachineID{
		Shell: r.Machine.Shell,
		ID:    r.Machine.Id,
	}, r.Status)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &celestial.Empty{}, errors.WithStack(err)
}

// ModifyLinks handles ModifyLinks grpc requests.
func (s *Server) ModifyLinks(_ context.Context, r *celestial.ModifyLinksRequest) (*celestial.Empty, error) {

	// log.Infof("Server: received ModifyLinks request for machine %s: %d to modify, %d to remove", r.A.String(), len(r.Modify), len(r.Remove))

	if !s.o.Initialized {
		return nil, errors.New("host is not yet initialized")
	}

	machineA := commons.MachineID{
		Shell: r.A.Shell,
		ID:    r.A.Id,
	}

	err := s.o.LockForLink(machineA)

	if err != nil {
		return nil, err
	}

	defer func(o *orchestrator.Orchestrator, a commons.MachineID) {
		err := o.UnlockForLink(a)
		if err != nil {
			log.Error(err.Error())
		}
	}(s.o, machineA)

	for _, modify := range r.Modify {
		//log.Debugf("modify: %s", modify.String())
		err := s.o.ModifyLink(machineA, commons.MachineID{
			Shell: modify.B.Shell,
			ID:    modify.B.Id,
		}, modify.Latency, modify.Bandwidth)

		if err != nil {
			log.Errorf("%+v\n", err)
		}
	}

	for _, remove := range r.Remove {
		err := s.o.RemoveLink(machineA, commons.MachineID{
			Shell: remove.B.Shell,
			ID:    remove.B.Id,
		})

		if err != nil {
			log.Errorf("%+v\n", err)
		}
	}

	return &celestial.Empty{}, nil
}
