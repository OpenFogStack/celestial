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

from concurrent import futures
from proto.celestial.celestial_pb2 import Shell
import traceback
import threading as td
import grpc
import urllib.parse
import typing

from multiprocessing.connection import Connection as MultiprocessingConnection

from .types import GroundstationConfig, Model, Path, ShellConfig
from proto.database import database_pb2, database_pb2_grpc

class Database(database_pb2_grpc.DatabaseServicer): # type: ignore
    def __init__(
        self,
        host: str,
        model: Model,
        shells: typing.List[ShellConfig],
        groundstations: typing.List[GroundstationConfig],
        constellation_conn: MultiprocessingConnection,
        ):

        # figure out port to bind to
        result = urllib.parse.urlsplit("//%s" % host)
        port = result.port
        if port is None:
            raise ValueError("could not determine port in %s" % host)

        self.initialized = False

        self.constellation_conn = constellation_conn

        self.model = model

        self.shells = shells

        self.groundstations = groundstations

        self.sat_positions: typing.List[typing.List[typing.Dict[str, typing.Union[float, bool]]]] = [[]] * len(self.shells)
        self.paths: typing.List[typing.List[Path]] = [[]] * len(self.shells)
        self.gst_sat_paths: typing.List[typing.List[Path]] = [[]] * len(self.shells)
        self.gst_paths: typing.List[typing.List[Path]] = [[]] * len(self.shells)
        self.gst_positions: typing.List[typing.List[typing.Dict[str, float]]] = [[]] * len(self.shells)

        self.control_thread = td.Thread(target=self.control_thread_handler)
        self.control_thread.start()

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        database_pb2_grpc.add_DatabaseServicer_to_server(
            self, server)
        server.add_insecure_port("0.0.0.0:%d" % port)
        server.start()
        server.wait_for_termination()


    def control_thread_handler(self) -> None:
        """
        Start a thread to deal with inter-process communications
        """
        while True:
            received_data = self.constellation_conn.recv()

            if received_data[0] == "init":

                for shell_no in range(len(self.shells)):
                    self.sat_positions[shell_no] = received_data[1][shell_no]
                    self.paths[shell_no] = received_data[2][shell_no]
                    self.gst_sat_paths[shell_no] = received_data[3][shell_no]
                    self.gst_paths[shell_no] = received_data[4][shell_no]
                    self.gst_positions[shell_no] = received_data[5]

                self.initialized = True

                continue

            if type(received_data) == list:

                shell_no = received_data[0]

                self.sat_positions[shell_no] = received_data[1]
                self.paths[shell_no] = received_data[2]
                self.gst_sat_paths[shell_no] = received_data[3]
                self.gst_paths[shell_no] = received_data[4]
                self.gst_positions[shell_no] = received_data[5]

    # all of the grpc api below

    def Constellation(self, request: database_pb2.Empty, context: grpc.ServicerContext) -> database_pb2.ConstellationInfo:

        ci = database_pb2.ConstellationInfo()

        if not self.initialized:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("not ready yet")
            return ci

        try:
            if self.model == Model.SGP4:
                ci.model = "SGP4"
            elif self.model == Model.Kepler:
                ci.model = "Kepler"

            ci.shells = len(self.shells)

            for g in self.groundstations:
                gsi = database_pb2.GroundStationId()
                gsi.name = g.name
                ci.groundstations.append(gsi)


        except:
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()

        return ci

    def Shell(self, request: database_pb2.ShellRequest, context: grpc.ServicerContext) -> database_pb2.ShellInfo:

        shell_no = request.shell

        si = database_pb2.ShellInfo()

        if not self.initialized:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("not ready yet")
            return si

        try:

            if shell_no >= len(self.shells):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("unknown shell: %d" % shell_no)
                return si

            si.planes = self.shells[shell_no].planes
            si.sats = self.shells[shell_no].sats
            si.altitude = self.shells[shell_no].altitude
            si.inclination = self.shells[shell_no].inclination
            si.arcofascendingsnodes = self.shells[shell_no].arcofascendingnodes
            si.eccentricity = self.shells[shell_no].eccentricity

            si.network.islpropagation = self.shells[shell_no].networkparams.islpropagation
            si.network.bandwidth = self.shells[shell_no].networkparams.bandwidth
            si.network.mincommsaltitude = self.shells[shell_no].networkparams.mincommsaltitude
            si.network.minelevation = self.shells[shell_no].networkparams.minelevation
            si.network.gstpropagation = self.shells[shell_no].networkparams.gstpropagation
            si.network.groundstationconnectiontype = self.shells[shell_no].networkparams.groundstationconnectiontype.value

            si.compute.vcpu = self.shells[shell_no].computeparams.vcpu_count
            si.compute.mem = self.shells[shell_no].computeparams.mem_size_mib
            si.compute.ht = self.shells[shell_no].computeparams.ht_enabled
            si.compute.disk = self.shells[shell_no].computeparams.disk_size_mib
            si.compute.kernel = self.shells[shell_no].computeparams.kernel
            si.compute.rootfs = self.shells[shell_no].computeparams.rootfs

            for s in range(len(self.sat_positions[shell_no])):
                if self.sat_positions[shell_no][s]["in_bbox"]:
                    activeSat = database_pb2.SatelliteId()
                    activeSat.shell = shell_no
                    activeSat.sat = s

                    si.activeSats.append(activeSat)

            if self.model == Model.SGP4:
                si.sgp4.starttime.FromDatetime(self.shells[shell_no].sgp4params.starttime)
                si.sgp4.model = self.shells[shell_no].sgp4params.model.value
                si.sgp4.mode = self.shells[shell_no].sgp4params.mode.value
                si.sgp4.bstar = self.shells[shell_no].sgp4params.bstar
                si.sgp4.ndot = self.shells[shell_no].sgp4params.ndot
                si.sgp4.argpo = self.shells[shell_no].sgp4params.argpo

        except:
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()

        return si

    def Satellite(self, request: database_pb2.SatelliteId, context: grpc.ServicerContext)-> database_pb2.SatelliteInfo:

        sat = request.sat
        shell = request.shell

        si = database_pb2.SatelliteInfo()

        if not self.initialized:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("not ready yet")
            return si

        try:

            if shell >= len(self.shells):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("unknown shell: %d" % shell)
                return si

            if sat >= len(self.sat_positions[shell]):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("unknown sat: %d" % sat)
                return si

            pos = self.sat_positions[shell][sat]

            si.position.x = float(pos["x"])
            si.position.y = float(pos["y"])
            si.position.z = float(pos["z"])

            si.active = bool(pos["in_bbox"])

            links = [x for x in self.paths[shell] if len(x.segments) == 1 and x.node_1 == sat or x.node_2 == sat]

            for l in links:
                sat2 = database_pb2.ConnectedSatInfo()
                sat2.sat.shell = shell
                if l.node_1 == sat:
                    sat2.sat.sat = l.node_2
                elif l.node_2 == sat:
                    sat2.sat.sat = l.node_1
                else: continue
                sat2.bandwidth = l.bandwidth
                sat2.delay = l.distance
                sat2.distance = l.distance
                si.connectedSats.append(sat2)

            gst_links = [x for x in self.gst_sat_paths[shell] if len(x.segments) == 1 and x.node_2 == sat]

            for l in gst_links:
                gst = database_pb2.GroundStationId()

                gst.name = self.groundstations[l.node_1].name

                si.connectedGST.append(gst)
        except:
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()

        return si

    def GroundStation(self, request: database_pb2.GroundStationId, context: grpc.ServicerContext) -> database_pb2.GroundStationInfo:

        gsi = database_pb2.GroundStationInfo()

        if not self.initialized:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("not ready yet")
            return gsi

        name = request.name

        try:

            index = 0
            for g in self.groundstations:
                if g.name == name:
                    break
                index += 1

            if index >= len(self.groundstations):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("unknown groundstation: %s" % name)
                return gsi

            pos = self.gst_positions[0][index]

            gsi.position.x = pos["x"]
            gsi.position.y = pos["y"]
            gsi.position.z = pos["z"]

            gsi.latitude = self.groundstations[index].lat
            gsi.longitude = self.groundstations[index].lng

            gsi.network.islpropagation = self.groundstations[index].networkparams.islpropagation
            gsi.network.bandwidth = self.groundstations[index].networkparams.bandwidth
            gsi.network.mincommsaltitude = self.groundstations[index].networkparams.mincommsaltitude
            gsi.network.minelevation = self.groundstations[index].networkparams.minelevation
            gsi.network.gstpropagation = self.groundstations[index].networkparams.gstpropagation
            gsi.network.groundstationconnectiontype = self.groundstations[index].networkparams.groundstationconnectiontype.value

            gsi.compute.vcpu = self.groundstations[index].computeparams.vcpu_count
            gsi.compute.mem = self.groundstations[index].computeparams.mem_size_mib
            gsi.compute.disk = self.groundstations[index].computeparams.disk_size_mib
            gsi.compute.ht = self.groundstations[index].computeparams.ht_enabled
            gsi.compute.kernel = self.groundstations[index].computeparams.kernel
            gsi.compute.rootfs = self.groundstations[index].computeparams.rootfs

            for shell_no in range(len(self.shells)):

                gst_links = [x for x in self.gst_sat_paths[shell_no] if len(x.segments) == 1 and x.node_1 == index]

                for l in gst_links:
                    sat = database_pb2.ConnectedSatInfo()
                    sat.sat.shell = shell_no
                    sat.sat.sat = l.node_2
                    sat.bandwidth = l.bandwidth
                    sat.delay = l.delay
                    sat.distance = l.distance

                    gsi.connectedSats.append(sat)


        except:
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()

        return gsi

    def Path(self, request: database_pb2.PathRequest, context: grpc.ServicerContext)-> database_pb2.PathInfo:

        pi = database_pb2.PathInfo()

        if not self.initialized:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("not ready yet")
            return pi

        ss = request.sourceShell
        ts = request.targetShell

        s = request.sourceSat
        t = request.targetSat

        if ss > ts:
            ss, ts = ts, ss
            s, t = t, s

        try:

            # case one: boths sats
            if ss >= 0 and ts >= 0:
                if ss != ts :
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("can't find path between different shells %d and %d" % (ss, ts))
                    return pi

                if ss >= len(self.sat_positions):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown shell: %d" % ss)
                    return pi

                if ts >= len(self.sat_positions):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown shell: %d" % ts)
                    return pi

                if s >= len(self.sat_positions[ss]):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown sat: %d in shell %d" % (s, ss))
                    return pi

                if t >= len(self.sat_positions[ts]):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown sat: %d in shell %d" % (t, ts))
                    return pi

                if not self.sat_positions[ss][s]["in_bbox"]:
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details("sourceSat %d in sourceShell %d is not active" % (s, ss))
                    return pi

                if not self.sat_positions[ts][t]["in_bbox"]:
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details("targetSat %d in targetShell %d is not active" % (t, ts))
                    return pi

                found = False
                for p in self.paths[ss]:
                    if ((p.node_1 == int(s) and p.node_2 == int(t)) or (p.node_2 == int(s) and p.node_1 == int(t))) and not p.node_2_is_gst and not p.node_1_is_gst:
                        path = database_pb2.Path()
                        path.distance = p.distance
                        path.delay = p.delay
                        path.bandwidth = p.bandwidth

                        for seg in p.segments:
                            segment = database_pb2.Segment()
                            segment.sourceShell = ss
                            segment.targetShell = ss
                            segment.sourceSat = seg.node_1
                            segment.targetSat = seg.node_2
                            segment.delay = seg.delay
                            segment.distance = seg.distance
                            segment.bandwidth = seg.bandwidth
                            path.segments.append(segment)

                        found = True
                        pi.paths.append(path)
                        break

                if not found:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("can't find path")
                    return pi

            # case two: one sat, one gst
            if ss < 0 and ts >= 0:
                found = False
                if s >= len(self.groundstations):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown ground station: %d" % s)
                    return pi

                if ts >= len(self.sat_positions):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown shell: %d" % ts)
                    return pi

                if t >= len(self.sat_positions[ts]):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown sat: %d in shell %d" % (t, ts))
                    return pi

                if not self.sat_positions[ts][t]["in_bbox"]:
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details("targetSat %d in targetShell %d is not active" % (t, ts))
                    return pi

                for p in self.gst_sat_paths[ts]:
                    if (p.node_2 == int(t) and not p.node_2_is_gst) or (p.node_1 == int(t) and not p.node_1_is_gst):
                        if (p.node_2 == int(s) and p.node_2_is_gst) or (p.node_1 == int(s) and p.node_1_is_gst):
                            path = database_pb2.Path()
                            path.distance = p.distance
                            path.delay = p.delay
                            path.bandwidth = p.bandwidth

                            first_leg = database_pb2.Segment()
                            first_leg.sourceShell = -1
                            first_leg.targetShell = ts
                            first_leg.sourceSat = p.segments[0].node_1
                            first_leg.targetSat = p.segments[0].node_2
                            first_leg.delay = p.segments[0].delay
                            first_leg.distance = p.segments[0].distance
                            first_leg.bandwidth = p.segments[0].bandwidth
                            path.segments.append(first_leg)

                            for seg in p.segments[1:]:
                                segment = database_pb2.Segment()
                                segment.sourceShell = ts
                                segment.targetShell = ts
                                segment.sourceSat = seg.node_1
                                segment.targetSat = seg.node_2
                                segment.delay = seg.delay
                                segment.distance = seg.distance
                                segment.bandwidth = seg.bandwidth
                                path.segments.append(segment)

                            found = True

                            pi.paths.append(path)
                            break

                if not found:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return pi

            # case three: both gst
            # only return the shortest
            if ss < 0 and ts < 0:
                if s >= len(self.groundstations):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown ground station: %d" % s)
                    return pi

                if t >= len(self.groundstations):
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("unknown ground station: %d" % t)
                    return pi

                for shell_no in range(len(self.shells)):
                    for p in self.gst_paths[shell_no]:
                        if ((p.node_1 == int(s) and p.node_2 == int(t)) or (p.node_1 == int(t) and p.node_2 == int(s))) and p.node_2_is_gst and p.node_1_is_gst:

                            path = database_pb2.Path()
                            path.distance = p.distance
                            path.delay = p.delay
                            path.bandwidth = p.bandwidth


                            first_leg = database_pb2.Segment()
                            first_leg.sourceShell = -1
                            first_leg.targetShell = ts
                            first_leg.sourceSat = p.segments[0].node_1
                            first_leg.targetSat = p.segments[0].node_2
                            first_leg.delay = p.segments[0].delay
                            first_leg.distance = p.segments[0].distance
                            first_leg.bandwidth = p.segments[0].bandwidth
                            path.segments.append(first_leg)

                            for seg in p.segments[1:len(p.segments)-1]:
                                segment = database_pb2.Segment()
                                segment.sourceShell = ts
                                segment.targetShell = ts
                                segment.sourceSat = seg.node_1
                                segment.targetSat = seg.node_2
                                segment.delay = seg.delay
                                segment.distance = seg.distance
                                segment.bandwidth = seg.bandwidth
                                path.segments.append(segment)

                            last_leg = database_pb2.Segment()
                            last_leg.sourceShell = ts
                            last_leg.targetShell = -1
                            last_leg.sourceSat = p.segments[-1].node_2
                            last_leg.targetSat = p.segments[-1].node_1
                            last_leg.delay = p.segments[-1].delay
                            last_leg.distance = p.segments[-1].distance
                            last_leg.bandwidth = p.segments[-1].bandwidth
                            path.segments.append(last_leg)

                            pi.paths.append(path)
                            break

                if len(pi.paths) == 0:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("can't find path")
                    return pi
        except:
            context.set_code(grpc.StatusCode.INTERNAL)
            traceback.print_exc()

        return pi
