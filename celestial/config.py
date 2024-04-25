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

"""Celestial configuration format and validation"""

import cerberus
import typing
from enum import Enum


class GroundStationConnectionType(Enum):
    """
    Ground station connection type, can be to `ALL` (all satellites in reach)
    or `ONE` (one closest satellite per shell).
    """

    ALL = 0
    ONE = 1

    def int(self) -> int:
        """
        Get the integer representation of the connection type.

        :return: The integer representation of the connection type.
        """
        return self.value


class MachineConfig:
    """
    Configuration of a Firecracker VM.
    """

    def __init__(
        self,
        vcpu_count: int,
        mem_size_mib: int,
        disk_size: int,
        kernel: str,
        rootfs: str,
        boot_parameters: typing.List[str],
    ):
        """
        Configuration.

        :param vcpu_count: The number of vCPUs.
        :param mem_size_mib: The size of the memory in MiB.
        :param disk_size: The size of the disk in MiB.
        :param kernel: Host path to the kernel.
        :param rootfs: Host path to the rootfs.
        :param boot_parameters: The boot parameters to use.
        """
        self.vcpu_count = vcpu_count
        self.mem_size_mib = mem_size_mib
        self.disk_size = disk_size
        self.kernel = kernel
        self.rootfs = rootfs
        self.boot_parameters = boot_parameters


class Shell:
    """
    Shell configuration
    """

    def __init__(
        self,
        planes: int,
        sats: int,
        altitude_km: int,
        inclination: float,
        arc_of_ascending_nodes: float,
        eccentricity: float,
        isl_bandwidth_kbits: int,
        machine_config: MachineConfig,
    ):
        """
        Shell configuration.

        :param planes: The number of planes in the constellation.
        :param sats: The number of satellites per plane.
        :param altitude_km: The altitude of the satellites in km.
        :param inclination: The inclination of the satellites in degrees.
        :param arc_of_ascending_nodes: The arc of ascending nodes in degrees.
        :param eccentricity: The eccentricity of the orbits.
        :param isl_bandwidth_kbits: The bandwidth of the inter-satellite links in kbit/s.
        :param machine_config: The machine configuration to use for the satellites.
        """
        self.planes = planes
        self.sats = sats
        self.altitude_km = altitude_km
        self.inclination = inclination
        self.arc_of_ascending_nodes = arc_of_ascending_nodes
        self.eccentricity = eccentricity
        self.isl_bandwidth_kbits = isl_bandwidth_kbits

        self.machine_config = machine_config

        self.total_sats = planes * sats


class GroundStation:
    """
    Ground station configuration
    """

    def __init__(
        self,
        name: str,
        lat: float,
        lng: float,
        gts_bandwidth_kbits: int,
        min_elevation: float,
        connection_type: GroundStationConnectionType,
        machine_config: MachineConfig,
    ):
        """
        Ground station configuration.

        :param name: The name of the ground station.
        :param lat: The latitude of the ground station.
        :param lng: The longitude of the ground station.
        :param gts_bandwidth_kbits: The bandwidth of the ground station in kbit/s.
        :param min_elevation: The minimum elevation of the ground station in degrees.
        :param connection_type: The connection type of the ground station.
        :param machine_config: The machine configuration to use for the ground station.
        """

        self.name = name
        self.lat = lat
        self.lng = lng
        self.gts_bandwidth_kbits = gts_bandwidth_kbits
        self.min_elevation = min_elevation
        self.connection_type = connection_type
        self.machine_config = machine_config


class BoundingBox:
    """
    Bounding box of the simulation area.
    """

    def __init__(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ):
        """
        Bounding box.

        :param lat1: The latitude of the first point.
        :param lon1: The longitude of the first point.
        :param lat2: The latitude of the second point.
        :param lon2: The longitude of the second point.
        """

        self.lat1 = lat1
        self.lon1 = lon1
        self.lat2 = lat2
        self.lon2 = lon2


NETWORK_PARAMS_SCHEMA = {
    "bandwidth_kbits": {
        "type": "integer",
        "min": 0,
    },
    "min_elevation": {
        "type": "float",
        "min": 0,
    },
    "ground_station_connection_type": {
        "type": "string",
        "allowed": ["all", "one"],
    },
}

