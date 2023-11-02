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
	"sync"

	"github.com/pkg/errors"

	"google.golang.org/grpc"

	"github.com/OpenFogStack/celestial/pkg/commons"
	"github.com/OpenFogStack/celestial/proto/database"
)

const (
	FCROOTPATH    = "/celestial"
	FCOUTFILEPATH = "/celestial/out/"

	DEFAULTRATE = "10.0Gbps"

	// MAXLATENCY means unusable: nothing is usable above 999.999 seconds?
	MAXLATENCY   = 999999.9
	MINBANDWIDTH = 0

	GUESTINTERFACE = "eth0"
	NAMESERVER     = "1.1.1.1"

	WGPORT      = 3000
	WGINTERFACE = "wg0"
	MASK        = "/26"

	// setting the path directly means we don't have to consult lookpath for each command
	// TODO: in theory we should probably add a LookPath to this

	TC       = "/sbin/tc"
	IPTABLES = "/sbin/iptables"
	IPSET    = "/sbin/ipset"
)

// Orchestrator orchestrates different firecracker microVMs on the host.
type Orchestrator struct {
	shells      map[shellid]*shell
	shellNo     int
	Initialized bool

	eager            bool
	initDelay        int
	networkInterface string

	groundstations map[string]*machine
	gstLock        *sync.RWMutex

	remoteHosts map[uint64]*host
	ownID       uint64
	ownHost     *host

	useDB    bool
	dbClient database.DatabaseClient

	debug bool

	// some information on how many machines were created and how many are left
	outstanding int64
	created     uint64
}

func (o *Orchestrator) InitDB(host string) error {
	o.useDB = true

	c, err := grpc.Dial(host, grpc.WithInsecure())

	if err != nil {
		return errors.WithStack(err)
	}

	o.dbClient = database.NewDatabaseClient(c)

	return errors.WithStack(err)

}

func (o *Orchestrator) InitShells(s []commons.Shell) error {
	// bootstrapping
	for i, curr := range s {

		machines := make(map[id]*machine)

		o.shells[shellid(i)] = &shell{
			planeNo:  curr.Planes,
			machines: machines,
			RWMutex:  sync.RWMutex{},
		}
	}

	// init shell for ground stations
	o.shells[shellid(-1)] = &shell{
		machines: make(map[id]*machine),
		RWMutex:  sync.RWMutex{},
	}

	o.shellNo = len(s)
	o.Initialized = true

	err := initHost(o.networkInterface)

	if err != nil {
		return errors.WithStack(err)
	}

	return nil
}

func (o *Orchestrator) Ready() (bool, uint64) {
	return o.outstanding <= 0, o.created
}

func (o *Orchestrator) Cleanup() error {
	if !o.Initialized {
		return errors.New("cannot run cleanup: orchestrator not initialized")
	}

	// shutdown all machines
	for _, shell := range o.shells {
		for _, machine := range shell.machines {
			err := o.destroy(machine)

			if err != nil {
				return errors.WithStack(err)
			}
		}
	}

	return nil
}

// New creates a new Orchestrator.
func New(eager bool, initDelay int, networkInterface string, debug bool) (*Orchestrator, error) {

	return &Orchestrator{
		eager:            eager,
		initDelay:        initDelay,
		shells:           make(map[shellid]*shell),
		remoteHosts:      make(map[uint64]*host),
		groundstations:   make(map[string]*machine),
		gstLock:          &sync.RWMutex{},
		debug:            debug,
		networkInterface: networkInterface,
	}, nil
}
