package dns

import (
	"fmt"
	"net"
	"strconv"

	"github.com/miekg/dns"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type dnsServer struct {
	*orchestrator.Orchestrator
}

// https://gist.github.com/walm/0d67b4fb2d5daf3edd4fad3e13b162cb

func (d *dnsServer) getIPFromDNS(qName string) (string, error) {
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

func (d *dnsServer) handleDnsRequest(w dns.ResponseWriter, r *dns.Msg) {
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

// Start starts our DNS service. The service helps applications find out the IP addresses
// of other satellites. It uses the custom (made up) "celestial." TLD. A satellite DNS
// record has the form [ID].[SHELL].celestial, where [ID] is the identifier and [SHELL] is
// the index of the shell of the satellite. That maps to an IP address. Additionally,
// ground station IP addresses can be determined with [NAME].gst.celestial, where NAME is the
// ground station name.
// Our DNS server supports only queries, only UDP (no DNSSEC), and only A records.
func Start(port uint64, orch *orchestrator.Orchestrator) error {
	d := &dnsServer{orch}

	dns.HandleFunc("celestial.", d.handleDnsRequest)

	server := &dns.Server{Addr: net.JoinHostPort("", strconv.Itoa(int(port))), Net: "udp"}

	log.Printf("DNS server starting on :%d", port)

	err := server.ListenAndServe()

	if err != nil {
		log.Errorf("%+v\n", err)
	}

	return errors.WithStack(err)
}
