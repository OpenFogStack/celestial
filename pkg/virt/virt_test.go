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

package virt

import (
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	log "github.com/sirupsen/logrus"

	"github.com/OpenFogStack/celestial/pkg/ebpfem"
	"github.com/OpenFogStack/celestial/pkg/netem"
	"github.com/OpenFogStack/celestial/pkg/orchestrator"
)

const NET_IF = "ens4"

func TestMain(m *testing.M) {
	err := checkCommands()

	if err != nil {
		panic(err)
	}

	log.SetLevel(log.InfoLevel)

	m.Run()
}

func createNMachines(v *Virt, n int) error {
	// create the machines (but only the network part)

	progress := 0
	for i := 0; i < n; i++ {

		id := orchestrator.MachineID{
			Group: 1,
			Id:    uint32(i),
		}

		mNetwork, err := getNet(id)

		if err != nil {
			return err
		}

		m := &machine{
			network: mNetwork,
		}

		err = m.createNetwork()

		if err != nil {
			return err
		}

		err = v.neb.Register(id, m.network.tap)

		if err != nil {
			return err
		}

		v.machines[id] = m

		progress++
		if progress%100 == 0 {
			log.Infof("create progress: %d/%d", progress, n)
		}
	}

	return nil
}

func blockAllLinks(v *Virt) error {
	var wg sync.WaitGroup
	var e error
	progress := atomic.Uint32{}

	for id := range v.machines {
		wg.Add(1)
		go func(id orchestrator.MachineID) {
			defer wg.Done()

			for id2 := range v.machines {
				if id == id2 {
					continue
				}

				err := v.blocklink(id, id2)
				if err != nil {
					e = err
				}
				progress.Add(1)
			}
		}(id)
	}
	shown := 0
	total := len(v.machines) * (len(v.machines) - 1)
	for s := 0; s < total; s = int(progress.Load()) {
		if s > shown && s%100 == 0 {
			log.Infof("block progress: %d/%d", progress.Load(), total)
			shown = s
		}
		time.Sleep(100 * time.Millisecond)
	}

	wg.Wait()
	if e != nil {
		return e
	}

	return nil
}

func unblockAllLinks(v *Virt) error {
	var wg sync.WaitGroup
	var e error
	progress := atomic.Uint32{}

	for id := range v.machines {
		wg.Add(1)
		go func(id orchestrator.MachineID) {
			defer wg.Done()
			for id2 := range v.machines {
				if id == id2 {
					continue
				}

				err := v.unblocklink(id, id2)
				if err != nil {
					e = err
				}

				progress.Add(1)
			}
		}(id)
	}

	shown := 0
	total := len(v.machines) * (len(v.machines) - 1)
	for s := 0; s < total; s = int(progress.Load()) {
		if s > shown && s%100 == 0 {
			log.Infof("unblock progress: %d/%d", progress.Load(), total)
			shown = s
		}
		time.Sleep(100 * time.Millisecond)
	}
	wg.Wait()
	if e != nil {
		return e
	}

	return nil
}

func latencyAllLinks(v *Virt, latency uint32) error {
	var wg sync.WaitGroup
	var e error
	progress := atomic.Uint32{}

	for id := range v.machines {
		wg.Add(1)
		go func(id orchestrator.MachineID) {
			defer wg.Done()

			for id2 := range v.machines {
				if id == id2 {
					continue
				}

				err := v.setlatency(id, id2, latency)
				if err != nil {
					e = err
				}

				progress.Add(1)
			}
		}(id)
	}
	shown := 0
	total := len(v.machines) * (len(v.machines) - 1)
	for s := 0; s < total; s = int(progress.Load()) {
		if s > shown && s%100 == 0 {
			log.Infof("latency progress: %d/%d", progress.Load(), total)
			shown = s
		}
		time.Sleep(100 * time.Millisecond)
	}
	wg.Wait()
	if e != nil {
		return e
	}

	return nil
}

func removeAllLinks(v *Virt) error {
	var wg sync.WaitGroup
	var e error
	progress := atomic.Uint32{}

	for _, m := range v.machines {
		wg.Add(1)
		go func(m *machine) {
			defer wg.Done()
			defer progress.Add(1)

			err := m.removeNetwork()

			if err != nil {
				e = err
			}

		}(m)
	}
	shown := 0
	total := len(v.machines)
	for s := 0; s < total; s = int(progress.Load()) {
		if s > shown && s%100 == 0 {
			log.Infof("remove progress: %d/%d", progress.Load(), total)
			shown = s
		}
		time.Sleep(100 * time.Millisecond)
	}
	wg.Wait()
	if e != nil {
		return e
	}

	return nil
}

func runNebBenchmark(b *testing.B, backend string, num int) {
	var n NetworkEmulationBackend
	switch backend {
	case "netem":
		n = netem.New()
	case "ebpf":
		n = ebpfem.New()
	default:
		panic("unknown backend")
	}

	v, err := New(NET_IF, 0, nil, n)

	if err != nil {
		panic(err)
	}

	b.StartTimer()

	err = createNMachines(v, num)

	if err != nil {
		panic(err)
	}

	err = blockAllLinks(v)

	if err != nil {
		panic(err)
	}

	err = unblockAllLinks(v)

	if err != nil {
		panic(err)
	}

	err = latencyAllLinks(v, 100)

	if err != nil {
		panic(err)
	}

	b.StopTimer()

	err = v.neb.Stop()

	if err != nil {
		panic(err)
	}

	err = removeAllLinks(v)

	if err != nil {
		panic(err)
	}
}

func Benchmark(b *testing.B) {
	var benchmarks []struct {
		name    string
		backend string
		num     int
	}

	for _, num := range []int{1, 10, 100, 1000} { // 10000
		for _, backend := range []string{"ebpf", "netem"} {
			benchmarks = append(benchmarks, struct {
				name    string
				backend string
				num     int
			}{
				fmt.Sprintf("%s%d", backend, num),
				backend,
				num,
			})
		}
	}

	for _, bm := range benchmarks {
		b.Run(bm.name, func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				runNebBenchmark(b, bm.backend, bm.num)
			}

			//fmt.Println("number of iterations: ", b.N)
			//fmt.Println("elapsed:", b.Elapsed()/time.Duration(b.N))
		})
	}
}
