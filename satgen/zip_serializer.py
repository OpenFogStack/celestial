import os
import pickle
import shutil
import subprocess
import struct
import typing

import satgen.types
import satgen.config

CONFIG_FILE = "c"
INIT_FILE = "i"
DIFF_LINK_FILE_PREFIX = "l"
DIFF_MACHINE_FILE_PREFIX = "m"


def config_to_bytes(config: satgen.config.Config) -> bytes:
    return pickle.dumps(config)


def config_from_bytes(b: bytes) -> satgen.config.Config:
    c = pickle.loads(b)

    if not isinstance(c, satgen.config.Config):
        raise TypeError(f"Invalid config: {c}")

    return c


# INIT commands include too many strings, hence we use CSV
INIT_HEAD = "machine_id_group,machine_id_id,machine_id_name,config_vcpu_count,config_mem_size_mib,config_disk_size,config_kernel,config_rootfs,config_boot_parameters"
LIST_SEP = "|"


def init_to_str(
    machine: satgen.types.MachineID_dtype, config: satgen.config.MachineConfig
) -> str:
    b = LIST_SEP.join(config.boot_parameters)

    return f"{machine[0]},{machine[1]},{machine[2]},{config.vcpu_count},{config.mem_size_mib},{config.disk_size},{config.kernel},{config.rootfs},{b}"


def init_from_str(
    s: str,
) -> typing.Tuple[satgen.types.MachineID_dtype, satgen.config.MachineConfig]:
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
            satgen.types.MachineID(int(group), int(id), name),
            satgen.config.MachineConfig(
                int(vcpu_count),
                int(mem_size_mib),
                int(disk_size),
                kernel,
                rootfs,
                boot_parameters.split(LIST_SEP),
            ),
        )
    except ValueError as e:
        raise ValueError(f"Invalid init string: {s}: {e}")


# struct format strings
# https://docs.python.org/3/library/struct.html
#  we always force little-endian byte order
# diff_link
# (source_machine_id_group:uint8/B,source_machine_id_id:uint16/H,target_machine_id_group:uint8/B,target_machine_id_id:uint16/H,link_latency:uint32/I,link_bandwidth:uint32/I,link_blocked:bool/?,link_next_hop_machine_id_group:uint8/B,link_next_hop_machine_id_id:uint16/H)
DIFF_LINK_FMT = "<BHBHII?BH"
# diff_machine
# (machine_id_group:uint8/B,machine_id_id:uint16/H,vm_state:uint8/B)
DIFF_MACHINE_FMT = "<BHB"


def diff_link_to_bytes(
    source: satgen.types.MachineID_dtype,
    target: satgen.types.MachineID_dtype,
    link: satgen.types.Link_dtype,
) -> bytes:
    return struct.pack(
        DIFF_LINK_FMT,
        satgen.types.MachineID_group(source),
        satgen.types.MachineID_id(source),
        satgen.types.MachineID_group(target),
        satgen.types.MachineID_id(target),
        satgen.types.Link_latency_us(link),
        satgen.types.Link_bandwidth_kbits(link),
        satgen.types.Link_blocked(link),
        satgen.types.MachineID_group(satgen.types.Link_next_hop(link)),
        satgen.types.MachineID_id(satgen.types.Link_next_hop(link)),
    )


def diff_link_from_bytes(
    b: bytes,
) -> typing.List[
    typing.Tuple[
        satgen.types.MachineID_dtype,
        satgen.types.MachineID_dtype,
        satgen.types.Link_dtype,
    ]
]:
    return [
        (
            satgen.types.MachineID(source_machine_id_group, source_machine_id_id),
            satgen.types.MachineID(target_machine_id_group, target_machine_id_id),
            satgen.types.Link(
                link_latency_us,
                link_bandwidth_kbits,
                link_blocked,
                satgen.types.MachineID(
                    link_next_hop_machine_id_group, link_next_hop_machine_id_id
                ),
            ),
        )
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
        ) in struct.iter_unpack(DIFF_LINK_FMT, b)
    ]


def diff_machine_to_bytes(
    machine: satgen.types.MachineID_dtype, s: satgen.types.VMState
) -> bytes:
    return struct.pack(
        DIFF_MACHINE_FMT,
        satgen.types.MachineID_group(machine),
        satgen.types.MachineID_id(machine),
        s.value,
    )


