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

package infoserver

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

var o *orchestrator.Orchestrator

func getSelf(w http.ResponseWriter, r *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	src, _, err := net.SplitHostPort(r.RemoteAddr)

	if err != nil {
		log.Errorf("%s", err.Error())
		return
	}

	srcIP := net.ParseIP(src)

	if srcIP == nil {
		log.Errorf("could not determine source IP %s", src)
		w.WriteHeader(http.StatusBadRequest)
		_, err = fmt.Fprintf(w, "could not determine source IP %s", src)

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	m, err := o.GetMachineByIP(srcIP)

	if err != nil {
		log.Errorf("%s", err.Error())
		w.WriteHeader(http.StatusInternalServerError)
		_, err = fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	var resp []byte

	if m.Name == "" {
		s := struct {
			Type       string `json:"type"`
			ID         uint64 `json:"id"`
			Shell      int64  `json:"shell"`
			Active     bool   `json:"active"`
			Identifier string `json:"identifier"`
		}{
			Type:       "sat",
			ID:         m.ID,
			Shell:      m.Shell,
			Identifier: fmt.Sprintf("%d.%d.celestial", m.ID, m.Shell),
		}

		resp, err = json.Marshal(s)

	} else {
		s := struct {
			Type       string `json:"type"`
			ID         uint64 `json:"id"`
			Name       string `json:"name"`
			Identifier string `json:"identifier"`
		}{
			Type:       "gst",
			ID:         m.ID,
			Name:       m.Name,
			Identifier: fmt.Sprintf("%s.gst.celestial", m.Name),
		}

		resp, err = json.Marshal(s)
	}

	if err != nil {
		log.Errorf("%s", err.Error())
		w.WriteHeader(http.StatusInternalServerError)
		_, err = fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

}

func getInfo(w http.ResponseWriter, _ *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	err := o.DBGetConstellation(w)

	if err != nil {
		log.Errorf("error getting info about constelation: %s", err.Error())
		w.WriteHeader(http.StatusNotFound)
		_, err := fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}
}

func getShell(w http.ResponseWriter, r *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	v := mux.Vars(r)

	if _, ok := v["shell"]; !ok {
		log.Error("no shell given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no shell given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	shell, err := strconv.ParseUint(v["shell"], 10, 32)

	if err != nil {
		log.Errorf("could not parse shell %s", v["shell"])
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprintf(w, "could not parse shell %s", v["shell"])

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	err = o.DBGetShell(uint32(shell), w)

	if err != nil {
		log.Errorf("error getting info about shell %d %s", shell, err.Error())
		w.WriteHeader(http.StatusNotFound)
		_, err := fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}
}

func getSat(w http.ResponseWriter, r *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	v := mux.Vars(r)

	if _, ok := v["shell"]; !ok {
		log.Error("no shell given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no shell given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	shell, err := strconv.ParseUint(v["shell"], 10, 32)

	if err != nil {
		log.Errorf("could not parse shell %s", v["shell"])
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprintf(w, "could not parse shell %s", v["shell"])

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	if _, ok := v["sat"]; !ok {
		log.Error("no sat given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no sat given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	sat, err := strconv.ParseUint(v["sat"], 10, 32)

	if err != nil {
		log.Errorf("could not parse sat %s", v["sat"])
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprintf(w, "could not parse sat %s", v["sat"])

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	err = o.DBGetSatellite(uint32(shell), uint32(sat), w)

	if err != nil {
		log.Errorf("error getting info about satellite %d in shell %d: %s", sat, shell, err.Error())
		w.WriteHeader(http.StatusNotFound)
		_, err := fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}
}

func getGST(w http.ResponseWriter, r *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	v := mux.Vars(r)
	name, ok := v["name"]
	if !ok {
		log.Error("no name given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no name given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	err := o.DBGetGroundStation(name, w)

	if err != nil {
		log.Errorf("error getting info about ground station %s: %s", name, err.Error())
		w.WriteHeader(http.StatusNotFound)
		_, err := fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}
}

func getPath(w http.ResponseWriter, r *http.Request) {

	if r, _ := o.Ready(); !r {
		log.Error("host not ready yet")
		w.WriteHeader(http.StatusServiceUnavailable)
		_, err := fmt.Fprint(w, "host not ready yet")

		if err != nil {
			log.Errorf("%s", err.Error())
		}

		return
	}

	v := mux.Vars(r)

	sourceShell, ok := v["source_shell"]

	if !ok {
		log.Error("no source shell given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no source shell given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	sourceSat, ok := v["source_sat"]

	if !ok {
		log.Error("no source sat given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no source sat given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	targetShell, ok := v["target_shell"]

	if !ok {
		log.Error("no target shell given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no target shell given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	targetSat, ok := v["target_sat"]

	if !ok {
		log.Error("no target sat given")
		w.WriteHeader(http.StatusBadRequest)
		_, err := fmt.Fprint(w, "no target sat given")

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}

	var ss, ts int64
	var s, t uint64
	var err error

	if sourceShell == "gst" {
		s, err = o.GetGSTID(sourceSat)
		if err != nil {
			log.Errorf("could not find ground station %s", sourceSat)
			w.WriteHeader(http.StatusNotFound)
			_, err := fmt.Fprintf(w, "could not find ground station %s", sourceSat)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}

		ss = -1
	} else {
		s, err = strconv.ParseUint(sourceSat, 10, 32)
		if err != nil {
			log.Errorf("could not parse sat %s", sourceSat)
			w.WriteHeader(http.StatusBadRequest)
			_, err := fmt.Fprintf(w, "could not parse sat %s", sourceSat)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}

		ss, err = strconv.ParseInt(sourceShell, 10, 32)
		if err != nil {
			log.Errorf("could not parse shell %s", sourceShell)
			w.WriteHeader(http.StatusBadRequest)
			_, err := fmt.Fprintf(w, "could not parse shell %s", sourceShell)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}
	}

	if targetShell == "gst" {
		t, err = o.GetGSTID(targetSat)
		if err != nil {
			log.Errorf("could not find ground station %s", targetSat)
			w.WriteHeader(http.StatusNotFound)
			_, err := fmt.Fprintf(w, "could not find ground station %s", targetSat)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}

		ts = -1
	} else {
		t, err = strconv.ParseUint(targetSat, 10, 32)
		if err != nil {
			log.Errorf("could not parse sat %s", targetSat)
			w.WriteHeader(http.StatusBadRequest)
			_, err := fmt.Fprintf(w, "could not parse sat %s", targetSat)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}

		ts, err = strconv.ParseInt(targetShell, 10, 32)
		if err != nil {
			log.Errorf("could not parse shell %s", targetShell)
			w.WriteHeader(http.StatusBadRequest)
			_, err := fmt.Fprintf(w, "could not parse shell %s", targetShell)

			if err != nil {
				log.Errorf("%s", err.Error())
			}
			return
		}
	}

	err = o.DBGetPath(int32(ss), uint32(s), int32(ts), uint32(t), w)

	if err != nil {
		log.Errorf("error getting path from sat %d in shell %d to sat %d in shell %d: %s", s, ss, t, ts, err.Error())
		w.WriteHeader(http.StatusNotFound)
		_, err := fmt.Fprint(w, err.Error())

		if err != nil {
			log.Errorf("%s", err.Error())
		}
		return
	}
}

// Start starts our information server that provides information about
// the constellation.
func Start(port int, orch *orchestrator.Orchestrator) error {
	o = orch

	r := mux.NewRouter()

	log.Printf("Info server starting on %s", net.JoinHostPort("", strconv.Itoa(port)))

	r.HandleFunc("/self", getSelf).Methods("GET")
	r.HandleFunc("/info", getInfo).Methods("GET")
	r.HandleFunc("/shell/{shell:[0-9]+}", getShell).Methods("GET")
	r.HandleFunc("/shell/{shell:[0-9]+}/{sat:[0-9]+}", getSat).Methods("GET")
	r.HandleFunc("/gst/{name}", getGST).Methods("GET")
	r.HandleFunc("/path/{source_shell}/{source_sat}/{target_shell}/{target_sat}", getPath).Methods("GET")

	err := http.ListenAndServe(net.JoinHostPort("", strconv.Itoa(port)), r)

	if err != nil {
		log.Errorf("%s", err.Error())
	}

	return errors.WithStack(err)
}
