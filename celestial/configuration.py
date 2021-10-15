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

import cerberus
import typing
import datetime

from .types import Configuration, Model, GroundstationConnectionTypeConfig, NetworkParamsConfig, ComputeParamsConfig, SGP4ModelConfig, SGP4ModeConfig, SGP4ParamsConfig, ShellConfig, GroundstationConfig, BoundingBoxConfig

NETWORKPARAMS_SCHEMA = {
    "islpropagation": {
        "type": "float",
        "min": 0.0,
    },
    "bandwidth": {
        "type": "integer",
        "min": 0,
    },
    "mincommsaltitude": {
        "type": "integer",
        "min": 0,
    },
    "minelevation": {
        "type": "integer",
        "min": 0,
    },
    "gstpropagation": {
        "type": "float",
        "min": 0.0,
    },
    "groundstationconnectiontype": {
        "type": "string",
        "allowed": ["all", "one", "shortest"],
    },
}

COMPUTEPARAMS_SCHEMA = {
    "vcpu_count": {
        "type": "integer",
        "min": 1,
    },
    "mem_size_mib": {
        "type": "integer",
        "min": 1,
    },
    "ht_enabled": {
        "type": "boolean",
    },
    "kernel": {
        "type": "string",
        "empty": False,
    },
    "rootfs": {
        "type": "string",
        "empty": False,
    },
    "bootparams": {
        "type": "string",
        "required": False,
    },
    "hostaffinity": {
        "type": "list",
        "schema": {
            "type": "integer",
        },
        "minlength": 1,
        "allowed_max": "hosts",
        "required": False,
    },
}

SGP4PARAMS_SCHEMA = {
    "starttime": {
        "type": "datetime",
    },
    "model": {
        "type": "string",
        "allowed": ["WGS72", "WGS72OLD", "WGS84"],
    },
    "mode": {
        "type": "string",
        "allowed": ["i", "a"],
    },
    "bstar": {
        "type": "float",
    },
    "ndot": {
        "type": "float",
    },
    "argpo": {
        "type": "float",
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
    "model": {
        "type": "string",
        "allowed": ["SGP4", "Kepler"],
        "required": True,
    },
    "bbox": {
        "type": "list",
        "items": [LAT, LON, LAT, LON],
        "required": True,
    },
    "interval": {
        "type": "integer",
        "required": True,
        "min": 1e0,
        "max": 1e10,
    },
    "animation": {
        "type": "boolean",
        "required": True,
    },
    "hosts": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
            "regex": "^[^:]+:[0-9]{1,5}$",
        },
        "minlength": 1,
        "required": True,
    },
    "peeringhosts": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
            "regex": "^[^:]+:[0-9]{1,5}$",
        },
        "minlength": 1,
        "match_length": "hosts",
        "required": True,
    },
    "database": {
        "type": "boolean",
        "required": True,
    },
    "dbhost": {
        "type": "string",
        "empty": False,
        "regex": "^[^:]+:[0-9]{1,5}$",
        "dependencies": {"database": [True]},
    },
    "networkparams": {
        "type": "dict",
        "schema": NETWORKPARAMS_SCHEMA,
        "require_all": True,
        "required": True,
    },
    "computeparams": {
        "type": "dict",
        "schema": COMPUTEPARAMS_SCHEMA,
        "require_all": True,
        "required": True,
    },
    "sgp4params": {
        "type": "dict",
        "schema": SGP4PARAMS_SCHEMA,
        "dependencies": {"model": ["SGP4"]},
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
                "planes": {
                    "type": "integer",
                    "min": 1,
                    "required": True
                },
                "sats": {
                    "type": "integer",
                    "min": 1,
                    "required": True
                },
                "altitude": {
                    "type": "integer",
                    "min": 0,
                    "required": True
                },
                "inclination": {
                    "type": "float",
                    "min": 0.0,
                    "max": 360.0,
                    "required": True
                },
                "arcofascendingnodes": {
                    "type": "float",
                    "required": True
                },
                "eccentricity": {
                    "type": "float",
                    "required": True
                },
                "networkparams": {
                    "type": "dict",
                    "schema": NETWORKPARAMS_SCHEMA
                },
                "computeparams": {
                    "type": "dict",
                    "schema": COMPUTEPARAMS_SCHEMA,
                },
                "sgp4params": {
                    "type": "dict",
                    "schema": SGP4PARAMS_SCHEMA,
                    "dependencies": {"^model": ["SGP4"]},
                },
            },
        },
    },
    "groundstation": {
        "type": "list",
        "check_with": "gst_name_unique",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "empty": False,
                    "required": True
                },
                "lat": LAT,
                "long": LON,
                "networkparams": {
                    "type": "dict",
                    "schema": NETWORKPARAMS_SCHEMA
                },
                "computeparams": {
                    "type": "dict",
                    "schema": COMPUTEPARAMS_SCHEMA,
                },
            },
        },
    },
}

