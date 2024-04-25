#!/usr/bin/env python3

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

import sys
import ping3  # type: ignore
import typing
import time
import requests  # type: ignore

DEBUG = False

ping3.EXCEPTIONS = DEBUG


def get_id(gateway: str) -> typing.Tuple[str, str]:
    try:
        response = requests.get(f"http://{gateway}/self")
        data = response.json()

        if DEBUG:
            print(f"get_id {data}")

        return (
            ("gst", str(data["identifier"]["name"]))
            if "name" in data["identifier"] and data["identifier"]["name"] != ""
            else (str(data["identifier"]["shell"]), str(data["identifier"]["id"]))
        )
    except Exception as e:
        print(f"got error when trying to get self info {e}")
        return "", ""


def get_shell_num(gateway: str) -> int:
    try:
        while True:
            response = requests.get(f"http://{gateway}/info")

            if response.status_code != 200:
                time.sleep(1.0)
                continue

            data = response.json()

            if DEBUG:
                print(f"get_shell_num {data}")

            return len(data["shells"])

    except Exception as e:
        print(f"got error when trying to get shell info {e}")
        return 0


def get_gst(gateway: str) -> typing.List[str]:
    try:
        while True:
            response = requests.get(f"http://{gateway}/info")

            if response.status_code != 200:
                time.sleep(1.0)
                continue

            data = response.json()

            if DEBUG:
                print(f"get_gst {data}")

            return [g["identifier"]["name"] for g in data["groundstations"]]

    except Exception as e:
        print(f"got error when trying to get shell info {e}")
        return []


def get_active_sats(shells: int, gateway: str) -> typing.List[typing.Dict[str, str]]:
    active = []

    for s in range(1, shells + 1):
        try:
            response = requests.get(f"http://{gateway}/shell/{s}")
            data = response.json()

            if DEBUG:
                print(f"get_active_sats {data}")

            for sat in data["sats"]:
                if sat["active"]:
                    active.append(
                        {
                            "sat": str(sat["identifier"]["id"]),
                            "shell": str(sat["identifier"]["shell"]),
                        }
                    )

        except Exception as e:
            print(f"got error when trying to get active sats in {s} info {e}")

    return active


def get_expected_latency(
    self_shell: str, self_id: str, shell: str, sat: str, gateway: str
) -> typing.Union[float, bool]:
    if DEBUG:
        print(
            f"get_expected_latency {self_shell} ({type(self_shell)}) {self_id} ({type(self_id)}) {shell} ({type(shell)}) {sat} ({type(sat)})"
        )

    if str(self_shell) == str(shell) and str(self_id) == str(sat):
        return 0.0

    try:
        response = requests.get(
            f"http://{gateway}/path/{self_shell}/{self_id}/{shell}/{sat}"
        )

        data = response.json()

        if DEBUG:
            print(f"get_expected_latency {data}")

        if "blocked" in data and data["blocked"]:
            return False

        return float(data["delay_us"]) / 1e3

    except Exception as e:
        print(
            f"got error when trying to get expected latency for sat {sat} shell {shell} {e}"
        )
        return False


def get_real_latency(sat: str, shell: str) -> typing.Union[float, bool]:
    if DEBUG:
        try:
            _ = ping3.verbose_ping(f"{sat}.{shell}.celestial", unit="ms", timeout=1)
            return False

        except Exception as e:
            print(
                f"got error when trying to get real latency for sat {sat} shell {shell} {e}"
            )
            return False

    # send 4 pings and take the average
    act = 0.0
    n_pings = 4
    for _ in range(n_pings):
        p = ping3.ping(f"{sat}.{shell}.celestial", unit="ms", timeout=1)

        if p is None:
            return False

        act += float(p) / float(n_pings)

    return act


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
        if int(id) % 7 != 0:
            exit("id is not a multiple of 7")

    except Exception:
        # id is not a number, probably a ground station
        pass

    shells = get_shell_num(gateway)

    if DEBUG:
        print(f"found {shells} shells")

    gst = get_gst(gateway)

    if DEBUG:
        print(f"found gsts: {gst}")

    while True:
        time.sleep(1.0)

        active = get_active_sats(shells, gateway)

        if DEBUG:
            print(f"found {len(active)} active sats")

        targets = [x for x in active if int(x["sat"]) % 7 == 0] + [
            {"sat": g, "shell": "gst"} for g in gst
        ]

        for sat in targets:
            expBef = get_expected_latency(shell, id, sat["shell"], sat["sat"], gateway)

            real_latency = get_real_latency(sat["sat"], sat["shell"])

            expAft = get_expected_latency(shell, id, sat["shell"], sat["sat"], gateway)

            f.write(
                f"{time.time()},{sat['shell']},{sat['sat']},{expBef},{expAft},{real_latency}\n"
            )

            f.flush()
