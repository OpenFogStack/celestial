// This file is part of Celestial (https://github.com/OpenFogStack/celestial).
// Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

package dns

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"strconv"
	"strings"

	"github.com/miekg/dns"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type DNSServer struct {
	*orchestrator.Orchestrator
}

// https://gist.github.com/walm/0d67b4fb2d5daf3edd4fad3e13b162cb

func (d *DNSServer) getIPFromDNS(qName string) (string, error) {
	labels := dns.SplitDomainName(qName)

	if len(labels) != 3 {
		return "", errors.Errorf("number of labels %d is not 3", len(labels))
	}

	if labels[len(labels)-1] != "celestial" {
		return "", errors.Errorf("provided TLD is not celestial")
	}

	if labels[len(labels)-2] == "gst" {
		ip, err := d.Orchestrator.InfoGetIPAddressByName(labels[len(labels)-3])
		if err != nil {
			return "", errors.WithStack(err)
		}
		return ip.String(), nil
	}

	shell, err := strconv.ParseInt(labels[len(labels)-2], 10, 64)

	if err != nil {
		return "", errors.Errorf("provided shell %s could not be parsed to int", labels[len(labels)-2])
	}

	id, err := strconv.ParseUint(labels[len(labels)-3], 10, 64)

	if err != nil {
		return "", errors.Errorf("provided id %s could not be parsed to int", labels[len(labels)-3])
	}

	ip, err := d.Orchestrator.InfoGetIPAddressByID(orchestrator.MachineID{
		Group: uint8(shell),
		Id:    uint32(id),
	})

	if err != nil {
		return "", errors.WithStack(err)
	}
	return ip.String(), nil
}

func (d *DNSServer) handleDnsRequest(w dns.ResponseWriter, r *dns.Msg) {
	m := new(dns.Msg)
	m.SetReply(r)
	m.Compress = false

	log.Debugf("DNS Query: %#v", *r)

	if r.Opcode != dns.OpcodeQuery {
		// unsupported opcode
		err := w.WriteMsg(m)
		if err != nil {
			log.Error(err.Error())
		}
		return
	}

	for _, q := range m.Question {
		if q.Qtype != dns.TypeA {
			// unsupported query type
			continue
		}

		ip, err := d.getIPFromDNS(q.Name)

		if err != nil {
			log.Debugf(err.Error())
		}

		if ip == "" {
			// no IP found
			log.Debugf("no IP found for %s", q.Name)
			continue
		}

		rr, err := dns.NewRR(fmt.Sprintf("%s A %s", q.Name, ip))
		if err != nil {
			log.Debugf(err.Error())
			continue
		}

		m.Answer = append(m.Answer, rr)

	}

	err := w.WriteMsg(m)

	if err != nil {
		log.Error(err.Error())
	}
}

// New creates a new DNS service. The service helps applications find out the IP addresses
// of other satellites. It uses the custom (made up) "celestial." TLD. A satellite DNS
// record has the form [ID].[SHELL].celestial, where [ID] is the identifier and [SHELL] is
// the index of the shell of the satellite. That maps to an IP address. Additionally,
// ground station IP addresses can be determined with [NAME].gst.celestial, where NAME is the
// ground station name.
// Our DNS server supports only queries, only UDP (no DNSSEC), and only A records.
// This service relies on configuring systemd-resolved to use our DNS server for the celestial
// TLD.
func New(o *orchestrator.Orchestrator) *DNSServer {
	return &DNSServer{
		Orchestrator: o,
	}
}

// Start starts our DNS service. We first check if systemd-resolved is available
// and panic otherwise. We then place  a configuration file in
// /etc/systemd/resolved.conf.d/celestial.conf that contains the following:
//
// ```conf
// [Resolve]
// DNS=127.0.0.1:[port]
// Domains=~celestial
// DNSStubListener=no
// DNSStubListenerExtra=0.0.0.0:53
// ```
//
// We then restart systemd-resolved.
func (d *DNSServer) Start(port uint64) error {
	// check if systemd-resolved is used
	cmd := exec.Command("systemctl", "is-active", "systemd-resolved")

	out, err := cmd.CombinedOutput()

	if err != nil {
		return errors.Errorf("systemd-resolved is not active: %s", string(out))
	}

	if string(out) != "active\n" {
		return errors.Errorf("systemd-resolved is not active: %s", string(out))
	}

	// check that systemd is version >= 247
	cmd = exec.Command("systemctl", "--version")

	out, err = cmd.CombinedOutput()

	if err != nil {
		return errors.Errorf("could not get systemd version: %s", string(out))
	}

	split := strings.SplitN(string(out), " ", 3)

	if len(split) < 2 {
		return errors.Errorf("could not get systemd version: %s", string(out))
	}

	version, err := strconv.Atoi(split[1])

	if err != nil {
		return errors.Errorf("could not get systemd version: %s", string(out))
	}

	if version < 247 {
		return errors.Errorf("systemd version is too old: %s. DNS server requires at least systemd 247", string(out))
	}

	// configure systemd-resolved
	// place a new config file in /etc/systemd/resolved.conf.d/celestial.conf
	err = os.Mkdir("/etc/systemd/resolved.conf.d", 0755)

	if err != nil && !os.IsExist(err) {
		return errors.WithStack(err)
	}

	f, err := os.Create("/etc/systemd/resolved.conf.d/celestial.conf")

	if err != nil {
		return errors.WithStack(err)
	}

	_, err = f.WriteString(fmt.Sprintf("[Resolve]\nDNS=127.0.0.1:%d\nDomains=~celestial\nDNSStubListener=no\nDNSStubListenerExtra=0.0.0.0:53", port))

	if err != nil {
		return errors.WithStack(err)
	}

	err = f.Close()

	if err != nil {
		return errors.WithStack(err)
	}

	// remove the file when we are done
	defer func() {

	}()

	// restart systemd-resolved
	cmd = exec.Command("systemctl", "restart", "systemd-resolved")

	out, err = cmd.CombinedOutput()

	if err != nil {
		return errors.Errorf("could not restart systemd-resolved: %s", string(out))
	}

	dns.HandleFunc("celestial.", d.handleDnsRequest)

	server := &dns.Server{Addr: net.JoinHostPort("", strconv.Itoa(int(port))), Net: "udp"}

	log.Printf("DNS server starting on :%d", port)

	err = server.ListenAndServe()

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return errors.WithStack(err)
}

// Stop stops our DNS service. We remove the configuration file we placed in
// /etc/systemd/resolved.conf.d/celestial.conf and restart systemd-resolved.
func (d *DNSServer) Stop() error {
	err := os.Remove("/etc/systemd/resolved.conf.d/celestial.conf")
	if err != nil {
		log.Errorf("could not remove /etc/systemd/resolved.conf.d/celestial.conf: %v", err)
		return err
	}

	cmd := exec.Command("systemctl", "restart", "systemd-resolved")

	out, err := cmd.CombinedOutput()

	if err != nil {
		return errors.Errorf("could not restart systemd-resolved: %s", string(out))
	}

	return nil
}
