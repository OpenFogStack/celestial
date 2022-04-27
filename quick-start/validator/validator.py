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

def get_id(gateway: str) -> str:
    try:
        response = requests.get("http://%s/self" % gateway)
        data = response.json()

        return data["name"]
    except Exception:
        return ""

def get_shell_num(gateway: str) -> int:
    try:
        while True:
            response = requests.get("http://%s/info" % gateway)

            if response.status_code != 200:
                time.sleep(1.0)
                continue

            data = response.json()
            return data["shells"]

    except Exception:
        return 0

def get_active_sats(shells: int, gateway: str) -> typing.List[typing.Dict]:
    try:
        active = []

        for s in range(shells):
            response = requests.get("http://%s/shell/%d" % (gateway, s))
            data = response.json()

            active.extend(data["activeSats"])

        return active
    except Exception as e:
        print(e)
        return []

def get_expected_latency(id: str, sat: int, shell: int, gateway: str) -> float:
    try:
        response = requests.get("http://%s/path/gst/%s/%d/%d" % (gateway, id, shell, sat))

        data = response.json()

        min_delay = 1e7

        for p in data["paths"]:
            min_delay = min(p["delay"], min_delay)

        return min_delay
    except Exception:
        return 1e7

def get_real_latency(sat: int, shell: int) -> float:
    act = ping3.ping("%d.%d.celestial" % (sat, shell), unit='ms')

    if act is None or act == False:
        return 1e7

    return act

if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 validator.py [gateway]")

    gateway = sys.argv[1]

    with open("validator.csv", "w") as f:
        f.write("t,shell,sat,expected_before,expected_after,actual_med,actual_avg,actual_max,actual_min,loss\n")

        f.flush()

        id = get_id(gateway)

        print("id is %s" % id)

        shells = get_shell_num(gateway)

        print("found %d shells" % shells)

        control_group = []

        # add some random sats
        for i in range(shells):
            for j in range(1):
                control_group.append({
                    "shell": i,
                    "sat": j,
                })

            for j in range(30, 31):
                control_group.append({
                    "shell": i,
                    "sat": j,
                })

        while True:
            time.sleep(5.0)
            active = get_active_sats(shells, gateway)

            print("found %d active sats" % len(active))

            targets = active.copy()
            targets.extend(control_group)

            for sat in targets:

                print("trying sat %d shell %d" % (sat["sat"], sat["shell"]) )

                expBef = get_expected_latency(id, sat["sat"], sat["shell"], gateway)

                act = get_real_latency(sat["sat"], sat["shell"])

                expAft = get_expected_latency(id, sat["sat"], sat["shell"], gateway)

                # act can be a bit higher than 2*exp but never lower!
                if 0 <= act - (expAft * 2) <= 5 or (expAft == 1e7 and act == 1e7):
                    # good
                    print("\033[92mexpect %f/%f for sat %d shell %d and found %f\033[0m" % (expBef, expAft, sat["sat"], sat["shell"], act))
                else:
                    # bad
                    print("\033[91mexpect %f/%f for sat %d shell %d and found %f\033[0m" % (expBef, expAft, sat["sat"], sat["shell"], act))

                o = ""
                o += str(time.time())
                o += ","
                o += str(sat["shell"])
                o += ","
                o += str(sat["sat"])
                o += ","
                o += str(expBef)
                o += ","
                o += str(expAft)
                o += ","
                o += str(act)
                o += ","
                o += str(act)
                o += ","
                o += str(act)
                o += ","
                o += str(act)
                o += ","
                o += str(act)
                o += "\n"

                f.write(o)

                f.flush()