def diff_machine_from_bytes(
    b: bytes,
) -> typing.List[typing.Tuple[satgen.types.MachineID_dtype, satgen.types.VMState]]:
    return [
        (
            satgen.types.MachineID(machine_id_group, machine_id_id),
            satgen.types.VMState(vm_state),
        )
        for (machine_id_group, machine_id_id, vm_state) in struct.iter_unpack(
            DIFF_MACHINE_FMT, b
        )
    ]


class ZipSerializer:
    def __init__(
        self, config: satgen.config.Config, output_file: typing.Optional[str] = None
    ):
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
        with open(os.path.join(self.write_dir, CONFIG_FILE), "wb") as f:
            f.write(config_to_bytes(config))

    def init_machine(
        self, machine: satgen.types.MachineID_dtype, config: satgen.config.MachineConfig
    ) -> None:
        with open(os.path.join(self.write_dir, INIT_FILE), "a") as f:
            f.write(f"{init_to_str(machine, config)}\n")

    def diff_link(
        self,
        t: satgen.types.timestamp_s,
        source: satgen.types.MachineID_dtype,
        target: satgen.types.MachineID_dtype,
        link: satgen.types.Link_dtype,
    ) -> None:
        with open(
            os.path.join(self.write_dir, f"{DIFF_LINK_FILE_PREFIX}{t}"), "ab"
        ) as f:
            f.write(diff_link_to_bytes(source, target, link))

    def diff_machine(
        self,
        t: satgen.types.timestamp_s,
        machine: satgen.types.MachineID_dtype,
        s: satgen.types.VMState,
    ) -> None:
        # print(f"diff_machine: {t} {machine} {s}")
        with open(
            os.path.join(self.write_dir, f"{DIFF_MACHINE_FILE_PREFIX}{t}"), "ab"
        ) as f:
            f.write(diff_machine_to_bytes(machine, s))

    def persist(self) -> None:
        # zip the temporary directory
        # filename = os.path.join(self.tmp_dir, self.filename)
        shutil.make_archive(self.filename, "zip", self.write_dir)

        # change the file extension to .celestial
        # os.rename(self.filename + ".zip", self.filename + ".celestial")

        # move the filename to the current directory
        # shutil.move(filename + ".celestial", ".")
        # self.filename = self.filename + ".celestial"

        # remove the temporary directory
        shutil.rmtree(self.tmp_dir)


class ZipDeserializer:
    def __init__(self, filename: str):
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

    def config(self) -> satgen.config.Config:
        with open(os.path.join(self.tmp_dir, CONFIG_FILE), "rb") as f:
            return config_from_bytes(f.read())

    def init_machines(
        self,
    ) -> typing.List[
        typing.Tuple[satgen.types.MachineID_dtype, satgen.config.MachineConfig]
    ]:
        if not os.path.exists(os.path.join(self.tmp_dir, INIT_FILE)):
            return []
        with open(os.path.join(self.tmp_dir, INIT_FILE), "r") as f:
            return [init_from_str(line) for line in f.readlines()]

    def diff_links(
        self, t: satgen.types.timestamp_s
    ) -> typing.List[
        typing.Tuple[
            satgen.types.MachineID_dtype,
            satgen.types.MachineID_dtype,
            satgen.types.Link_dtype,
        ]
    ]:
        if not os.path.exists(
            os.path.join(self.tmp_dir, f"{DIFF_LINK_FILE_PREFIX}{t}")
        ):
            return []

        with open(os.path.join(self.tmp_dir, f"{DIFF_LINK_FILE_PREFIX}{t}"), "rb") as f:
            return diff_link_from_bytes(f.read())

    def diff_machines(
        self, t: satgen.types.timestamp_s
    ) -> typing.List[typing.Tuple[satgen.types.MachineID_dtype, satgen.types.VMState]]:
        if not os.path.exists(
            os.path.join(self.tmp_dir, f"{DIFF_MACHINE_FILE_PREFIX}{t}")
        ):
            return []

        with open(
            os.path.join(self.tmp_dir, f"{DIFF_MACHINE_FILE_PREFIX}{t}"), "rb"
        ) as f:
            return diff_machine_from_bytes(f.read())
