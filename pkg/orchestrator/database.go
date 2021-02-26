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
	"context"
	"io"

	"github.com/pkg/errors"
	"google.golang.org/protobuf/encoding/protojson"

	"github.com/OpenFogStack/celestial/proto/database"
)

// TODO: this is just super ugly

func (o *Orchestrator) DBGetConstellation(w io.Writer) error {
	if !o.useDB {
		return errors.New("database not in use")
	}

	c, err := o.dbClient.Constellation(context.Background(), &database.Empty{})

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := protojson.MarshalOptions{EmitUnpopulated: true, AllowPartial: true}.Marshal(c)

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = w.Write(m)

	return err
}

func (o *Orchestrator) DBGetShell(shell uint32, w io.Writer) error {
	if !o.useDB {
		return errors.New("database not in use")
	}

	s, err := o.dbClient.Shell(context.Background(), &database.ShellRequest{
		Shell: shell,
	})

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := protojson.MarshalOptions{EmitUnpopulated: true, AllowPartial: true}.Marshal(s)

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = w.Write(m)

	return err
}

func (o *Orchestrator) DBGetSatellite(shell uint32, sat uint32, w io.Writer) error {
	if !o.useDB {
		return errors.New("database not in use")
	}

	s, err := o.dbClient.Satellite(context.Background(), &database.SatelliteId{
		Shell: shell,
		Sat:   sat,
	})

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := protojson.MarshalOptions{EmitUnpopulated: true, AllowPartial: true}.Marshal(s)

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = w.Write(m)

	return err
}

func (o *Orchestrator) DBGetGroundStation(name string, w io.Writer) error {
	if !o.useDB {
		return errors.New("database not in use")
	}

	gst, err := o.dbClient.GroundStation(context.Background(), &database.GroundStationId{
		Name: name,
	})

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := protojson.MarshalOptions{EmitUnpopulated: true, AllowPartial: true}.Marshal(gst)

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = w.Write(m)

	return err
}

func (o *Orchestrator) DBGetPath(sourceShell int32, sourceId uint32, targetShell int32, targetId uint32, w io.Writer) error {
	if !o.useDB {
		return errors.New("database not in use")
	}

	p, err := o.dbClient.Path(context.Background(), &database.PathRequest{
		SourceShell: sourceShell,
		SourceSat:   sourceId,
		TargetShell: targetShell,
		TargetSat:   targetId,
	})

	if err != nil {
		return errors.WithStack(err)
	}

	m, err := protojson.MarshalOptions{EmitUnpopulated: true, AllowPartial: true}.Marshal(p)

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = w.Write(m)

	return err
}
