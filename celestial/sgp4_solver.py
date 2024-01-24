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

"""Solve satellite positions using SGP4"""

import datetime
import numpy as np
import math
import sgp4.api as sgp4

if not sgp4.accelerated:
    import warnings

    warnings.warn(
        "SGP4 C++ API not available on your system, falling back to slower Python implementation..."
    )

import celestial.types

### CONSTANTS ###
EARTH_RADIUS = 6371000
STD_GRAVITATIONAL_PARAMATER_EARTH = 3.986004418e14
SECONDS_PER_DAY = 86400
START_TIME = "2023-01-01T00:00:00+00:00"

SGP4_MODEL = sgp4.WGS72
SGP4_MODE = "i"
SGP4_BSTAR = 0.0
SGP4_NDOT = 0.0
SGP4_ARGPO = 0.0


class SGP4Solver:
    """
    Implements routines to solve satellite positions using SGP4.
    """

    def __init__(
        self,
        planes: int,
        sats: int,
        altitude_km: float,
        inclination: float,
        arc_of_ascending_nodes: float = 360.0,
        eccentricity: float = 0.0,
    ):
        """
        Initialize the SGP4 solver.

        :param planes: The number of planes in the constellation.
        :param sats: The number of satellites per plane.
        :param altitude_km: The altitude of the satellites in km.
        :param inclination: The inclination of the satellites in degrees.
        :param arc_of_ascending_nodes: The arc of ascending nodes in degrees.
        :param eccentricity: The eccentricity of the orbits.
        """
        # constellation options
        self.number_of_planes = planes
        self.nodes_per_plane = sats
        self.total_sats = planes * sats

        # orbit options
        self.eccentricity = eccentricity
        self.inclination = inclination
        self.arc_of_ascending_nodes = arc_of_ascending_nodes
        self.altitude_km = altitude_km
        self.semi_major_axis = float(self.altitude_km) * 1000 + EARTH_RADIUS

        starttime = datetime.datetime.fromisoformat(START_TIME)
        self.start_jd, self.start_fr = sgp4.jday(
            starttime.year,
            starttime.month,
            starttime.day,
            starttime.hour,
            starttime.minute,
            starttime.second,
        )

    def init_sat_array(self, satellites_array: np.ndarray) -> np.ndarray:  # type: ignore
        """
        Initialize the satellite array with the initial positions.

        :param satellites_array: The satellite array to initialize.
        :return: The initialized satellite array.
        """
        raan_offsets = [
            (self.arc_of_ascending_nodes / self.number_of_planes) * i
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

        self.sgp4_solvers = [sgp4.Satrec()] * self.total_sats

        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):
                unique_id = (plane * self.nodes_per_plane) + node

                self.sgp4_solvers[unique_id] = sgp4.Satrec()

                self.sgp4_solvers[unique_id].sgp4init(
                    # whichconst=
                    SGP4_MODEL,  # gravity model
                    # opsmode=
                    SGP4_MODE,  # 'a' = old AFSPC mode, 'i' = improved mode
                    # satnum=
                    unique_id,  # satnum: Satellite number
                    # epoch=
                    self.start_jd
                    - 2433281.5,  # epoch: days since 1949 December 31 00:00 UT
                    # bstar=
                    SGP4_BSTAR,  # bstar: drag coefficient (/earth radii)
                    # ndot=
                    SGP4_NDOT,  # ndot: ballistic coefficient (revs/day)
                    # nddot=
                    0.0,  # nddot: second derivative of mean motion (revs/day^3)
                    # ecco=
                    self.eccentricity,  # ecco: eccentricity
                    # argpo=
                    np.radians(
                        SGP4_ARGPO
                    ),  # argpo: argument of perigee (radians) -> zero for circular orbits
                    # inclo=
                    np.radians(self.inclination),  # inclo: inclination (radians)
                    # mo=
                    np.radians(
                        (node) * (360.0 / self.nodes_per_plane)
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

    def set_time(
        self,
        time: celestial.types.timestamp_s,
        satellites_array: np.ndarray,  # type: ignore
    ) -> np.ndarray:  # type: ignore
        """
        Calculate the satellite positions at a given time.

        :param time: The time in seconds since the start of the simulation.
        :param satellites_array: The satellite array to update.
        :return: The updated satellite array.
        """
        fr = self.start_fr + (time / SECONDS_PER_DAY)

        for sat_id in range(len(satellites_array)):
            e, r, d = self.sgp4_solvers[sat_id].sgp4(self.start_jd, fr)

            satellites_array[sat_id]["x"] = np.int32(r[0]) * 1000
            satellites_array[sat_id]["y"] = np.int32(r[1]) * 1000
            satellites_array[sat_id]["z"] = np.int32(r[2]) * 1000

        return satellites_array
