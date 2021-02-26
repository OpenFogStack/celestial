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

import toml
import sys
import multiprocessing as mp

from celestial.animation import Animation
from celestial.configuration import fill_configuration, validate_configuration
from celestial.check_bbox import check_bbox
from celestial.constellation import Constellation
from celestial.repeated_timer import RepeatedTimer

if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 animate.py [config.toml]")

# read toml
    try:
        text_config = toml.load(sys.argv[1])
    except Exception as e:
        exit(e)

    print("📄 Validating configuration...")
    try:
        validate_configuration(text_config)
    except Exception as e:
        print("\033[91m❌ Invalid configuration!\033[0m")
        exit(e)
    print("\033[92m✅ Configuration valid!\033[0m")

    config = fill_configuration(text_config)

    config.animation = True

    print("🗺  Validating bounding box...")
    if check_bbox(config.bbox, config.shells, config.groundstations):
         print("\033[92m✅ All ground stations are covered by your bounding box!\033[0m")

    # initialize a constellation
    constellation_conn, mm_conn = mp.Pipe()

    animation_conn = None

    animation_conn, animation_constellation_conn = mp.Pipe()

    animation = mp.Process(target=Animation, kwargs={
        "p": animation_constellation_conn
    })
    animation.start()


    c = Constellation(model=config.model, shells=config.shells, groundstations=config.groundstations, mm_conn=mm_conn, interval=config.interval, animate=True, animate_only=True, bbox=config.bbox, animation_conn=animation_conn)

    timer = RepeatedTimer(config.interval, c.update)