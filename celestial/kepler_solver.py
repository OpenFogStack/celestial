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

import numpy as np
from PyAstronomy import pyasl
import math

EARTH_RADIUS = 6371000

STD_GRAVITATIONAL_PARAMETER_EARTH = 3.986004418e14

# number of seconds per earth rotation (day)
SECONDS_PER_DAY = 86400


class KeplerSolver:
    def __init__(
        self,
        planes: int,
        sats: int,
        altitude: float,
        inclination: float,
        arcOfAscendingNodes: float = 360.0,
        eccentricity: float = 0.0,
    ):
        # constellation options
        self.number_of_planes = planes
        self.nodes_per_plane = sats
        self.total_sats = planes * sats

        # orbit options
        self.eccentricity = eccentricity
        self.inclination = inclination
        self.arcOfAscendingNodes = arcOfAscendingNodes
        self.altitude = altitude
        self.semi_major_axis = float(self.altitude) * 1000 + EARTH_RADIUS

    def init_sat_array(self, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        raan_offsets = [
            (self.arcOfAscendingNodes / self.number_of_planes) * i
            for i in range(0, self.number_of_planes)
        ]

        self.period = int(
            2.0
            * math.pi
            * math.sqrt(
                math.pow(self.semi_major_axis, 3) / STD_GRAVITATIONAL_PARAMETER_EARTH
            )
        )

        self.plane_solvers = []
        for raan in raan_offsets:
            self.plane_solvers.append(
                pyasl.KeplerEllipse(
                    per=self.period,
                    a=self.semi_major_axis,
                    e=self.eccentricity,
                    Omega=raan,
                    w=0.0,
                    i=self.inclination,
                )
            )

        self.time_offsets = [
            (self.period / self.nodes_per_plane) * i
            for i in range(0, self.nodes_per_plane)
        ]

        # we offset each plane by a small amount, so they do not 'collide'
        # this little algorithm comes up with a list of offset values
        phase_offset = 0.0
        phase_offset_increment = (
            self.period / self.nodes_per_plane
        ) / self.number_of_planes
        temp = []
        toggle = False
        # this loop results puts thing in an array in this order:
        # [...8,6,4,2,0,1,3,5,7...]
        # so that the offsets in adjacent planes are similar
        # basically do not want the max and min offset in two adjcent planes
        for i in range(self.number_of_planes):
            if toggle:
                temp.append(phase_offset)
            else:
                temp.insert(0, phase_offset)
                # temp.append(phase_offset)
            toggle = not toggle
            phase_offset = phase_offset + phase_offset_increment

        phase_offsets = temp

        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):
                unique_id = (plane * self.nodes_per_plane) + node

                offset = self.time_offsets[node] + phase_offsets[plane]

                init_pos = self.plane_solvers[plane].xyzPos(offset)

                satellites_array[unique_id]["time_offset"] = np.float32(offset)
                satellites_array[unique_id]["x"] = np.int32(init_pos[0])
                satellites_array[unique_id]["y"] = np.int32(init_pos[1])
                satellites_array[unique_id]["z"] = np.int32(init_pos[2])

        return satellites_array

    def set_time(self, time: int, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        for sat_id in range(len(satellites_array)):
            plane = satellites_array[sat_id]["plane_number"]
            offset = satellites_array[sat_id]["time_offset"]
            pos = self.plane_solvers[plane].xyzPos(time + offset)

            satellites_array[sat_id]["x"] = np.int32(pos[0])
            satellites_array[sat_id]["y"] = np.int32(pos[1])
            satellites_array[sat_id]["z"] = np.int32(pos[2])

        return satellites_array