class CelestialValidator(cerberus.Validator): # type: ignore
    def _check_with_max_satellites(self, field: str, value: typing.Dict[str, typing.Any]) -> bool:
        if "planes" not in value or "sats" not in value:
            return False

        if value["planes"] * value["sats"] > 16384:
            self._error(field, "max. 16384 satellites allowed per shell")
            return False

        return True

    def _check_with_gst_name_unique(self, field: str, value: typing.List[typing.Dict[str, str]]) -> None:
        names: typing.Set[str] = set()
        without_names: typing.Set[str] = set()
        duplicates: typing.Set[str] = set()

        for gst in value:
            if not "name" in gst:
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

    def _validate_match_length(self, other: str, field: str, value: typing.List[str]) -> None:

        "{'type': 'string'}"

        if len(value) != len(self.document[other]):
            self._error(field, "Length %d is not %d (length of field %s)" % (len(value), len(self.document[other]), other))

    def _validate_allowed_max(self, other: str, field: str, value: typing.List[int]) -> None:

        "{'type': 'string'}"

        for i in value:
            if i >= len(self.root_document[other]):
                self._error(field, "Host %d is not in %s" % (i, other))

def validate_configuration(config: typing.MutableMapping[str, typing.Any]) -> None:
    v = CelestialValidator(CONFIG_SCHEMA)
    if not v.validate(config):
        raise ValueError(v.errors)

def fill_configuration(config: typing.MutableMapping[str, typing.Any]) -> Configuration:

    if "bootparams" not in config["computeparams"]:
        config["computeparams"]["bootparams"] = ""

    if "hostaffinity" not in config["computeparams"]:
        config["computeparams"]["hostaffinity"] = range(len(config["hosts"]))

    if "sgp4params" not in config:
        config["sgp4params"] = None

    for shell in config["shell"]:
        network = {}

        if config["networkparams"] is not None:
            for key, value in config["networkparams"].items():
                network[key] = value

        if "networkparams" in shell:
            for key, value in shell["networkparams"].items():
                network[key] = value

        shell["networkparams"] = network

    if "groundstation" not in config:
        config["groundstation"] = []

    for groundstation in config["groundstation"]:
        network = {}

        if config["networkparams"] is not None:
            for key, value in config["networkparams"].items():
                network[key] = value

        if "networkparams" in groundstation:
            for key, value in groundstation["networkparams"].items():
                network[key] = value

        groundstation["networkparams"] = network

    for shell in config["shell"]:
        compute = {}

        if config["computeparams"] is not None:
            for key, value in config["computeparams"].items():
                compute[key] = value

        if "computeparams" in shell:
            for key, value in shell["computeparams"].items():
                compute[key] = value

        shell["computeparams"] = compute

    for groundstation in config["groundstation"]:
        compute = {}

        if config["computeparams"] is not None:
            for key, value in config["computeparams"].items():
                compute[key] = value

        if "computeparams" in groundstation:
            for key, value in groundstation["computeparams"].items():
                compute[key] = value

        groundstation["computeparams"] = compute

    if config["model"] == "SGP4":
        for shell in config["shell"]:
            sgp4_kwargs = {
                "starttime": datetime.datetime.now(),
                "model": "WGS72",
                "mode": "i",
                "bstar": 0.0,
                "ndot": 0.0,
                "argpo": 0.0,
            }

            if "sgp4params" in config:
                for key, value in config["sgp4params"].items():
                    sgp4_kwargs[key] = value

            if "sgp4params" in shell:
                for key, value in shell["sgp4params"].items():
                    sgp4_kwargs[key] = value

            shell["sgp4params"] = sgp4_kwargs

    return config_object_from_configuration(config)

