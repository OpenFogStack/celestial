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

package info

import (
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

type infoserver struct {
	*orchestrator.Orchestrator
}

func errRes(w http.ResponseWriter, code int, err error) {
	log.Errorf("%s", err.Error())
	http.Error(w, err.Error(), code)
}

func write(w http.ResponseWriter, res []byte) {
	_, err := w.Write(res)

	if err != nil {
		log.Errorf("%s", err.Error())
	}
}

func (i *infoserver) getSelf(w http.ResponseWriter, r *http.Request) {
	src, _, err := net.SplitHostPort(r.RemoteAddr)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not determine source IP"))
		return
	}

	srcIP := net.ParseIP(src)

	if srcIP == nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not determine source IP"))
		return
	}

	m, err := i.Orchestrator.InfoGetNodeByIP(srcIP)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not determine source IP"))
		return
	}

	var s interface{}

	if m.Name != "" {
		s = &GroundStation{
			Identifier: Identifier{
				Shell: m.ID.Group,
				ID:    m.ID.Id,
			},
			Name: m.Name,
			Lat:  m.Lat,
			Lon:  m.Lon,
		}
	} else {
		s = &Sat{
			Identifier: Identifier{
				Shell: m.ID.Group,
				ID:    m.ID.Id,
			},
			Active: m.Active,
			TLE1:   m.TLE1,
			TLE2:   m.TLE2,
		}
	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

func (i *infoserver) getInfo(w http.ResponseWriter, r *http.Request) {
	c, err := i.Orchestrator.InfoGetConstellation()

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	s := Constellation{
		Shells: make([]Shell, len(c.Groups)-1),
	}

	for _, g := range c.Groups {
		if g.Group == 0 {
			s.GroundStations = make([]GroundStation, len(g.Nodes))
			for j, n := range g.Nodes {
				s.GroundStations[j] = GroundStation{
					Identifier: Identifier{
						Shell: n.ID.Group,
						ID:    n.ID.Id,
					},
					Name: n.Name,
					Lat:  n.Lat,
					Lon:  n.Lon,
				}
			}
			continue
		}

		s.Shells[g.Group-1] = Shell{
			Sats: make([]Sat, len(g.Nodes)),
		}

		for _, n := range g.Nodes {

			s.Shells[g.Group-1].Sats[n.ID.Id] = Sat{
				Identifier: Identifier{
					Shell: n.ID.Group,
					ID:    n.ID.Id,
				},
				Active: n.Active,
				TLE1:   n.TLE1,
				TLE2:   n.TLE2,
			}
		}

	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

func (i *infoserver) getShell(w http.ResponseWriter, r *http.Request) {
	v := mux.Vars(r)

	if _, ok := v["shell"]; !ok || v["shell"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("shell not specified"))
		return
	}

	shell, err := strconv.ParseUint(v["shell"], 10, 32)

	if err != nil {
		errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse shell"))
		return
	}

	g, err := i.Orchestrator.InfoGetGroup(uint8(shell))

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	s := Shell{
		Sats: make([]Sat, 0, len(g.Nodes)),
	}

	for _, n := range g.Nodes {
		s.Sats = append(s.Sats, Sat{
			Identifier: Identifier{
				Shell: n.ID.Group,
				ID:    n.ID.Id,
			},
			Active: n.Active,
			TLE1:   n.TLE1,
			TLE2:   n.TLE2,
		})
	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

func (i *infoserver) getSat(w http.ResponseWriter, r *http.Request) {
	v := mux.Vars(r)

	if _, ok := v["shell"]; !ok || v["shell"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("shell not specified"))
		return
	}

	if _, ok := v["sat"]; !ok || v["sat"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("sat not specified"))
		return
	}

	shell, err := strconv.ParseUint(v["shell"], 10, 32)

	if err != nil {
		errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse shell"))
		return
	}

	sat, err := strconv.ParseUint(v["sat"], 10, 32)

	if err != nil {
		errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse sat"))
		return
	}

	n, err := i.Orchestrator.InfoGetNodeByID(orchestrator.MachineID{
		Group: uint8(shell),
		Id:    uint32(sat),
	})

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not get node by id"))
		return
	}

	s := Sat{
		Identifier: Identifier{
			Shell: n.ID.Group,
			ID:    n.ID.Id,
		},
		Active: n.Active,
		TLE1:   n.TLE1,
		TLE2:   n.TLE2,
	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

func (i *infoserver) getGST(w http.ResponseWriter, r *http.Request) {
	v := mux.Vars(r)

	if _, ok := v["name"]; !ok || v["name"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("name not specified"))
		return
	}

	g, err := i.Orchestrator.InfoGetNodeByName(v["name"])

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	s := GroundStation{
		Identifier: Identifier{
			Shell: g.ID.Group,
			ID:    g.ID.Id,
		},
		Name: g.Name,
		Lat:  g.Lat,
		Lon:  g.Lon,
	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

func (i *infoserver) getPath(w http.ResponseWriter, r *http.Request) {
	v := mux.Vars(r)

	if _, ok := v["source_shell"]; !ok || v["source_shell"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("source_shell not specified"))
		return
	}

	if _, ok := v["source_sat"]; !ok || v["source_sat"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("source_sat not specified"))
		return
	}

	if _, ok := v["target_shell"]; !ok || v["target_shell"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("target_shell not specified"))
		return
	}

	if _, ok := v["target_sat"]; !ok || v["target_sat"] == "" {
		errRes(w, http.StatusBadRequest, errors.New("target_sat not specified"))
		return
	}

	var source orchestrator.MachineID

	if v["source_shell"] == "gst" {
		n, err := i.Orchestrator.InfoGetNodeByName(v["source_sat"])
		if err != nil {
			errRes(w, http.StatusNotFound, errors.Wrap(err, "could not find gst node"))
			return
		}
		source = orchestrator.MachineID{
			Group: n.ID.Group,
			Id:    n.ID.Id,
		}
	} else {
		sourceShell, err := strconv.ParseUint(v["source_shell"], 10, 32)

		if err != nil {
			errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse source_shell"))
			return
		}

		sourceSat, err := strconv.ParseUint(v["source_sat"], 10, 32)

		if err != nil {
			errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse source_sat"))
			return
		}

		source = orchestrator.MachineID{
			Group: uint8(sourceShell),
			Id:    uint32(sourceSat),
		}
	}

	var target orchestrator.MachineID

	if v["target_shell"] == "gst" {
		n, err := i.Orchestrator.InfoGetNodeByName(v["target_sat"])
		if err != nil {
			errRes(w, http.StatusNotFound, errors.Wrap(err, "could not find gst node"))
			return
		}
		target = orchestrator.MachineID{
			Group: n.ID.Group,
			Id:    n.ID.Id,
		}
	} else {
		targetShell, err := strconv.ParseUint(v["target_shell"], 10, 32)

		if err != nil {
			errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse source_shell"))
			return
		}

		targetSat, err := strconv.ParseUint(v["target_sat"], 10, 32)

		if err != nil {
			errRes(w, http.StatusBadRequest, errors.Wrap(err, "could not parse source_sat"))
			return
		}

		target = orchestrator.MachineID{
			Group: uint8(targetShell),
			Id:    uint32(targetSat),
		}
	}
	p, err := i.Orchestrator.InfoGetPath(source, target)

	if err != nil {
		errRes(
			w,
			http.StatusInternalServerError,
			errors.Wrap(
				err,
				fmt.Sprintf("could not find path between %s and %s", source, target),
			),
		)
		return
	}

	s := Path{
		Source: Identifier{
			Shell: p.Source.Group,
			ID:    p.Source.Id,
		},
		Target: Identifier{
			Shell: p.Target.Group,
			ID:    p.Target.Id,
		},
	}

	if !p.Blocked {
		s.Delay = p.Latency
		s.Bandwidth = p.Bandwidth
		s.Segments = make([]Segment, len(p.Segments))

		for j, seg := range p.Segments {
			s.Segments[j] = Segment{
				Source: Identifier{
					Shell: seg.Source.Group,
					ID:    seg.Source.Id,
				},
				Target: Identifier{
					Shell: seg.Target.Group,
					ID:    seg.Target.Id,
				},
				Delay:     seg.Latency,
				Bandwidth: seg.Bandwidth,
			}
		}
	} else {
		s.Blocked = true
	}

	resp, err := json.Marshal(s)

	if err != nil {
		errRes(w, http.StatusInternalServerError, errors.Wrap(err, "could not marshal response"))
		return
	}

	write(w, resp)
}

// Start starts our information server that provides information about
// the constellation.
func Start(port uint64, o *orchestrator.Orchestrator) error {
	i := &infoserver{
		o,
	}

	r := mux.NewRouter()

	log.Printf("Info server starting on :%d", port)

	r.HandleFunc("/self", i.getSelf).Methods("GET")
	r.HandleFunc("/info", i.getInfo).Methods("GET")
	r.HandleFunc("/shell/{shell:[1-9][0-9]*}", i.getShell).Methods("GET")
	r.HandleFunc("/shell/{shell:[1-9][0-9]*}/{sat:[0-9]+}", i.getSat).Methods("GET")
	r.HandleFunc("/gst/{name}", i.getGST).Methods("GET")
	r.HandleFunc("/path/{source_shell}/{source_sat}/{target_shell}/{target_sat}", i.getPath).Methods("GET")

	err := http.ListenAndServe(net.JoinHostPort("", strconv.Itoa(int(port))), r)

	if err != nil {
		log.Errorf("%s", err.Error())
	}

	return errors.WithStack(err)
}
