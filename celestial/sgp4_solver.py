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
import math
import sgp4.api as sgp4

if not sgp4.accelerated:
    print(
        "\033[93m⚠️  SGP4 C++ API not available on your system, falling back to slower Python implementation...\033[0m"
    )
from .types import Model, SGP4ModelConfig, SGP4ParamsConfig


EARTH_RADIUS = 6371000

STD_GRAVITATIONAL_PARAMATER_EARTH = 3.986004418e14

# number of seconds per earth rotation (day)
SECONDS_PER_DAY = 86400


class SGP4Solver:
    def __init__(
        self,
        planes: int,
        sats: int,
        altitude: float,
        inclination: float,
        sgp4params: SGP4ParamsConfig,
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

        starttime = sgp4params.starttime
        self.start_jd, self.start_fr = sgp4.jday(
            starttime.year,
            starttime.month,
            starttime.day,
            starttime.hour,
            starttime.minute,
            starttime.second,
        )

        self.mode = sgp4params.mode.value
        self.bstar = sgp4params.bstar
        self.ndot = sgp4params.ndot
        self.argpo = sgp4params.argpo

        if sgp4params.model == SGP4ModelConfig.WGS72:
            self.model = sgp4.WGS72
        elif sgp4params.model == SGP4ModelConfig.WGS72OLD:
            self.model = sgp4.WGS72OLD
        elif sgp4params.model == SGP4ModelConfig.WGS84:
            self.model = sgp4.WGS84
        else:
            raise ValueError("Unknown SGP4 model")

    def init_sat_array(self, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        raan_offsets = [
            (self.arcOfAscendingNodes / self.number_of_planes) * i
            for i in range(0, self.number_of_planes)
        ]

        self.period = int(
            2.0
            * math.pi
            * math.sqrt(
                math.pow(self.semi_major_axis, 3) / STD_GRAVITATIONAL_PARAMATER_EARTH
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

        self.sgp4_solvers = [sgp4.Satrec()] * self.total_sats

        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):
                unique_id = (plane * self.nodes_per_plane) + node

                self.sgp4_solvers[unique_id] = sgp4.Satrec()

                self.sgp4_solvers[unique_id].sgp4init(
                    # whichconst=
                    self.model,  # gravity model
                    # opsmode=
                    self.mode,  # 'a' = old AFSPC mode, 'i' = improved mode
                    # satnum=
                    unique_id,  # satnum: Satellite number
                    # epoch=
                    self.start_jd
                    - 2433281.5,  # epoch: days since 1949 December 31 00:00 UT
                    # bstar=
                    self.bstar,  # bstar: drag coefficient (/earth radii)
                    # ndot=
                    self.ndot,  # ndot: ballistic coefficient (revs/day)
                    # nddot=
                    0.0,  # nddot: second derivative of mean motion (revs/day^3)
                    # ecco=
                    self.eccentricity,  # ecco: eccentricity
                    # argpo=
                    np.radians(
                        self.argpo
                    ),  # argpo: argument of perigee (radians) -> zero for circular orbits
                    # inclo=
                    np.radians(self.inclination),  # inclo: inclination (radians)
                    # mo=
                    np.radians(
                        (
                            node
                            + (
                                phase_offsets[plane]
                                * self.nodes_per_plane
                                / self.period
                            )
                        )
                        * (360.0 / self.nodes_per_plane)
                        + self.time_offsets[node] / self.period
                    ),  # mo: mean anomaly (radians) -> starts at 0 plus offset for the satellites
                    # no_kozai=
                    np.radians(360.0)
                    / (self.period / 60),  # no_kozai: mean motion (radians/minute)
                    # nodeo=
                    np.radians(
                        raan_offsets[plane]
                    ),  # nodeo: right ascension of ascending node (radians)
                )

                # calculate initial position
                e, r, d = self.sgp4_solvers[unique_id].sgp4(
                    self.start_jd, self.start_fr
                )

                # update satellties array

                satellites_array[unique_id]["x"] = np.int32(r[0]) * 1000
                satellites_array[unique_id]["y"] = np.int32(r[1]) * 1000
                satellites_array[unique_id]["z"] = np.int32(r[2]) * 1000

        return satellites_array

    def set_time(self, time: int, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        fr = self.start_fr + (time / SECONDS_PER_DAY)

        for sat_id in range(len(satellites_array)):
            e, r, d = self.sgp4_solvers[sat_id].sgp4(self.start_jd, fr)

            satellites_array[sat_id]["x"] = np.int32(r[0]) * 1000
            satellites_array[sat_id]["y"] = np.int32(r[1]) * 1000
            satellites_array[sat_id]["z"] = np.int32(r[2]) * 1000

        return satellites_array
