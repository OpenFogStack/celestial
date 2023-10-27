#!/usr/bin/env python3

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

import sys
import ping3
import typing
import time
import requests


def get_id(gateway: str) -> typing.Tuple[str, str]:
    try:
        response = requests.get(f"http://{gateway}/self")
        data = response.json()

        return (
            ("gst", str(data["name"]))
            if "name" in data
            else (data["shell"], data["id"])
        )
    except Exception as e:
        print(f"got error when trying to get self info {e}", file=sys.stderr)
        return ("", "")


def get_shell_num(gateway: str) -> int:
    try:
        while True:
            response = requests.get(f"http://{gateway}/info")

            if response.status_code != 200:
                time.sleep(1.0)
                continue

            data = response.json()
            return int(data["shells"])

    except Exception as e:
        print(f"got error when trying to get shell info {e}", file=sys.stderr)
        return 0


def get_active_sats(shells: int, gateway: str) -> typing.List[typing.Dict[str, int]]:
    active = []

    for s in range(shells):
        try:
            response = requests.get(f"http://{gateway}/shell/{s}")
            data = response.json()

            active.extend(data["activeSats"])

        except Exception as e:
            print(
                f"got error when trying to get active sats in {s} info {e}",
                file=sys.stderr,
            )

    return active


def get_expected_latency(
    self_shell: str, self_id: str, sat: int, shell: int, gateway: str
) -> typing.Union[float, bool]:
    try:
        response = requests.get(
            f"http://{gateway}/path/{self_shell}/{self_id}/{shell}/{sat}"
        )

        data = response.json()

        min_delay = 1e7

        for p in data["paths"]:
            min_delay = min(p["delay"], min_delay)

        return min_delay
    except Exception as e:
        print(
            f"got error when trying to get expected latency for sat {sat} shell {shell} {e}",
            file=sys.stderr,
        )
        return False


def get_real_latency(sat: int, shell: int) -> typing.Union[float, bool]:
    act = ping3.ping(f"{sat}.{shell}.celestial", unit="ms", timeout=1)

    if act is None or act == False:
        return False

    return float(act)


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 validator.py [gateway]")

    gateway = sys.argv[1]

    f = sys.stdout

    f.write("t,shell,sat,expected_before,expected_after,actual\n")

    f.flush()

    shell = ""
    id = ""
    while id == "":
        shell, id = get_id(gateway)

    print(f"shell is {shell}, id is {id}")

    try:
        if int(id) % 8 != 0:
            exit("id is not a multiple of 8")

    except Exception:
        # id is not a number, probably a ground station
        pass

    shells = get_shell_num(gateway)

    print(f"found {shells} shells")

    active = get_active_sats(shells, gateway)

    print(f"found {len(active)} active sats")

    targets = [x for x in active if x["sat"] % 8 == 0]

    while True:
        time.sleep(1.0)

        for sat in targets:
            expBef = get_expected_latency(shell, id, sat["sat"], sat["shell"], gateway)

            act = get_real_latency(sat["sat"], sat["shell"])

            expAft = get_expected_latency(shell, id, sat["sat"], sat["shell"], gateway)

            f.write(
                f"{time.time()},{sat['shell']},{sat['sat']},{expBef},{expAft},{act}\n"
            )

            f.flush()
