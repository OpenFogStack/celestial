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

package dnsservice

import (
	"fmt"
	"net"
	"strconv"

	"github.com/pkg/errors"

	"github.com/miekg/dns"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

var o *orchestrator.Orchestrator

// https://gist.github.com/walm/0d67b4fb2d5daf3edd4fad3e13b162cb

func getIPFromDNS(qName string) (string, error) {
	labels := dns.SplitDomainName(qName)

	if len(labels) != 3 {
		return "", errors.Errorf("number of labels %d is not 3", len(labels))
	}

	if labels[len(labels)-1] != "celestial" {
		return "", errors.Errorf("provided TLD is not celestial")
	}

	if labels[len(labels)-2] == "gst" {
		return o.GetGSTIPAddress(labels[len(labels)-3])
	}

	shell, err := strconv.ParseInt(labels[len(labels)-2], 10, 64)

	if err != nil {
		return "", errors.Errorf("provided shell %s could not be parsed to int", labels[len(labels)-2])
	}

	id, err := strconv.ParseUint(labels[len(labels)-3], 10, 64)

	if err != nil {
		return "", errors.Errorf("provided id %s could not be parsed to int", labels[len(labels)-3])
	}

	return o.GetIPAddress(shell, id)
}

func handleDnsRequest(w dns.ResponseWriter, r *dns.Msg) {
	m := new(dns.Msg)
	m.SetReply(r)
	m.Compress = false

	log.Debugf("DNS Query: %#v", *r)

	switch r.Opcode {
	case dns.OpcodeQuery:
		for _, q := range m.Question {
			switch q.Qtype {
			case dns.TypeA:

				ip, err := getIPFromDNS(q.Name)

				if err != nil {
					log.Debugf(err.Error())
				}

				if ip != "" {
					rr, err := dns.NewRR(fmt.Sprintf("%s A %s", q.Name, ip))
					if err == nil {
						m.Answer = append(m.Answer, rr)
					}
				}
			}
		}
	}

	err := w.WriteMsg(m)

	if err != nil {
		log.Error(err.Error())
	}
}

// Start starts our DNS service. The service helps applications find out the IP addresses
// of other satellites. It uses the custom (made up) "celestial." TLD. A satellite DNS
// record has the form [ID].[SHELL].celestial, where [ID] is the identifier and [SHELL] is
// the index of the shell of the satellite. That maps to an IP address. Additionally,
// ground station IP addresses can be determined with [NAME].gst.celestial, where NAME is the
// ground station name.
// Our DNS server supports only queries, only UDP (no DNSSEC), and only A records.
func Start(port int, orch *orchestrator.Orchestrator) error {
	o = orch

	dns.HandleFunc("celestial.", handleDnsRequest)

	server := &dns.Server{Addr: net.JoinHostPort("", strconv.Itoa(port)), Net: "udp"}

	log.Printf("DNS server starting on %s", net.JoinHostPort("", strconv.Itoa(port)))

	err := server.ListenAndServe()

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return errors.WithStack(err)
}
