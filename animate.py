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

import time
import toml
import sys
import multiprocessing as mp

import celestial.config
import celestial.constellation
import celestial.animation

if __name__ == "__main__":
    if len(sys.argv) > 3 or len(sys.argv) < 2:
        exit("Usage: python3 celestial.py [config.toml] [output-file (optional)]")

    # read toml
    try:
        text_config = toml.load(sys.argv[1])
    except Exception as e:
        exit(str(e))

    output_file = None
    if len(sys.argv) == 3:
        output_file = sys.argv[2]

    # read the configuration
    config: celestial.config.Config = celestial.config.Config(text_config)

    animation_conn, animation_constellation_conn = mp.Pipe()

    animation = mp.Process(
        target=celestial.animation.Animation,
        kwargs={
            "config": config,
            "animation_conn": animation_conn,
        },
    )

    animation.start()

    # init the constellation
    constellation = celestial.animation.AnimationConstellation(
        config, animation_constellation_conn
    )

    # run the simulation
    i = 0
    start_time = time.perf_counter()

    while i < config.duration:
        print(f"step {i}")
        constellation.step(i)
        i += config.resolution

        while time.perf_counter() - start_time < i:
            time.sleep(0.001)

    animation.join()

    print("Done!")
