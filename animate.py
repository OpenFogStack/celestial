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

"""
If you want to animate a constellation instead of running a full emulation,
you can use this file. It takes a Celestial configuration file and starts a
VTK-based animation of the constellation. You can use the animation to
visualize the constellation and its satellites.

Note that this will not generate a .zip file that can be used for emulation.

Prequisites
-----------

Make sure you have all the necessary dependencies installed. You can install
them using pip in a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-animation.txt

Usage
-----

    python3 animate.py [config.toml]

Note that the animation will start in a new window and may require re-sizing.
To stop the animation, send a SIGTERM or SIGINT to the original process.
Closing the animation window will not stop the animation process properly
(a weird behavior of VTK).
"""

import time
import toml
import sys
import multiprocessing as mp

import celestial.config
import celestial.constellation
import celestial.animation

if __name__ == "__main__":
    if len(sys.argv) > 3 or len(sys.argv) < 2:
        exit("Usage: python3 animate.py [config.toml]")

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
