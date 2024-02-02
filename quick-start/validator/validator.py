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

MAX_DELAY = 1e7
TERM_RED = "\033[91m"
TERM_GREEN = "\033[92m"
TERM_END = "\033[0m"


def get_id(gateway: str) -> str:
    try:
        response = requests.get(f"http://{gateway}/self")
        data = response.json()

        return str(data["identifier"]["name"])
    except Exception:
        return ""


def get_shell_num(gateway: str) -> int:
    while True:
        try:
            response = requests.get(f"http://{gateway}/info")

            if response.status_code != 200:
                time.sleep(1.0)
                continue

            data = response.json()
            return len(data["shells"])

        except Exception:
            pass


def get_active_sats(shells: int, gateway: str) -> typing.List[typing.Dict[str, int]]:
    active = []

    for s in range(1, shells + 1):
        try:
            response = requests.get(f"http://{gateway}/shell/{s}")
            data = response.json()

            for sat in data["sats"]:
                if sat["active"]:
                    active.append(
                        {
                            "sat": sat["identifier"]["id"],
                            "shell": sat["identifier"]["shell"],
                        }
                    )

        except Exception as e:
            print(f"got error when trying to get active sats in {s} info {e}")

    return active


def get_sats_state(
    sats: typing.List[typing.Dict[str, int]], gateway: str
) -> typing.List[typing.Tuple[typing.Dict[str, int], bool]]:
    states = []

    for sat in sats:
        try:
            response = requests.get(
                f"http://{gateway}/shell/{sat['shell']}/{sat['sat']}"
            )
            data = response.json()

            states.append((sat, data["active"]))

        except Exception as e:
            print(f"got error when trying to get sat {sat} info {e}")

    return states


def get_expected_latency(
    self_id: str, sat: int, shell: int, gateway: str
) -> typing.Union[float, bool]:
    try:
        response = requests.get(f"http://{gateway}/path/gst/{self_id}/{shell}/{sat}")

        data = response.json()

        if "blocked" in data and data["blocked"]:
            return MAX_DELAY

        return float(data["delay"]) / 1e3  # convert to ms

    except Exception as e:
        print(
            f"got error when trying to get expected latency for sat {sat} shell {shell} {e}"
        )
        return MAX_DELAY


def get_real_latency(sat: int, shell: int) -> float:
    # send 4 pings and take the average
    act = 0.0
    n_pings = 4
    for _ in range(n_pings):
        p = ping3.ping(f"{sat}.{shell}.celestial", unit="ms", timeout=1)

        if p is None:
            return MAX_DELAY

        act += float(p) / float(n_pings)

    return act


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 validator.py [gateway]")

    gateway = sys.argv[1]

    with open("validator.csv", "w") as f:
        print(
            "t,shell,sat,expected_before,expected_after,actual",
            file=f,
            flush=True,
        )

        id = get_id(gateway)

        print("id is %s" % id)

        shells = get_shell_num(gateway)

        print("found %d shells" % shells)

        control_group = []

        # add some random sats
        for i in range(1, shells + 1):
            for j in range(1):
                control_group.append(
                    {
                        "shell": i,
                        "sat": j,
                    }
                )

            for j in range(30, 31):
                control_group.append(
                    {
                        "shell": i,
                        "sat": j,
                    }
                )

        while True:
            time.sleep(5.0)
            active_sats = get_active_sats(shells, gateway)

            print(f"found {len(active_sats)} active sats")

            targets = [(sat, True) for sat in active_sats]

            targets.extend(get_sats_state(control_group, gateway))

            for sat, active in targets:
                expBef = (
                    get_expected_latency(id, sat["sat"], sat["shell"], gateway)
                    if active
                    else MAX_DELAY
                )

                act = get_real_latency(sat["sat"], sat["shell"])

                expAft = (
                    get_expected_latency(id, sat["sat"], sat["shell"], gateway)
                    if active
                    else MAX_DELAY
                )

                # act can be a bit higher than 2*exp but never lower!
                if 0 <= act - (expAft * 2) <= 5 or (
                    expAft == MAX_DELAY and act == MAX_DELAY
                ):
                    # good
                    print(
                        f"{TERM_GREEN}expect {expBef}/{expAft} for sat {sat['sat']} shell {sat['shell']} and found {act}{TERM_END}"
                    )
                else:
                    # bad
                    print(
                        f"{TERM_RED}expect {expBef}/{expAft} for sat {sat['sat']} shell {sat['shell']} and found {act}{TERM_END}"
                    )

                print(
                    f"{time.time()},{sat['shell']},{sat['sat']},{expBef},{expAft},{act}",
                    file=f,
                    flush=True,
                )
