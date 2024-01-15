import cerberus
import typing
from enum import Enum


class GroundStationConnectionType(Enum):
    ALL = 0
    ONE = 1

    def int(self) -> int:
        return self.value


class MachineConfig:
    def __init__(
        self,
        vcpu_count: int,
        mem_size_mib: int,
        disk_size: int,
        kernel: str,
        rootfs: str,
        boot_parameters: typing.List[str],
    ):
        self.vcpu_count = vcpu_count
        self.mem_size_mib = mem_size_mib
        self.disk_size = disk_size
        self.kernel = kernel
        self.rootfs = rootfs
        self.boot_parameters = boot_parameters


class Shell:
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
        self.name = name
        self.lat = lat
        self.lng = lng
        self.gts_bandwidth_kbits = gts_bandwidth_kbits
        self.min_elevation = min_elevation
        self.connection_type = connection_type
        self.machine_config = machine_config


class BoundingBox:
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
                "name": {"type": "string", "empty": False, "required": True},
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
    def _check_with_max_satellites(
        self, field: str, value: typing.Dict[str, typing.Any]
    ) -> bool:
        if "planes" not in value or "sats" not in value:
            return False

        if value["planes"] * value["sats"] > 16384:
            self._error(field, "max. 16384 satellites allowed per shell")
            return False

        return True

    def _check_with_gst_name_unique(
        self, field: str, value: typing.List[typing.Dict[str, str]]
    ) -> None:
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

    def _validate_match_length(
        self, other: str, field: str, value: typing.List[str]
    ) -> None:
        "{'type': 'string'}"

        if len(value) != len(self.document[other]):
            self._error(
                field,
                "Length %d is not %d (length of field %s)"
                % (len(value), len(self.document[other]), other),
            )

    def _validate_allowed_max(
        self, other: str, field: str, value: typing.List[int]
    ) -> None:
        "{'type': 'string'}"

        for i in value:
            if i >= len(self.root_document[other]):
                self._error(field, "Host %d is not in %s" % (i, other))


def _validate_configuration(config: typing.MutableMapping[str, typing.Any]) -> None:
    v = CelestialValidator(CONFIG_SCHEMA)
    if not v.validate(config):
        raise ValueError(v.errors)


def _fill_configuration(
    config: typing.MutableMapping[str, typing.Any],
) -> typing.MutableMapping[str, typing.Any]:
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
    def __init__(
        self,
        text_config: typing.MutableMapping[str, typing.Any],
    ):
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
        return hash(
            (
                self.bbox,
                self.duration,
                self.resolution,
                tuple(self.shells),
                tuple(self.ground_stations),
            )
        )