COMPUTE_PARAMS_SCHEMA = {
    "vcpu_count": {
        "type": "integer",
    },
    "mem_size_mib": {
        "type": "integer",
        "min": 1,
    },
    "disk_size_mib": {
        "type": "integer",
        "min": 1,
    },
    "kernel": {
        "type": "string",
        "empty": False,
    },
    "rootfs": {
        "type": "string",
        "empty": False,
    },
    "boot_parameters": {
        "type": "list",
        "schema": {"type": "string"},
        "required": False,
    },
}

LAT = {
    "type": "float",
    "min": -90.0,
    "max": 90.0,
    "required": True,
}

LON = {
    "type": "float",
    "min": -180.0,
    "max": 180.0,
    "required": True,
}

CONFIG_SCHEMA = {
    "bbox": {
        "type": "list",
        "items": [LAT, LON, LAT, LON],
        "required": True,
    },
    "resolution": {
        "type": "integer",
        "required": True,
        "min": 1e0,
        "max": 1e10,
    },
    "duration": {
        "type": "integer",
        "required": True,
        "min": 30e0,
        "max": 1e10,
    },
    "offset": {
        "type": "integer",
        "required": False,
        "min": 0,
    },
    "network_params": {
        "type": "dict",
        "schema": NETWORK_PARAMS_SCHEMA,
        "require_all": True,
        "required": True,
    },
    "compute_params": {
        "type": "dict",
        "schema": COMPUTE_PARAMS_SCHEMA,
        "require_all": True,
        "required": True,
    },
    "shell": {
        "type": "list",
        "empty": False,
        "minlength": 1,
        "maxlength": 245,
        "schema": {
            "type": "dict",
            "check_with": "max_satellites",
            "schema": {
                "planes": {"type": "integer", "min": 1, "required": True},
                "sats": {"type": "integer", "min": 1, "required": True},
                "altitude_km": {"type": "integer", "min": 0, "required": True},
                "inclination": {
                    "type": "float",
                    "min": 0.0,
                    "max": 360.0,
                    "required": True,
                },
                "arc_of_ascending_nodes": {"type": "float", "required": True},
                "eccentricity": {"type": "float", "required": True},
                "network_params": {"type": "dict", "schema": NETWORK_PARAMS_SCHEMA},
                "compute_params": {
                    "type": "dict",
                    "schema": COMPUTE_PARAMS_SCHEMA,
                },
            },
        },
    },
    "ground_station": {
        "type": "list",
        "check_with": "gst_name_unique",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "empty": False,
                    "required": True,
                    "regex": "^[a-zA-Z0-9-]+$",
                },
                "lat": LAT,
                "long": LON,
                "network_params": {"type": "dict", "schema": NETWORK_PARAMS_SCHEMA},
                "compute_params": {
                    "type": "dict",
                    "schema": COMPUTE_PARAMS_SCHEMA,
                },
            },
        },
    },
}


class CelestialValidator(cerberus.Validator):  # type: ignore
    """
    Validator for the Celestial configuration.
    """

    def _check_with_max_satellites(
        self, field: str, value: typing.Dict[str, typing.Any]
    ) -> bool:
        """Check that we have less than 16384 satellites per shell."""
        if "planes" not in value or "sats" not in value:
            return False

        if value["planes"] * value["sats"] > 16384:
            self._error(field, "max. 16384 satellites allowed per shell")
            return False

        return True

    def _check_with_gst_name_unique(
        self, field: str, value: typing.List[typing.Dict[str, str]]
    ) -> None:
        """Check that all ground station names are unique."""
        names: typing.Set[str] = set()
        without_names: typing.Set[str] = set()
        duplicates: typing.Set[str] = set()

        for gst in value:
            if "name" not in gst:
                without_names.add(gst["name"])
                continue
            if gst["name"] in names:
                duplicates.add(gst["name"])

            names.add(gst["name"])

        err = ""

        if len(without_names) > 0:
            err += "no names given for:"
            for name in without_names:
                err += " "
                err += name
            err += "\n"

        if len(duplicates) > 0:
            err += "duplicate names:"
            for name in duplicates:
                err += " "
                err += name
            err += "\n"

        if err != "":
            self._error(field, err)


def _validate_configuration(config: typing.MutableMapping[str, typing.Any]) -> None:
    """Validate the configuration."""
    v = CelestialValidator(CONFIG_SCHEMA)
    if not v.validate(config):
        raise ValueError(v.errors)