def config_object_from_configuration(config: typing.MutableMapping[str, typing.Any]) -> Configuration:

    return Configuration(
        model=Model(config["model"]),
        bbox=BoundingBoxConfig(lat1=config["bbox"][0], lon1=config["bbox"][1], lat2=config["bbox"][2], lon2=config["bbox"][3]),
        interval=config["interval"],
        animation=config["animation"],
        hosts=config["hosts"],
        peeringhosts=config["peeringhosts"],
        database=config["database"],
        dbhost=(config["dbhost"] if config["database"] else None),
        shells=[ShellConfig(
            planes=s["planes"],
            sats=s["sats"],
            altitude=s["altitude"],
            inclination=s["inclination"],
            arcofascendingnodes=s["arcofascendingnodes"],
            eccentricity=s["eccentricity"],
            networkparams=NetworkParamsConfig(
                islpropagation=s["networkparams"]["islpropagation"],
                bandwidth=s["networkparams"]["bandwidth"],
                mincommsaltitude=s["networkparams"]["mincommsaltitude"],
                minelevation=s["networkparams"]["minelevation"],
                gstpropagation=s["networkparams"]["gstpropagation"],
                groundstationconnectiontype=GroundstationConnectionTypeConfig(s["networkparams"]["groundstationconnectiontype"]),
            ),
            computeparams=ComputeParamsConfig(
                vcpu_count=s["computeparams"]["vcpu_count"],
                mem_size_mib=s["computeparams"]["mem_size_mib"],
                ht_enabled=s["computeparams"]["ht_enabled"],
                kernel=s["computeparams"]["kernel"],
                rootfs=s["computeparams"]["rootfs"],
                bootparams=s["computeparams"]["bootparams"],
                hostaffinity=s["computeparams"]["hostaffinity"],
            ),
            sgp4params=(None if config["model"] != "SGP4" else SGP4ParamsConfig(
                starttime=s["sgp4params"]["starttime"],
                model=SGP4ModelConfig(s["sgp4params"]["model"]),
                mode=SGP4ModeConfig(s["sgp4params"]["mode"]),
                bstar=s["sgp4params"]["bstar"],
                ndot=s["sgp4params"]["ndot"],
                argpo=s["sgp4params"]["argpo"],
            ))
        ) for s in config["shell"]],
        groundstations=[GroundstationConfig(
            name=g["name"],
            lat=g["lat"],
            lng=g["long"],
            networkparams=NetworkParamsConfig(
                islpropagation=g["networkparams"]["islpropagation"],
                bandwidth=g["networkparams"]["bandwidth"],
                mincommsaltitude=g["networkparams"]["mincommsaltitude"],
                minelevation=g["networkparams"]["minelevation"],
                gstpropagation=g["networkparams"]["gstpropagation"],
                groundstationconnectiontype=GroundstationConnectionTypeConfig(g["networkparams"]["groundstationconnectiontype"]),
            ),
            computeparams=ComputeParamsConfig(
                vcpu_count=g["computeparams"]["vcpu_count"],
                mem_size_mib=g["computeparams"]["mem_size_mib"],
                ht_enabled=g["computeparams"]["ht_enabled"],
                kernel=g["computeparams"]["kernel"],
                rootfs=g["computeparams"]["rootfs"],
                bootparams=g["computeparams"]["bootparams"],
                hostaffinity=g["computeparams"]["hostaffinity"],
            ),
        )for g in config["groundstation"]]
    )
