#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
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
import typing
import datetime
from enum import Enum
import numpy as np


class Model(Enum):
    SGP4 = "SGP4"
    Kepler = "Kepler"


class GroundstationConnectionTypeConfig(Enum):
    All = "all"
    One = "one"
    Shortest = "shortest"


class NetworkParamsConfig:
    def __init__(
        self,
        islpropagation: float,
        bandwidth: int,
        mincommsaltitude: int,
        minelevation: float,
        gstpropagation: float,
        groundstationconnectiontype: GroundstationConnectionTypeConfig,
    ):
        self.islpropagation = islpropagation
        self.bandwidth = bandwidth
        self.mincommsaltitude = mincommsaltitude
        self.minelevation = minelevation
        self.gstpropagation = gstpropagation
        self.groundstationconnectiontype = groundstationconnectiontype


class ComputeParamsConfig:
    def __init__(
        self,
        vcpu_count: int,
        mem_size_mib: int,
        ht_enabled: bool,
        disk_size_mib: int,
        kernel: str,
        rootfs: str,
        bootparams: str,
        hostaffinity: typing.List[int],
    ):
        self.vcpu_count = vcpu_count
        self.mem_size_mib = mem_size_mib
        self.ht_enabled = ht_enabled
        self.disk_size_mib = disk_size_mib
        self.kernel = kernel
        self.rootfs = rootfs
        self.bootparams = bootparams
        self.hostaffinity = hostaffinity


class SGP4ModelConfig(Enum):
    WGS72 = "WGS72"
    WGS72OLD = "WGS72OLD"
    WGS84 = "WGS84"


class SGP4ModeConfig(Enum):
    i = "i"
    a = "a"


class SGP4ParamsConfig:
    def __init__(
        self,
        starttime: datetime.datetime,
        model: SGP4ModelConfig,
        mode: SGP4ModeConfig,
        bstar: float,
        ndot: float,
        argpo: float,
    ):
        self.starttime = starttime
        self.model = model
        self.mode = mode
        self.bstar = bstar
        self.ndot = ndot
        self.argpo = argpo


class ShellConfig:
    def __init__(
        self,
        planes: int,
        sats: int,
        altitude: int,
        inclination: float,
        arcofascendingnodes: float,
        eccentricity: float,
        networkparams: NetworkParamsConfig,
        computeparams: ComputeParamsConfig,
        sgp4params: typing.Optional[SGP4ParamsConfig],
    ):
        self.planes = planes
        self.sats = sats
        self.altitude = altitude
        self.inclination = inclination
        self.arcofascendingnodes = arcofascendingnodes
        self.eccentricity = eccentricity
        self.networkparams = networkparams
        self.computeparams = computeparams

        if sgp4params is not None:
            self.sgp4params = sgp4params

        self.total_sats = planes * sats


class GroundstationConfig:
    def __init__(
        self,
        name: str,
        lat: float,
        lng: float,
        networkparams: NetworkParamsConfig,
        computeparams: ComputeParamsConfig,
    ):
        self.name = name
        self.lat = lat
        self.lng = lng
        self.networkparams = networkparams
        self.computeparams = computeparams


class BoundingBoxConfig:
    def __init__(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ):
        self.lat1 = lat1
        self.lon1 = lon1
        self.lat2 = lat2
        self.lon2 = lon2


class Configuration:
    def __init__(
        self,
        model: Model,
        bbox: BoundingBoxConfig,
        interval: int,
        animation: bool,
        hosts: typing.List[str],
        peeringhosts: typing.List[str],
        database: bool,
        dbhost: typing.Optional[str],
        shells: typing.List[ShellConfig],
        groundstations: typing.List[GroundstationConfig],
    ):
        self.model = model
        self.bbox = bbox
        self.interval = interval
        self.animation = animation
        self.hosts = hosts
        self.peeringhosts = peeringhosts
        self.database = database
        self.dbhost = dbhost
        self.shells = shells
        self.groundstations = groundstations


class Segment:
    def __init__(
        self,
        node_1: int,
        node_1_is_gst: bool,
        node_2: int,
        node_2_is_gst: bool,
        distance: float,
        delay: float,
        bandwidth: int,
    ):
        self.node_1 = node_1
        self.node_1_is_gst = node_1_is_gst
        self.node_2 = node_2
        self.node_2_is_gst = node_2_is_gst
        self.distance = distance
        self.delay = delay
        self.bandwidth = bandwidth


class Path(object):
    def __init__(
        self,
        node_1: int,
        node_1_is_gst: bool,
        node_2: int,
        node_2_is_gst: bool,
        distance: float,
        delay: float,
        bandwidth: int,
        segments: typing.Optional[typing.Iterable[Segment]] = None,
        dist_matrix: typing.Optional[np.ndarray] = None,  # type: ignore
        predecessors: typing.Optional[np.ndarray] = None,  # type: ignore
        islpropagation: typing.Optional[float] = None,
        total_sats: typing.Optional[int] = None,
    ):
        self.node_1 = node_1
        self.node_1_is_gst = node_1_is_gst
        self.node_2 = node_2
        self.node_2_is_gst = node_2_is_gst
        self.distance = distance
        self.delay = delay
        self.bandwidth = bandwidth
        if segments is not None:
            self.segments = segments
        elif (
            dist_matrix is not None
            and predecessors is not None
            and islpropagation is not None
            and total_sats is not None
        ):
            self.__dist_matrix = dist_matrix
            self.__predecessors = predecessors
            self.__islpropagation = islpropagation
            self.__total_sats = total_sats
        else:
            raise ValueError(
                "Either segments or dist_matrix and predecessors must be set"
            )

    def __make_segments(self) -> typing.List[typing.Tuple[int, int, int, float]]:
        # find the shortest path segments from the predecessor matrix
        node_1 = (
            self.node_1 if not self.node_1_is_gst else self.node_1 + self.__total_sats
        )
        node_2 = (
            self.node_2 if not self.node_2_is_gst else self.node_2 + self.__total_sats
        )
        a = node_1
        b = node_1
        sp: typing.List[typing.Tuple[int, int, int, float]] = []
        # print("getting shortest segment from %d to %d" % (node_1, node_2))

        while a != node_2:
            b = self.__predecessors[node_2, a]
            # print("going from %d to %d", a, b)
            if b == -9999:
                break
            sp.append(
                (
                    a,
                    b,
                    self.__dist_matrix[a, b],
                    self.__dist_matrix[a, b] * self.__islpropagation,
                )
            )
            a = b

        if b == -9999:
            return []

        return sp

    def __getattribute__(self, name: str) -> typing.Any:
        if name == "segments":
            if not "segments" in self.__dict__:
                self.segments = [
                    Segment(
                        node_1=s[0]
                        if s[0] < self.__total_sats
                        else s[0] - self.__total_sats,
                        node_1_is_gst=s[0] >= self.__total_sats,
                        node_2=s[1]
                        if s[1] < self.__total_sats
                        else s[1] - self.__total_sats,
                        node_2_is_gst=s[1] >= self.__total_sats,
                        distance=s[2],
                        bandwidth=self.bandwidth,
                        delay=s[3],
                    )
                    for s in self.__make_segments()
                ]
        return object.__getattribute__(self, name)
