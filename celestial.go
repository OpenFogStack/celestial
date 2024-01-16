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
	"os"
	"os/signal"
	"strconv"
	"syscall"

	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"

	"github.com/OpenFogStack/celestial/pkg/dns"
	"github.com/OpenFogStack/celestial/pkg/info"
	"github.com/OpenFogStack/celestial/pkg/netem"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
	"github.com/OpenFogStack/celestial/pkg/peer"
	"github.com/OpenFogStack/celestial/pkg/server"
	"github.com/OpenFogStack/celestial/pkg/virt"
	"github.com/OpenFogStack/celestial/proto/celestial"
)

const (
	PEER_WGPORT        = 3000
	PEER_WGINTERFACE   = "wg0"
	PEER_MASK          = "/26"
	PEER_KEYPATH       = "/celestial/privatekey"
	DEFAULT_IF         = "ens4"
	DEFAULT_INIT_DELAY = 15
)

func main() {
	// needs some configuration data
	port := flag.Uint64("port", 1969, "Port to bind to")
	dnsServicePort := flag.Uint64("dns-service-port", 1970, "Port to bind DNS service server to")
	infoServerPort := flag.Uint64("info-server-port", 80, "Port to bind info server to")
	networkInterface := flag.String("network-interface", DEFAULT_IF, "Name of your main network interface")
	initDelay := flag.Uint64("init-delay", DEFAULT_INIT_DELAY, "Maximum delay when initially booting a machine -- can help reduce load at beginning of emulation")
	debug := flag.Bool("debug", false, "Enable debug logging")

	flag.Parse()

	log.SetLevel(log.WarnLevel)

	if *debug {
		log.SetLevel(log.DebugLevel)
	}

	s := grpc.NewServer()

	pb, err := peer.New(PEER_MASK, PEER_KEYPATH, PEER_WGINTERFACE, PEER_WGPORT)

	if err != nil {
		panic(err)
	}

	neb := netem.New()

	if err != nil {
		panic(err)
	}

	vb, err := virt.New(*networkInterface, *initDelay, pb, neb)

	if err != nil {
		panic(err)
	}

	o := orchestrator.New(vb)

	celestial.RegisterCelestialServer(s, server.New(o, pb))

	lisS, err := net.Listen("tcp", net.JoinHostPort("", strconv.Itoa(int(*port))))

	if err != nil {
		panic(err)
	}

	d := dns.New(o)

	go func() {
		err := d.Start(*dnsServicePort)
		if err != nil {
			panic(err.Error())
		}
	}()

	go func() {
		err := info.Start(*infoServerPort, o)
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

	// listen for SIGINT
	c := make(chan os.Signal, 1)

	signal.Notify(c, os.Interrupt, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)

	<-c

	err = o.Stop()

	if err != nil {
		panic(err.Error())
	}

	// stop the grpc servers
	s.Stop()

	// stop the dns server
	err = d.Stop()

	if err != nil {
		panic(err.Error())
	}

	os.Exit(0)
}