def _fill_configuration(
    config: typing.MutableMapping[str, typing.Any],
) -> typing.MutableMapping[str, typing.Any]:
    """Fill the configuration with default values."""

    if "offset" not in config:
        config["offset"] = 0

    if "boot_parameters" not in config["compute_params"]:
        config["compute_params"]["boot_parameters"] = []

    for shell in config["shell"]:
        network = {}

        if config["network_params"] is not None:
            for key, value in config["network_params"].items():
                network[key] = value

        if "network_params" in shell:
            for key, value in shell["network_params"].items():
                network[key] = value

        shell["network_params"] = network

    if "ground_station" not in config:
        config["ground_station"] = []

    for groundstation in config["ground_station"]:
        network = {}

        if config["network_params"] is not None:
            for key, value in config["network_params"].items():
                network[key] = value

        if "network_params" in groundstation:
            for key, value in groundstation["network_params"].items():
                network[key] = value

        groundstation["network_params"] = network

    for shell in config["shell"]:
        compute = {}

        if config["compute_params"] is not None:
            for key, value in config["compute_params"].items():
                compute[key] = value

        if "compute_params" in shell:
            for key, value in shell["compute_params"].items():
                compute[key] = value

        shell["compute_params"] = compute

    for groundstation in config["ground_station"]:
        compute = {}

        if config["compute_params"] is not None:
            for key, value in config["compute_params"].items():
                compute[key] = value

        if "compute_params" in groundstation:
            for key, value in groundstation["compute_params"].items():
                compute[key] = value

        groundstation["compute_params"] = compute

    return config


class Config:
    """
    Celestial configuration
    """

    def __init__(
        self,
        text_config: typing.MutableMapping[str, typing.Any],
    ):
        """
        Initialize the configuration from a text-based configuration

        :param text_config: The text-based configuration.
        """
        _validate_configuration(text_config)

        config = _fill_configuration(text_config)

        self.bbox = BoundingBox(
            lat1=config["bbox"][0],
            lon1=config["bbox"][1],
            lat2=config["bbox"][2],
            lon2=config["bbox"][3],
        )

        self.duration = config["duration"]
        self.resolution = config["resolution"]
        self.offset = config["offset"]

        self.shells = [
            Shell(
                planes=s["planes"],
                sats=s["sats"],
                altitude_km=s["altitude_km"],
                inclination=s["inclination"],
                arc_of_ascending_nodes=s["arc_of_ascending_nodes"],
                eccentricity=s["eccentricity"],
                isl_bandwidth_kbits=s["network_params"]["bandwidth_kbits"],
                machine_config=MachineConfig(
                    vcpu_count=s["compute_params"]["vcpu_count"],
                    mem_size_mib=s["compute_params"]["mem_size_mib"],
                    disk_size=s["compute_params"]["disk_size_mib"],
                    kernel=s["compute_params"]["kernel"],
                    rootfs=s["compute_params"]["rootfs"],
                    boot_parameters=s["compute_params"]["boot_parameters"],
                ),
            )
            for s in config["shell"]
        ]

        self.ground_stations = [
            GroundStation(
                name=g["name"],
                lat=g["lat"],
                lng=g["long"],
                gts_bandwidth_kbits=g["network_params"]["bandwidth_kbits"],
                min_elevation=g["network_params"]["min_elevation"],
                connection_type=GroundStationConnectionType.ALL
                if g["network_params"]["ground_station_connection_type"] == "all"
                else GroundStationConnectionType.ONE,
                machine_config=MachineConfig(
                    vcpu_count=g["compute_params"]["vcpu_count"],
                    mem_size_mib=g["compute_params"]["mem_size_mib"],
                    disk_size=g["compute_params"]["disk_size_mib"],
                    kernel=g["compute_params"]["kernel"],
                    rootfs=g["compute_params"]["rootfs"],
                    boot_parameters=g["compute_params"]["boot_parameters"],
                ),
            )
            for g in config["ground_station"]
        ]

    def __hash__(self) -> int:
        """
        Return a hash of the configuration.
        """
        return hash(
            (
                self.bbox,
                self.duration,
                self.resolution,
                tuple(self.shells),
                tuple(self.ground_stations),
            )
        )
