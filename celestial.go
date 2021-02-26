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

package main

import (
	"flag"
	"net"
	"strconv"

	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"

	"github.com/OpenFogStack/celestial/pkg/dnsservice"
	"github.com/OpenFogStack/celestial/pkg/infoserver"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/pkg/peer"
	"github.com/OpenFogStack/celestial/pkg/server"
	"github.com/OpenFogStack/celestial/proto/celestial"
	"github.com/OpenFogStack/celestial/proto/peering"
)

func main() {
	// needs some configuration data
	port := flag.Int("port", 1969, "Port to bind to")
	peeringPort := flag.Int("peer-port", 1970, "Port to bind peer to")
	dnsServicePort := flag.Int("dns-service-port", 53, "Port to bind DNS service server to")
	infoServerPort := flag.Int("info-server-port", 80, "Port to bind info server to")
	networkInterface := flag.String("network-interface", "ens4", "Name of your main network interface")
	initDelay := flag.Int("init-delay", 15, "Maximum delay when initialy booting a machine -- can help reduce load at beginning of emulation")
	eager := flag.Bool("eager", false, "Eager initialization -- start each machine at the beginning instead of lazily (default off)")

	flag.Parse()

	log.SetLevel(log.WarnLevel)

	s := grpc.NewServer()
	p := grpc.NewServer()

	o, err := orchestrator.New(*eager, *initDelay, *networkInterface)

	if err != nil {
		panic(err)
	}

	celestial.RegisterCelestialServer(s, server.New(o))
	peering.RegisterPeeringServer(p, peer.New(o))

	lisS, err := net.Listen("tcp", net.JoinHostPort("", strconv.Itoa(*port)))

	if err != nil {
		panic(err)
	}

	lisP, err := net.Listen("tcp", net.JoinHostPort("", strconv.Itoa(*peeringPort)))

	if err != nil {
		panic(err)
	}

	go func() {
		err := dnsservice.Start(*dnsServicePort, o)
		if err != nil {
			panic(err.Error())
		}
	}()
	go func() {
		err := infoserver.Start(*infoServerPort, o)
		if err != nil {
			panic(err.Error())
		}
	}()
	go func() {
		err := s.Serve(lisS)
		if err != nil {
			panic(err.Error())
		}
	}()
	panic(p.Serve(lisP))
}
