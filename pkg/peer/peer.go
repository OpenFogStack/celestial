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

package peer

import (
	"context"

	"github.com/pkg/errors"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/commons"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/proto/peering"
)

// Peer handles internal grpc requests.
type Peer struct {
	o *orchestrator.Orchestrator
}

func (p *Peer) StartPeer(_ context.Context, request *peering.StartPeerRequest) (*peering.Empty, error) {
	err := p.o.StartPeer(request.Publickey, request.Index)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &peering.Empty{}, err
}

func (p *Peer) Route(_ context.Context, request *peering.RouteRequest) (*peering.Empty, error) {

	err := p.o.RouteMachine(commons.MachineID{
		Shell: request.Machine.Shell,
		ID:    request.Machine.Id,
		Name:  request.Machine.Name,
	}, request.Bandwidth, request.Index)

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return &peering.Empty{}, errors.WithStack(err)
}

// New creates a new Peering server for grpc requests.
func New(o *orchestrator.Orchestrator) *Peer {
	return &Peer{o: o}
}
