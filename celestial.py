#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
This is the main entry point for a Celestial emulation run. It takes a
Celestial .zip file as an input and runs the emulation according to the
configuration in the .zip file.

Prerequisites
-------------

Make sure you have all the necessary dependencies installed. You can install
them using pip in a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

You should have generated a .zip file using satgen.py. A copy of the original
configuration file will be included in that .zip file to avoid drift between
generated network topologies and the original configuration.

Usage
-----

First, you will need to start at least one Celestial host that must be available
over the network from the machine you are running celestial.py on. You can start
a host using the following command:

    ./celestial.bin

Then, you can start the emulation run:

    python3 celestial.py [celestial.zip] [host1_addr] [host2_addr] ... [hostN_addr]

You can specify as many hosts as you want. The hosts will be assigned machines
in a round-robin fashion.

Note that the Celestial emulation run will only for as long as specified in the
`duration` field of the configuration file. If you want to stop the emulation
run before that, you can send a SIGTERM signal to celestial.py. It will then
stop the emulation run and exit gracefully, including on the hosts.
"""

import concurrent.futures
import signal
import sys
import time
import typing

import celestial.host
import celestial.types
import celestial.zip_serializer

DEBUG = True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit(
            "Usage: python3 celestial.py [celestial.zip] [host1_addr] [host2_addr] ... [hostN_addr]"
        )

    celestial_zip = sys.argv[1]

    serializer = celestial.zip_serializer.ZipDeserializer(celestial_zip)

    config = serializer.config()

    host_addrs = sys.argv[2:]
    hosts: typing.List[celestial.host.Host] = [
        celestial.host.Host(num=i, addr=host_addrs[i]) for i in range(len(host_addrs))
    ]

    # init the constellation
    # register the hosts
    with concurrent.futures.ThreadPoolExecutor() as e:
        for h in hosts:
            e.submit(h.register)

    inits = serializer.init_machines()

    machines: typing.Dict[
        int,
        typing.List[
            typing.Tuple[
                celestial.types.MachineID_dtype, celestial.config.MachineConfig
            ]
        ],
    ] = {h: [] for h in range(len(hosts))}
    count = 0

    for m_id, m_config in inits:
        # this is the logic that assigns machines to hosts
        # we just do a round robin assignment for now
        # this might be suboptimal, because it forces any neighbor
        # communication to go across the hosts
        # assinging by shells might be better
        m_host = count % len(hosts)

        machines[m_host].append((m_id, m_config))
        count += 1

    # init the hosts
    with concurrent.futures.ThreadPoolExecutor() as e:
        for h in hosts:
            e.submit(h.init, hosts, machines)

    def get_diff(
        t: celestial.types.timestamp_s,
    ) -> typing.Tuple[
        typing.List[
            typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
        ],
        typing.List[
            typing.Tuple[
                celestial.types.MachineID_dtype,
                celestial.types.MachineID_dtype,
                celestial.types.Link_dtype,
            ]
        ],
    ]:
        machine_diff = serializer.diff_machines(t)
        link_diff = serializer.diff_links(t)

        return (machine_diff, link_diff)

    # start the simulation
    timestep: celestial.types.timestamp_s = 0
    machine_diff, link_diff = get_diff(timestep)
    start_time = time.perf_counter()
    print("starting simulation")

    # install sigterm handler
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        while True:
            print(f"timestep: {timestep}")

            with concurrent.futures.ThreadPoolExecutor() as e:
                for h in hosts:
                    e.submit(h.update, machine_diff, link_diff)

            timestep += config.resolution

            if timestep > config.duration:
                break

            print(f"getting update for timestep {timestep}")
            machine_diff, link_diff = get_diff(timestep)

            print(f"waiting for {timestep -(time.perf_counter() - start_time)} seconds")
            while time.perf_counter() - start_time < timestep:
                time.sleep(0.001)

    finally:
        print("got keyboard interrupt, stopping...")
        for h in hosts:
            h.stop()
        print("finished")
