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

"""Serialization of Celestial initialization and updates to a custom .zip format file."""

import os
import pickle
import shutil
import subprocess
import struct
import typing

import celestial.types
import celestial.config

_CONFIG_FILE = "c"
_INIT_FILE = "i"
_DIFF_LINK_FILE_PREFIX = "l"
_DIFF_MACHINE_FILE_PREFIX = "m"


def _config_to_bytes(config: celestial.config.Config) -> bytes:
    """
    Serialize a Celestial configuration to bytes.

    :param config: The configuration to serialize.
    :returns: The serialized configuration.
    """
    return pickle.dumps(config)


def _config_from_bytes(b: bytes) -> celestial.config.Config:
    """
    Restore a Celestial configuration from bytes.

    :param b: The serialized configuration.
    :returns: The restored configuration.
    :raises TypeError: If the serialized configuration is not a valid
        configuration.
    """
    c = pickle.loads(b)

    if not isinstance(c, celestial.config.Config):
        raise TypeError(f"Invalid config: {c}")

    return c


# INIT commands include too many strings, hence we use CSV
_INIT_HEAD = "machine_id_group,machine_id_id,machine_id_name,config_vcpu_count,config_mem_size_mib,config_disk_size,config_kernel,config_rootfs,config_boot_parameters"
_LIST_SEP = "|"


def _init_to_str(
    machine: celestial.types.MachineID_dtype, config: celestial.config.MachineConfig
) -> str:
    """
    Serialize the initialization of a Celestial emulation VM to a string.
    We serialize to CSV instead of a binary format as we may have to deal
    with strings (mostly for VM parameters such as boot parameters, kernel
    path, and image path). This is not optimal but good enough, as we only
    have to read the initialization file once.

    :param machine: The machine ID of the machine to initialize.
    :param config: The configuration of the machine to initialize.
    :returns: The serialized initialization.
    """
    b = _LIST_SEP.join(config.boot_parameters)

    return f"{machine[0]},{machine[1]},{machine[2]},{config.vcpu_count},{config.mem_size_mib},{config.disk_size},{config.kernel},{config.rootfs},{b}"


def _init_from_str(
    s: str,
) -> typing.Tuple[celestial.types.MachineID_dtype, celestial.config.MachineConfig]:
    """
    Restore the machine initialization parameters from a CSV line.

    :param s: The serialized initialization.
    :returns: The machine ID and its configuration.
    :raises ValueError: If the serialized initialization is not a valid
        initialization.
    """

    (
        group,
        id,
        name,
        vcpu_count,
        mem_size_mib,
        disk_size,
        kernel,
        rootfs,
        boot_parameters,
    ) = s.split(",")
    try:
        return (
            celestial.types.MachineID(int(group), int(id), name),
            celestial.config.MachineConfig(
                int(vcpu_count),
                int(mem_size_mib),
                int(disk_size),
                kernel,
                rootfs,
                boot_parameters.split(_LIST_SEP),
            ),
        )
    except ValueError as e:
        raise ValueError(f"Invalid init string: {s}: {e}")


# struct format strings
# https://docs.python.org/3/library/struct.html
#  we always force little-endian byte order
# diff_link
# (source_machine_id_group:uint8/B,source_machine_id_id:uint16/H,target_machine_id_group:uint8/B,target_machine_id_id:uint16/H,link_latency:uint32/I,link_bandwidth:uint32/I,link_blocked:bool/?,link_next_hop_machine_id_group:uint8/B,link_next_hop_machine_id_id:uint16/H,link_prev_hop_machine_id_group:uint8/B,link_prev_hop_machine_id_id:uint16/H)
_DIFF_LINK_FMT = "<BHBHII?BHBH"
# diff_machine
# (machine_id_group:uint8/B,machine_id_id:uint16/H,vm_state:uint8/B)
_DIFF_MACHINE_FMT = "<BHB"


def _diff_link_to_bytes(
    source: celestial.types.MachineID_dtype,
    target: celestial.types.MachineID_dtype,
    link: celestial.types.Link_dtype,
) -> bytes:
    """
    Serialize a link diff to bytes using the struct format string.

    :param source: The source machine ID of the link.
    :param target: The target machine ID of the link.
    :param link: The link to serialize.
    :returns: The serialized link as bytes.
    """
    return struct.pack(
        _DIFF_LINK_FMT,
        celestial.types.MachineID_group(source),
        celestial.types.MachineID_id(source),
        celestial.types.MachineID_group(target),
        celestial.types.MachineID_id(target),
        celestial.types.Link_latency_us(link),
        celestial.types.Link_bandwidth_kbits(link),
        celestial.types.Link_blocked(link),
        celestial.types.MachineID_group(celestial.types.Link_next_hop(link)),
        celestial.types.MachineID_id(celestial.types.Link_next_hop(link)),
        celestial.types.MachineID_group(celestial.types.Link_prev_hop(link)),
        celestial.types.MachineID_id(celestial.types.Link_prev_hop(link)),
    )


