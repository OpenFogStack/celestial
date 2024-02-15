#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Ben S. Kempton, Tobias Pfandzelter, The OpenFogStack Team.
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
A constellation of satellite shells that takes updates and sends them to
the serializer
"""

import typing

import celestial.serializer
import celestial.config
import celestial.types
import celestial.shell

DELAY_UPDATE_THRESHOLD_US = 500


class SatgenConstellation:
    """
    A constellation of satellite shells that takes updates and sends them to
    the serializer
    """

    def __init__(
        self,
        config: celestial.config.Config,
        writer: celestial.serializer.Serializer,
    ):
        """
        Initialize the constellation.

        :param config: The configuration of the constellation.
        :param writer: The serializer to use for writing updates.
        """
        self.current_time = 0
        self.shells: typing.List[celestial.shell.Shell] = []
        self.ground_stations: typing.List[celestial.types.MachineID_dtype] = []

        self.writer = writer

        self.start_time: celestial.types.timestamp_s = 0

        for i, sc in enumerate(config.shells):
            s = celestial.shell.Shell(
                shell_identifier=i + 1,
                planes=sc.planes,
                sats=sc.sats,
                altitude_km=sc.altitude_km,
                inclination=sc.inclination,
                arc_of_ascending_nodes=sc.arc_of_ascending_nodes,
                eccentricity=sc.eccentricity,
                isl_bandwidth_kbits=sc.isl_bandwidth_kbits,
                bbox=config.bbox,
                ground_stations=config.ground_stations,
            )

            self.shells.append(s)

        self.nodes: typing.List[celestial.types.MachineID_dtype] = []

        self.node_configs: typing.Dict[
            celestial.types.MachineID_dtype, celestial.config.MachineConfig
        ] = {}

        self.node_infos: typing.Dict[
            celestial.types.MachineID_dtype, celestial.types.MachineInfo
        ] = {}

        self.ground_stations_initialized = False

        for i, g in enumerate(config.ground_stations):
            gst = celestial.types.MachineID(
                group=0,
                id=i,
                name=g.name,
            )

            self.nodes.append(gst)
            self.node_configs[gst] = g.machine_config
            self.node_infos[gst] = celestial.types.MachineInfo(
                name=g.name,
                location=[g.lat, g.long],
            )
            self.ground_stations.append(gst)

        for i, sc in enumerate(config.shells):
            for j in range(sc.total_sats):
                m_id = celestial.types.MachineID(
                    group=1 + i,
                    id=j,
                )

                self.nodes.append(m_id)
                self.node_configs[m_id] = sc.machine_config
                self.node_infos[m_id] = celestial.types.MachineInfo(tle=sc.get_tle(j))

        self.machines_state = {m: celestial.types.VMState.STOPPED for m in self.nodes}

        self.links_state = {
            m1: {
                m2: celestial.types.Link(
                    latency_us=0,
                    bandwidth_kbits=0,
                    blocked=True,
                    next_hop=m1,
                    prev_hop=m2,
                )
                for m2 in self.nodes
                if m1 != m2
            }
            for m1 in self.nodes
        }

        for machine in self.nodes:
            self.writer.init_machine(
                machine, self.node_configs[machine], self.node_infos[machine]
            )

        for gst in self.ground_stations:
            self.machines_state[gst] = celestial.types.VMState.ACTIVE

            self.writer.diff_machine(
                0,  # starting time stamp 0
                gst,
                celestial.types.VMState.ACTIVE,
            )

    def step(self, t: celestial.types.timestamp_s) -> None:
        """
        Step the constellation forward in time to a given timestamp.

        :param t: The timestamp to step to.
        """
        self.current_time = t

        for s in self.shells:
            s.step(
                self.current_time,
                calculate_diffs=True,
                delay_update_threshold_us=DELAY_UPDATE_THRESHOLD_US,
            )

        for s in self.shells:
            for machine, state in s.get_sat_node_diffs().items():
                self.writer.diff_machine(self.current_time, machine, state)

            for source, links in s.get_link_diff().items():
                for target, link in links.items():
                    self.writer.diff_link(self.current_time, source, target, link)
