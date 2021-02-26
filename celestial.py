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

from celestial.configuration import fill_configuration, validate_configuration
from celestial.resource_estimate import resource_estimate
from celestial.check_bbox import check_bbox

from celestial.constellation import Constellation
from celestial.repeated_timer import RepeatedTimer
from celestial.machine_manager import MachineManager
from celestial.connection_manager import ConnectionManager

if __name__ == "__main__":
    if not len(sys.argv) == 2:
        exit("Usage: python3 celestial.py [config.toml]")

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

    print("🗺 Validating bounding box...")
    if check_bbox(config.bbox, config.shells, config.groundstations):
         print("\033[92m✅ All ground stations are covered by your bounding box!\033[0m")

    # initialize cloud stuff
    print("⏳ Initializing server peering...")
    cm = ConnectionManager(hosts=config.hosts, peeringhosts=config.peeringhosts, allowed_concurrent=16)
    print("\033[92m✅ Server peering initialized!\033[0m")

    # check hosts
    machine_count, cpus, mem = cm.collect_host_infos()

    # estimate resource use
    utilization = resource_estimate(bbox=config.bbox, shells=config.shells, groundstations=config.groundstations, cpus=cpus, mem=mem)

    if (utilization > 1.0):
        print("\033[93m⚠️  You should reduce your bounding box by at least", str(int((1 - 1.0/utilization) * 100))+"%", "for an optimal emulation.\033[0m")
    elif (utilization < 0.5):
        print("\033[93m⚠️  You can increase your bounding box by up to", str(int((1.0/utilization - 1) * 100))+"%.\033[0m")
    else:
        print("\033[92m✅ Your bounding box is well chosen!\033[0m")

    cm.init(db=config.database, db_host=config.dbhost, shell_count=len(config.shells), shells=config.shells)

    # initialize a constellation

    constellation_conn, mm_conn = mp.Pipe()

    animation_conn = None
    if config.animation:
        from celestial.animation import Animation

        animation_conn, animation_constellation_conn = mp.Pipe()

        animation = mp.Process(target=Animation, kwargs={
            "p": animation_constellation_conn
        })
        animation.start()

    db_conn = None
    if config.database:
        from celestial.database import Database

        db_conn, db_constellation_conn = mp.Pipe()

        database = mp.Process(target=Database, kwargs={
            "host": config.dbhost,
            "model": config.model,
            "shells": config.shells,
            "groundstations": config.groundstations,
            "constellation_conn": db_constellation_conn,
        })

        database.start()

    mm = mp.Process(target=MachineManager, kwargs={
        "shells": config.shells,
        "groundstations": config.groundstations,
        "constellation_conn": constellation_conn,
        "connection_manager": cm
    })

    mm.start()

    c = Constellation(model=config.model, shells=config.shells, groundstations=config.groundstations, mm_conn=mm_conn, interval=config.interval, animate=config.animation, bbox=config.bbox, animation_conn=animation_conn, database=config.database, db_conn=db_conn)

    c.update()

    timer = RepeatedTimer(config.interval, c.update)