def _diff_link_from_bytes(
    b: bytes,
) -> typing.Iterator[
    typing.Tuple[
        celestial.types.MachineID_dtype,
        celestial.types.MachineID_dtype,
        celestial.types.Link_dtype,
    ]
]:
    """
    Restore link diffs from bytes using the struct format string.

    :param b: Bytes of all serialized links in a timestep.
    :returns: The restored links as an iterator.
    """

    for (
        source_machine_id_group,
        source_machine_id_id,
        target_machine_id_group,
        target_machine_id_id,
        link_latency_us,
        link_bandwidth_kbits,
        link_blocked,
        link_next_hop_machine_id_group,
        link_next_hop_machine_id_id,
        link_prev_hop_machine_id_group,
        link_prev_hop_machine_id_id,
    ) in struct.iter_unpack(_DIFF_LINK_FMT, b):
        yield (
            celestial.types.MachineID(source_machine_id_group, source_machine_id_id),
            celestial.types.MachineID(target_machine_id_group, target_machine_id_id),
            celestial.types.Link(
                link_latency_us,
                link_bandwidth_kbits,
                link_blocked,
                celestial.types.MachineID(
                    link_next_hop_machine_id_group, link_next_hop_machine_id_id
                ),
                celestial.types.MachineID(
                    link_prev_hop_machine_id_group, link_prev_hop_machine_id_id
                ),
            ),
        )


def _diff_machine_to_bytes(
    machine: celestial.types.MachineID_dtype, s: celestial.types.VMState
) -> bytes:
    """
    Serialize a machine diff to bytes using the struct format string.

    :param machine: The machine ID of the machine to serialize.
    :param s: The VM state of the machine to serialize.
    :returns: The serialized machine diff as bytes.
    """
    return struct.pack(
        _DIFF_MACHINE_FMT,
        celestial.types.MachineID_group(machine),
        celestial.types.MachineID_id(machine),
        s.value,
    )


def _diff_machine_from_bytes(
    b: bytes,
) -> typing.Iterator[
    typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
]:
    """
    Restore machine diffs from bytes using the struct format string.

    :param b: Bytes of all serialized machines in a timestep.
    :returns: The restored machines as an iterator.
    """
    for machine_id_group, machine_id_id, vm_state in struct.iter_unpack(
        _DIFF_MACHINE_FMT, b
    ):
        yield (
            celestial.types.MachineID(machine_id_group, machine_id_id),
            celestial.types.VMState(vm_state),
        )


class ZipSerializer:
    """
    The ZipSerializer implements the Serializer interface and serializes
    Celestial initialization and updates to a custom .zip format file.
    We use mostly bytes for serialization, except for the initialization
    file, which is serialized to CSV.
    This combination allows us efficient compression and fast serialization
    for updates without being too hairy to implement for initialization.

    Note that the resulting .zip file is not meant for manual inspection
    but should be used with the ZipDeserializer to restore the initialization
    and updates.
    """

    def __init__(
        self, config: celestial.config.Config, output_file: typing.Optional[str] = None
    ):
        """
        Initialize the serializer.

        :param config: The Celestial configuration.
        :param output_file: The output file to write to. If None, a filename
            will be generated based on a hash of the configuration.

        :raises FileExistsError: If `mktemp` fails and the temporary directory
            `./tmp` already exists.
        """
        if output_file is None:
            self.filename = "{:08x}".format(abs(hash(config)))
        else:
            self.filename = output_file
            if self.filename.endswith(".zip"):
                self.filename = self.filename[:-4]

        # create a temporary directory
        # check if the `mktemp` command is available
        self.tmp_dir = "./.tmp"
        if subprocess.run(["which", "mktemp"]).returncode == 0:
            self.tmp_dir = (
                subprocess.run(["mktemp", "-d"], capture_output=True)
                .stdout.decode("utf-8")
                .strip()
            )
        else:
            print("WARNING: `mktemp` command not found. Using `./.tmp` instead.")
            try:
                os.makedirs(self.tmp_dir, exist_ok=False)
            except FileExistsError:
                print("ERROR: `./.tmp` already exists. Please remove it and try again.")
                raise

        self.write_dir = os.path.join(self.tmp_dir, "raw")
        os.makedirs(self.write_dir, exist_ok=False)

        # write the config
        with open(os.path.join(self.write_dir, _CONFIG_FILE), "wb") as f:
            f.write(_config_to_bytes(config))

    def init_machine(
        self,
        machine: celestial.types.MachineID_dtype,
        config: celestial.config.MachineConfig,
    ) -> None:
        """
        Write an initialization for a machine to the initialization file.

        :param machine: The machine ID of the machine to initialize.
        :param config: The configuration of the machine to initialize.
        """
        with open(os.path.join(self.write_dir, _INIT_FILE), "a") as f:
            f.write(f"{_init_to_str(machine, config)}\n")

    def diff_link(
        self,
        t: celestial.types.timestamp_s,
        source: celestial.types.MachineID_dtype,
        target: celestial.types.MachineID_dtype,
        link: celestial.types.Link_dtype,
    ) -> None:
        """
        Write a link diff to the link diff file.

        :param t: The timestamp of the link diff.
        :param source: The source machine ID of the link.
        :param target: The target machine ID of the link.
        :param link: The link to serialize.
        """
        with open(
            os.path.join(self.write_dir, f"{_DIFF_LINK_FILE_PREFIX}{t}"), "ab"
        ) as f:
            f.write(_diff_link_to_bytes(source, target, link))

    def diff_machine(
        self,
        t: celestial.types.timestamp_s,
        machine: celestial.types.MachineID_dtype,
        s: celestial.types.VMState,
    ) -> None:
        """
        Write a machine diff to the machine diff file.

        :param t: The timestamp of the machine diff.
        :param machine: The machine ID of the machine to serialize.
        :param s: The VM state of the machine to serialize.
        """
        with open(
            os.path.join(self.write_dir, f"{_DIFF_MACHINE_FILE_PREFIX}{t}"), "ab"
        ) as f:
            f.write(_diff_machine_to_bytes(machine, s))

    def persist(self) -> None:
        """
        Persist the serialized initialization and updates to a .zip file.

        :raises FileExistsError: If the output file already exists.
        """
        # zip the temporary directory
        # filename = os.path.join(self.tmp_dir, self.filename)
        shutil.make_archive(self.filename, "zip", self.write_dir)

        # remove the temporary directory
        shutil.rmtree(self.tmp_dir)


