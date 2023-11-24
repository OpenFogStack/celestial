#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Ben S. Kempton, Tobias Pfandzelter, The OpenFogStack Team.
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

import threading as td
import time
import typing
import numpy as np

import satgen.config
import satgen.types
import satgen.shell


class Constellation:
    def __init__(
        self,
        config: satgen.config.Config,
    ):
        self.shells: typing.List[satgen.shell.Shell] = []

        self.start_time: satgen.types.timestep = 0

        for i, sc in enumerate(config.shells):
            s = satgen.shell.Shell(
                shell_identifier=i + 1,
                planes=sc.planes,
                sats=sc.sats,
                altitude=sc.altitude,
                inclination=sc.inclination,
                arc_of_ascending_nodes=sc.arc_of_ascending_nodes,
                eccentricity=sc.eccentricity,
                isl_bandwidth=sc.isl_bandwidth,
                bbox=config.bbox,
                ground_stations=config.ground_stations,
            )

            self.shells.append(s)

        self.nodes: typing.Dict[
            satgen.types.MachineID, satgen.config.MachineConfig
        ] = {}

        for i, g in enumerate(config.ground_stations):
            self.nodes[
                satgen.types.MachineID(
                    group=0,
                    id=i,
                    name=g.name,
                )
            ] = g.machine_config

        for i, sc in enumerate(config.shells):
            for j in range(s.total_sats):
                self.nodes[
                    satgen.types.MachineID(
                        group=1 + i,
                        id=j,
                    )
                ] = sc.machine_config

    def get_machines(
        self
    ) -> typing.Dict[satgen.types.MachineID, satgen.config.MachineConfig]:
        return self.nodes

    def step(self, to: satgen.types.timestep) -> satgen.types.State:
        for s in self.shells:
            s.step(to)

        machines: satgen.types.MachineState = {}

        for i, s in enumerate(self.shells):
            for sat, state in s.get_sat_nodes().items():
                machines[sat] = state

        links: satgen.types.LinkState = {}

        for i, s in enumerate(self.shells):
            for s1, s1_links in s.get_sat_links().items():
                if s1 not in links:
                    links[s1] = {}

                for s2, link in s1_links.items():
                    links[s1][s2] = link

            for g1, g1_links in s.get_gst_links().items():
                if g1 not in links:
                    links[g1] = {}

                for s2, link in g1_links.items():
                    links[s1][s2] = link

        return satgen.types.State(
            machines_state=machines,
            links_state=links,
        )
