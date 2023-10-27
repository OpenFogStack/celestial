#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Ben S. Kempton, Tobias Pfandzelter, The OpenFogStack Team.
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

import threading as td
import time
import multiprocessing as mp
from multiprocessing.connection import Connection as MultiprocessingConnection
import typing
import numpy as np

from .types import Model, ShellConfig, GroundstationConfig, BoundingBoxConfig, Path
from .shell import Shell
from .solver import Solver


class Constellation:
    def __init__(
        self,
        model: Model,
        shells: typing.List[ShellConfig],
        bbox: BoundingBoxConfig,
        groundstations: typing.List[GroundstationConfig],
        mm_conn: MultiprocessingConnection,
        interval: float,
        database: bool = False,
        db_conn: typing.Optional[MultiprocessingConnection] = None,
        animate: bool = False,
        animation_conn: typing.Optional[MultiprocessingConnection] = None,
        animate_only: bool = False,
    ):
        self.model = model

        self.shells: typing.List[Shell] = []

        self.mm_conn = mm_conn

        self.interval = interval

        # if a fixed time offset is ever needed, this is how to do it
        # START_TIME_OFFSET = 4 * 60 * 60
        # self.start_time = time.time() - START_TIME_OFFSET

        self.start_time = time.time()

        for shell in shells:
            solver: Solver

            if model == Model.SGP4:
                from .sgp4_solver import SGP4Solver

                solver = SGP4Solver(
                    planes=shell.planes,
                    sats=shell.sats,
                    altitude=shell.altitude,
                    inclination=shell.inclination,
                    arcOfAscendingNodes=shell.arcofascendingnodes,
                    eccentricity=shell.eccentricity,
                    sgp4params=shell.sgp4params,
                )

            elif model == Model.Kepler:
                from .kepler_solver import KeplerSolver

                solver = KeplerSolver(
                    planes=shell.planes,
                    sats=shell.sats,
                    altitude=shell.altitude,
                    inclination=shell.inclination,
                    arcOfAscendingNodes=shell.arcofascendingnodes,
                    eccentricity=shell.eccentricity,
                )

            s = Shell(
                planes=shell.planes,
                sats=shell.sats,
                altitude=shell.altitude,
                bbox=bbox,
                groundstations=groundstations,
                network=shell.networkparams,
                solver=solver,
                include_paths=not animate_only,
            )

            self.shells.append(s)

        sat_positions: typing.List[np.ndarray] = []  # type: ignore
        paths: typing.List[typing.List[Path]] = []
        gst_sat_paths: typing.List[typing.List[Path]] = []
        gst_paths: typing.List[typing.List[Path]] = []

        for s in self.shells:
            sat_positions.append(s.get_sat_positions())
            paths.append(s.get_paths())
            gst_sat_paths.append(s.get_gst_sat_paths())
            gst_paths.append(s.get_gst_paths())

        gst_positions: np.ndarray = self.shells[0].get_gst_positions()  # type: ignore

        self.animate = animate
        self.animate_only = animate_only

        if self.animate and animation_conn is not None:
            links = []
            gst_links = []

            for s in self.shells:
                links.append(s.get_links())
                gst_links.append(s.get_gst_links())

            self.animation_conn = animation_conn

            total_sats = []

            for s in self.shells:
                total_sats.append(len(s.get_sat_positions()))

            print("🌍 Constellation: sending information to animation...")
            self.animation_conn.send(
                [
                    "init",
                    {
                        "num_shells": len(self.shells),
                        "total_sats": total_sats,
                        "sat_positions": sat_positions,
                        "links": links,
                        "bbox": bbox,
                        "gst_positions": gst_positions,
                        "gst_links": gst_links,
                    },
                ]
            )

            print("🌍 Constellation: waiting for return from animation...")
            if not self.animation_conn.recv():
                exit(1)

            print("🌍 Constellation: animation ready!")

        if not self.animate_only:
            # send init information to machine manager
            self.mm_conn.send(["init", sat_positions, paths, gst_sat_paths, gst_paths])

            print("🌍 Constellation: waiting for return from machine manager...")
            if not self.mm_conn.recv():
                exit(1)

            print("🌍 Constellation: machine manager ready!")

        self.database = database
        if database:
            if db_conn is None:
                raise ValueError("database in use but db_conn unset")

            self.db_conn = db_conn
            self.db_conn.send(
                ["init", sat_positions, paths, gst_sat_paths, gst_paths, gst_positions]
            )

    def update(self) -> None:
        start_time = time.time()

        if self.animate:
            self.animation_conn.send(["time", int(time.time() - self.start_time)])

        sat_positions: typing.List[np.ndarray] = []  # type: ignore
        paths: typing.List[typing.List[Path]] = []
        gst_sat_paths: typing.List[typing.List[Path]] = []
        gst_paths: typing.List[typing.List[Path]] = []

        # this is actually super inefficient because we are calculating shells
        # in sequence instead of in parallel. there is probably a better way to
        # do it
        update_threads = []
        for i in range(len(self.shells)):
            update_threads.append(
                td.Thread(
                    target=self.shells[i].set_time,
                    args=(int(time.time() - self.start_time),),
                )
            )
            update_threads[i].start()

        for i in range(len(self.shells)):
            update_threads[i].join()
            sat_positions.append(self.shells[i].get_sat_positions())
            paths.append(self.shells[i].get_paths())
            gst_sat_paths.append(self.shells[i].get_gst_sat_paths())
            gst_paths.append(self.shells[i].get_gst_paths())

        if not self.animate_only:
            self.mm_conn.send([sat_positions, paths, gst_sat_paths, gst_paths])

        if not self.animate_only:
            ok = self.mm_conn.recv()

            if not ok:
                print("\033[91m❌ Did not get ok from machine manager!\033[0m")

        for i in range(len(self.shells)):
            gst_positions = self.shells[i].get_gst_positions()

            if self.animate:
                links = self.shells[i].get_links()
                gst_links = self.shells[i].get_gst_links()

                self.animation_conn.send(
                    [
                        "shell",
                        i,
                        {
                            "sat_positions": sat_positions[i],
                            "links": links,
                            "gst_positions": gst_positions,
                            "gst_links": gst_links,
                        },
                    ]
                )

            if self.database:
                self.db_conn.send(
                    [
                        i,
                        sat_positions[i],
                        paths[i],
                        gst_sat_paths[i],
                        gst_paths[i],
                        gst_positions,
                    ]
                )

        end_time = time.time()

        total = end_time - start_time

        if total > self.interval:
            print("\033[93m⚠️  Update took %.3fs\033[0m" % total)
        else:
            print("\033[92m✅ Update took %.3fs\033[0m" % total)
