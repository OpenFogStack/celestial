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

import logging
import sys
import time
import typing

import celestial.host
import celestial.types
import celestial.zip_serializer

DEBUG = True
DEFAULT_PORT = 1969

if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit(
            "Usage: python3 celestial.py [celestial.zip] [host1_addr] [host2_addr] ... [hostN_addr]"
        )

    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    celestial_zip = sys.argv[1]

    serializer = celestial.zip_serializer.ZipDeserializer(celestial_zip)

    config = serializer.config()

    host_addrs = sys.argv[2:]

    for i in range(len(host_addrs)):
        if ":" not in host_addrs[i]:
            host_addrs[i] = f"{host_addrs[i]}:{DEFAULT_PORT}"

    hosts: typing.List[celestial.host.Host] = [
        celestial.host.Host(num=i, addr=host_addrs[i]) for i in range(len(host_addrs))
    ]

    # init the constellation
    # register the hosts
    logging.info("Registering hosts...")
    # with concurrent.futures.ThreadPoolExecutor() as e:
    # for h in hosts:
    # e.submit(h.register)
    logging.info("Hosts registered!")

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
    logging.info("Initializing hosts...")
    # init_request = celestial.host.make_init_request(hosts, machines)
    # with concurrent.futures.ThreadPoolExecutor() as e:
    # for h in hosts:
    # e.submit(h.init, args=(init_request,))
    logging.info("Hosts initialized!")

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
    logging.info("Starting emulation...")

    # install sigterm handler
    # signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    update_request = celestial.host.make_update_request(machine_diff, link_diff)

    with open("test.bin", "wb") as f:
        f.write(update_request.SerializeToString())