class ZipDeserializer:
    """
    The ZipDeserializer implements the Deserializer interface and deserializes
    Celestial initialization and updates from a custom .zip format file created
    by the ZipSerializer.
    """

    def __init__(self, filename: str):
        """
        Initialize the deserializer.

        :param filename: The filename of the .zip file to deserialize from.

        :raises FileExistsError: If `mktemp` fails and the temporary directory
            `./tmp` already exists.
        """
        self.filename = filename

        # create a temporary directory
        # check if the `mktemp` command is available
        self.tmp_dir = "./.tmp"
        if subprocess.run(["which", "mktemp"]).returncode == 0:
            self.tmp_dir = (
                subprocess.run(["mktemp", "-d"], capture_output=True)
                .stdout.decode("utf-8")
                .strip()
            )
        else:
            print("WARNING: `mktemp` command not found. Using `./.tmp` instead.")
            try:
                os.makedirs(self.tmp_dir, exist_ok=False)
            except FileExistsError:
                print("ERROR: `./.tmp` already exists. Please remove it and try again.")
                raise

        # unzip the file
        shutil.unpack_archive(self.filename, self.tmp_dir)

    def config(self) -> celestial.config.Config:
        """
        Restore the Celestial configuration from the configuration file
        copied to the .zip file.

        :returns: The restored configuration.
        """
        p = os.path.join(self.tmp_dir, _CONFIG_FILE)
        with open(p, "rb") as f:
            return _config_from_bytes(f.read())

    def init_machines(
        self,
    ) -> typing.List[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.config.MachineConfig]
    ]:
        """
        Restore the machine initializations from the initialization file
        copied to the .zip file.

        :returns: A list of the restored machine initializations.
        """
        p = os.path.join(self.tmp_dir, _INIT_FILE)
        if not os.path.exists(p):
            return []
        with open(p, "r") as f:
            return [_init_from_str(line) for line in f.readlines()]

    def diff_links(
        self, t: celestial.types.timestamp_s
    ) -> typing.Iterator[
        typing.Tuple[
            celestial.types.MachineID_dtype,
            celestial.types.MachineID_dtype,
            celestial.types.Link_dtype,
        ]
    ]:
        """
        Restore the link diffs from the link diff file copied to the .zip file
        for a given timestep.

        :param t: The timestep to restore the link diffs for.
        :returns: An iterator of the restored link diffs.
        """

        p = os.path.join(self.tmp_dir, f"{_DIFF_LINK_FILE_PREFIX}{t}")

        if not os.path.exists(p):
            yield from ()  # return empty iterator
            return

        with open(p, "rb") as f:
            for ld in _diff_link_from_bytes(f.read()):
                yield ld

        return

    def diff_machines(
        self, t: celestial.types.timestamp_s
    ) -> typing.Iterator[
        typing.Tuple[celestial.types.MachineID_dtype, celestial.types.VMState]
    ]:
        """
        Restore the machine diffs from the machine diff file copied to the .zip
        file for a given timestep.

        :param t: The timestep to restore the machine diffs for.
        :returns: An iterator of the restored machine diffs.
        """
        p = os.path.join(self.tmp_dir, f"{_DIFF_MACHINE_FILE_PREFIX}{t}")

        if not os.path.exists(p):
            yield from ()  # return empty iterator
            return

        with open(p, "rb") as f:
            for md in _diff_machine_from_bytes(f.read()):
                yield md

        return
