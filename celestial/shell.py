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

import numpy as np
import math
import time as tm

import igraph as ig

import scipy.sparse
import scipy.sparse.csgraph

import typing

from .solver import Solver
from .types import BoundingBoxConfig, GroundstationConfig, GroundstationConnectionTypeConfig, NetworkParamsConfig, Path, Segment

import numba
import tqdm

EARTH_RADIUS = 6371000

SECONDS_PER_DAY = 86400

SATELLITE_DTYPE = np.dtype([
    ('ID', np.int16),             # ID number, unique, = array index
    ('plane_number', np.int16),   # which orbital plane is the satellite in?
    ('offset_number', np.int16),  # What satellite withen the plane?
    ('time_offset', np.float32),  # time offset for kepler ellipse solver
    ('in_bbox', bool),            # is sat in bbox?
    ('x', np.int32),              # x position in meters
    ('y', np.int32),              # y position in meters
    ('z', np.int32)])             # z position in meters

# The numpy data type used to store ground point data
# ground points have negative unique IDs
# positions are always calculated from the initial position
# to keep rounding error from compounding
GROUNDPOINT_DTYPE = np.dtype([
    ("ID", np.int16),      # ID number, unique, = array index
    ("conn_type", np.int32), # connection type of the ground station
    # 0 = all, 1 = one
    ("max_stg_range", np.int32), # max stg range of ground stations
    # depends on minelevation
    ("gstpropagation", np.float64), # max stg range of ground stations
    # depends on minelevation
    ("bandwidth", np.int32), # bandwidth this ground station supports
    ("init_x", np.int32),  # initial x position in meters
    ("init_y", np.int32),  # initial y position in meters
    ("init_z", np.int32),  # initial z position in meters
    ("x", np.int32),       # x position in meters
    ("y", np.int32),       # y position in meters
    ("z", np.int32)])      # z position in meters

# The numpy data type used to store link data
# link array size may have to be adjusted
# each index is 8 bytes
SAT_LINK_DTYPE = np.dtype([
    ("node_1", np.int16),     # an endpoint of the link
    ("node_2", np.int16),     # the other endpoint of the link
    ("distance", np.int32),   # distance of the link in meters
    ("delay", np.float64),    # delay of this link in ms
    ("active", bool)])        # can this link be active?

GST_SAT_LINK_DTYPE = np.dtype([
    ("gst", np.int16),        # ground station this link refers to
    ("sat", np.int16),        # satellite endpoint of the link
    ("distance", np.int32),   # distance of the link in meters
    ("delay", np.float64),    # delay of this link in ms
    ("bandwidth", np.int32)]) # bandwidth of this link

LINK_ARRAY_SIZE = 10000000  # 10 million indices = 80 megabyte array (huge)

class Shell():
    def __init__(
        self,
        planes: int,
        sats: int,
        altitude: float,
        bbox: BoundingBoxConfig,
        groundstations: typing.List[GroundstationConfig],
        network: NetworkParamsConfig,
        solver: Solver,
        include_paths: bool=True):

        self.profile_time = True

        self.current_time = 0

        self.include_paths = include_paths

        # constellation options
        self.number_of_planes = planes
        self.nodes_per_plane = sats
        self.total_sats = planes*sats

        # orbit options
        self.altitude = altitude

        self.semi_major_axis = float(self.altitude)*1000 + EARTH_RADIUS

        self.solver = solver

        # bounding box
        self.bbox = bbox

        # some network options
        self.min_communication_altitude: int = network.mincommsaltitude
        self.minelevation: float = network.minelevation
        self.islpropagation: float = network.islpropagation
        self.bandwidth: int = network.bandwidth

        self.satellites_array = np.empty(self.total_sats, dtype=SATELLITE_DTYPE)

        self.link_array_size = LINK_ARRAY_SIZE
        self.link_array = np.zeros(self.link_array_size, dtype=SAT_LINK_DTYPE)
        self.total_links = 0

        self.paths: typing.List[Path] = []

        self.total_gst = len(groundstations)
        self.gst_array = np.zeros(self.total_gst,dtype=GROUNDPOINT_DTYPE)

        self.gst_links_array_size = LINK_ARRAY_SIZE
        self.gst_links_array = np.zeros(self.gst_links_array_size, dtype=GST_SAT_LINK_DTYPE)
        self.total_gst_links = 0

        self.gst_sat_paths: typing.List[Path] = []
        self.gst_paths: typing.List[Path] = []


        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):

                unique_id = (plane*self.nodes_per_plane) + node
                self.satellites_array[unique_id]['ID'] = np.int16(unique_id)
                self.satellites_array[unique_id]['plane_number'] = np.int16(plane)
                self.satellites_array[unique_id]['offset_number'] = np.int16(node)

        self.satellites_array = self.solver.init_sat_array(self.satellites_array)

        neg_rotation_matrix = self.get_rotation_matrix(-0.0)

        for sat in self.satellites_array:
                sat['in_bbox'] =  self.is_in_bbox((sat['x'], sat['y'], sat['z']), neg_rotation_matrix)

        self.init_ground_stations(groundstations)

        self.initialize_network_design()


    def init_ground_stations(self, groundstations: typing.List[GroundstationConfig]) -> None:

        for i in range(len(groundstations)):

            g = groundstations[i]

            init_pos = [0.0, 0.0, 0.0]

            latitude = math.radians(g.lat)
            longitude = math.radians(g.lng)

            init_pos[0] = (EARTH_RADIUS + 100.0) * math.cos(latitude) * math.cos(longitude)
            init_pos[1] = (EARTH_RADIUS + 100.0) * math.cos(latitude) * math.sin(longitude)
            init_pos[2] = (EARTH_RADIUS + 100.0) * math.sin(latitude)

            temp = np.zeros(1, dtype=GROUNDPOINT_DTYPE)
            temp[0]["ID"] = np.int16(i)
            if g.networkparams.groundstationconnectiontype == GroundstationConnectionTypeConfig.All:
                temp[0]["conn_type"] = 0
            else:
                temp[0]["conn_type"] = 1
            temp[0]["max_stg_range"] = self.calculate_max_space_to_gst_distance(g.networkparams.minelevation)
            temp[0]["bandwidth"] = g.networkparams.bandwidth
            temp[0]["gstpropagation"] = g.networkparams.gstpropagation
            temp[0]["init_x"] = np.int32(init_pos[0])
            temp[0]["init_y"] = np.int32(init_pos[1])
            temp[0]["init_z"] = np.int32(init_pos[2])
            temp[0]["x"] = np.int32(init_pos[0])
            temp[0]["y"] = np.int32(init_pos[1])
            temp[0]["z"] = np.int32(init_pos[2])

            self.gst_array[i] = temp[0]

    def initialize_network_design(self) -> None:
        self.init_plus_grid_links(crosslink_interpolation=1)

        self.max_isl_range = self.calculate_max_ISL_distance()

        self.update_plus_grid_links()
        if self.include_paths:
            self.calculate_paths()

    def set_time(self, time: int) -> None:

        start_time = tm.time()

        self.current_time = int(time)

        self.satellites_array = self.solver.set_time(time, self.satellites_array)

        sat_pos_time = tm.time()

        if self.current_time == 0 or self.current_time % SECONDS_PER_DAY == 0:
            degrees_to_rotate = 0.0
        else:
            degrees_to_rotate = 360.0/(SECONDS_PER_DAY /
                                       (self.current_time % SECONDS_PER_DAY))

        rotation_matrix = self.get_rotation_matrix(degrees_to_rotate)
        neg_rotation_matrix = self.get_rotation_matrix(-degrees_to_rotate)

        in_bbox = 0

        for sat_id in range(len(self.satellites_array)):
            sat_is_in_bbox = self.is_in_bbox((self.satellites_array[sat_id]['x'], self.satellites_array[sat_id]['y'], self.satellites_array[sat_id]['z']), neg_rotation_matrix)
            if sat_is_in_bbox:
                in_bbox += 1

            self.satellites_array[sat_id]['in_bbox'] = sat_is_in_bbox

        sat_bbox_time = tm.time()

        for gst in self.gst_array:
            new_pos = np.dot(rotation_matrix, [gst['init_x'], gst['init_y'], gst['init_z']])
            gst['x'] = new_pos[0]
            gst['y'] = new_pos[1]
            gst['z'] = new_pos[2]

        gst_pos_time = tm.time()

        self.update_plus_grid_links()

        links_time = tm.time()

        if self.include_paths:
            self.calculate_paths()

        paths_time = tm.time()

        gst_paths_time = tm.time()

        if self.profile_time:
            print("⏱ Sat Pos: %.3f" % (sat_pos_time - start_time))
            print("⏱ Sat BBox: %.3f" % (sat_bbox_time - sat_pos_time))
            print("⏱ GST Pos: %.3f" % (gst_pos_time - sat_bbox_time))
            print("⏱ Links: %.3f" % (links_time - gst_pos_time))
            print("⏱ Paths: %.3f" % (paths_time - links_time))
            print("⏱ GST Paths: %.3f" % (gst_paths_time - paths_time))

    def get_rotation_matrix(self, degrees: float) -> np.ndarray:
        """
        Return the rotation matrix associated with counterclockwise rotation about
        the given axis by theta radians.

        Parameters
        ----------
        degrees : float
            The number of degrees to rotate

        """

        theta = math.radians(degrees)
        # earth"s z axis (eg a vector in the positive z direction)
        # EARTH_ROTATION_AXIS = [0, 0, 1]
        axis = np.asarray([0,0,1])
        axis = axis / math.sqrt(np.dot(axis, axis))
        a = math.cos(theta / 2.0)
        b, c, d = -axis * math.sin(theta / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array([
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

    def is_in_bbox(self, pos: typing.Tuple[float, float, float], rotation_matrix: np.ndarray) -> bool:
        # take cartesian coordinates and convert to lat long
        l = np.dot(rotation_matrix, np.array(pos))

        x = l[0]
        y = l[1]
        z = l[2]

        # convert that position into lat lon

        lat = np.degrees(np.arcsin(z/self.semi_major_axis))
        lon = np.degrees(np.arctan2(y, x))


        # check if lat long is in bounding box
        if self.bbox.lon2 < self.bbox.lon1:
            if lon < self.bbox.lon1 and lon > self.bbox.lon2:
                return False
        else:
            if lon < self.bbox.lon1 or lon > self.bbox.lon2:
                return False

        return bool(lat >= self.bbox.lat1 and lat <= self.bbox.lat2)

    def get_sat_positions(self) -> np.ndarray:
        """copies a sub array of only position data from
        satellite array

        Returns
        -------
        sat_positions : np array
            a copied sub array of the satellite array, that only contains positions data
        """

        sat_positions: np.ndarray = np.copy(self.satellites_array[["ID", "x", "y", "z", "in_bbox"]])

        return sat_positions

    def get_gst_positions(self) -> np.ndarray:
        """copies a sub array of only position data from
         groundpoint array

        Returns
        -------
        ground_positions : np array
            a copied sub array of the ground point array, that only contains positions
        """

        ground_positions: np.ndarray = np.copy(self.gst_array[["x", "y", "z"]])

        return ground_positions

    def get_links(self) -> np.ndarray:
        """copies a sub array of link data

        Returns
        -------
        links : np array
            contains all links
        """
        total_links = self.total_links
        links: np.ndarray = np.copy(self.link_array[:total_links])

        return links

    def get_gst_links(self) -> np.ndarray:
        """copies a sub array of gst link data

        Returns
        -------
        links : np array
            contains all links
        """
        total_gst_links = self.total_gst_links
        gst_links: np.ndarray = np.copy(self.gst_links_array[:total_gst_links])

        return gst_links

    def calculate_paths(self) -> None:
        """calculate the shortest paths between all active
        satellites

        Returns
        -------
        paths : np array
            contains all links including their total distance
        """

        # generate an array of active satellites
        # we also need to add satellites for our ground stations so we can be sure of shortest paths and everything
        targets = set([x["ID"] for x in self.satellites_array if x["in_bbox"]]).union([x["sat"] for x in self.gst_links_array[:self.total_gst_links]])

        # generate a network graph
        # start with sat links
        edges = [[e["node_1"], e["node_2"], e["distance"]] for e in self.link_array[:self.total_links] if e["node_1"] >= 0 and e["node_2"] >= 0]

        # gaussian sum of len(targets)-1 because we don't store stuff twice
        len_path_array = int( ( (len(targets)-1) * len(targets) ) /2 )

        paths: typing.List[Path] = []
        gst_paths: typing.List[Path] = []
        gst_sat_paths: typing.List[Path] = []

        if len(targets) > math.sqrt(self.total_sats):
            # use the more efficient floyd warshall algorithm for large graphs where we need to find everything

            # add gst links
            # simply add them add the end, so the first gst id is self.total_sats
            print("have %d sat edges" % len(edges))
            edges.extend([[e["gst"]+self.total_sats, e["sat"], e["distance"]] for e in self.gst_links_array[:self.total_gst_links]])
            print("have %d gst links" % self.total_gst_links)
            print("have %d total edges" % len(edges))
            # print("gst links:", self.gst_links_array[:self.total_gst_links])

            graph = np.zeros((self.total_sats+self.total_gst, self.total_sats+self.total_gst))

            # fill the graph with our edges
            for e in edges:
                graph[e[0], e[1]] = e[2]
                graph[e[1], e[0]] = e[2]

            # generate a list of all paths
            dist_matrix, predecessors = scipy.sparse.csgraph.floyd_warshall(csgraph=scipy.sparse.csr_matrix(graph), directed=False, return_predecessors=True)
            print("done with scipy\n")

            path_list: typing.List[typing.List[typing.Tuple[int, int, int, float]]] = []
            gst_sat_paths_list: typing.List[typing.Tuple[int, int, typing.List[typing.Tuple[int, int, int, float]]]] = []
            gst_paths_list: typing.List[typing.Tuple[int, int, typing.List[typing.Tuple[int, int, int, float]]]] = []

            known_paths: typing.Dict[int, typing.Dict[int, typing.List[typing.Tuple[int, int, int, float]]]] = {}

            targets = targets.union(range(self.total_sats, self.total_sats+self.total_gst))

            # def __segments(dist_matrix: np.ndarray, predecessors:)

            for node_1 in tqdm.tqdm(targets):
                for node_2 in targets:
                    if node_1 >= node_2:
                        continue

                    # find the shortest path segments from the predecessor matrix
                    a = node_1
                    b = node_1
                    sp: typing.List[typing.Tuple[int, int, int, float]] = []

                    while a != node_2:
                        # do we know the path from this node to the target already? great, use it
                        if a in known_paths and node_2 in known_paths[a]:
                            sp.extend(known_paths[a][node_2])
                            break
                        if node_2 in known_paths and a in known_paths[node_2]:
                            sp.extend([(x[1], x[0], x[2], x[3]) for x in reversed(known_paths[node_2][a])])
                            break

                        b = predecessors[node_2, a]

                        if b == -9999:
                            break

                        sp.append((a, b, dist_matrix[a, b], dist_matrix[a, b] * self.islpropagation))

                        if not node_1 in known_paths:
                            known_paths[node_1] = {}
                        known_paths[node_1][b] = sp
                        # print("adding %d on way from %d to %d" % (b, sat_1, sat_2))
                        a = b

                    if b == -9999:
                        continue

                    if not node_1 in known_paths:
                        known_paths[node_1] = {}
                    known_paths[node_1][node_2] = sp

                    # find out to which path list to append this
                    if node_1 < self.total_sats and node_2 < self.total_sats:
                        # this is a sat<->sat path
                        path_list.append(sp)
                        continue
                    elif node_1 < self.total_sats and node_2 >= self.total_sats:
                        # this is a sat<->gst path
                        # note that node_2 must come first, since it is the more important gst
                        gst_sat_paths_list.append((node_2, node_1, sp))

                        if node_1 == 10 and node_2 == 1 + self.total_sats:
                            print("found path:", sp)

                        continue
                    elif node_1 >= self.total_sats and node_2 >= self.total_sats:
                        # this is a gst<->gst path
                        gst_paths_list.append((node_1, node_2, sp))
                        continue
                    else:
                        # this cannot happen, as node_1 must be smaller than node_2
                        pass


            print("done creating tuples\n")

            paths = [Path(
                node_1=p[0][0],
                node_1_is_gst=False,
                node_2=p[-1][1],
                node_2_is_gst=False,
                delay=sum([x[3] for x in p]),
                distance=sum([x[2] for x in p]),
                bandwidth=self.bandwidth,
                segments=(Segment(
                                node_1=s[0] if s[0] < self.total_sats else s[0] - self.total_sats,
                                node_1_is_gst=s[0] >= self.total_sats,
                                node_2=s[1] if s[1] < self.total_sats else s[1] - self.total_sats,
                                node_2_is_gst=s[1] >= self.total_sats,
                                distance=s[2],
                                bandwidth=self.bandwidth,
                                delay=s[3],
                            ) for s in p)
            ) for p in tqdm.tqdm(path_list)]

            # and now get the gst_sat_paths
            gst_sat_paths = [Path(
                node_1=p[0]-self.total_sats,
                node_1_is_gst=True,
                node_2=p[1],
                node_2_is_gst=False,
                delay=sum([x[3] for x in p[2]]),
                distance=sum([x[2] for x in p[2]]),
                bandwidth=self.bandwidth,
                segments=(Segment(
                                node_1=s[0] if s[0] < self.total_sats else s[0] - self.total_sats,
                                node_1_is_gst=s[0] >= self.total_sats,
                                node_2=s[1] if s[1] < self.total_sats else s[1] - self.total_sats,
                                node_2_is_gst=s[1] >= self.total_sats,
                                distance=s[2],
                                bandwidth=self.bandwidth,
                                delay=s[3],
                            ) for s in p[2])
            ) for p in tqdm.tqdm(gst_sat_paths_list)]

            gst_paths = [Path(
                node_1=p[0]-self.total_sats,
                node_1_is_gst=True,
                node_2=p[1]-self.total_sats,
                node_2_is_gst=True,
                delay=sum([x[3] for x in p[2]]),
                distance=sum([x[2] for x in p[2]]),
                bandwidth=self.bandwidth,
                segments=(Segment(
                                node_1=s[0] if s[0] < self.total_sats else s[0] - self.total_sats,
                                node_1_is_gst=s[0] >= self.total_sats,
                                node_2=s[1] if s[1] < self.total_sats else s[1] - self.total_sats,
                                node_2_is_gst=s[1] >= self.total_sats,
                                distance=s[2],
                                bandwidth=self.bandwidth,
                                delay=s[3],
                            ) for s in p[2])
            ) for p in tqdm.tqdm(gst_paths_list)]

            print("getting gst path 91")
            print(vars(gst_paths[91]))
            print(len(list(gst_paths[91].segments)))
            for s in gst_paths[91].segments:
                print(vars(s))

            print("done doing actual paths\n")
        else:
            G = ig.Graph.TupleList(edges, weights=True)

            def __get_paths(sat_1: int) -> typing.List[Path]:

                consider_sat = G.vs.select([sat_2 for sat_2 in targets if sat_1 < sat_2])

                sp = G.get_shortest_paths(v=sat_1, to=consider_sat,     weights="weight")

                sat_paths = [
                    Path(
                        node_1= sat_1,
                        node_1_is_gst=False,
                        node_2=path[-1],
                        node_2_is_gst=False,
                        delay=0.0,
                        distance=0.0,
                        bandwidth=self.bandwidth,
                        segments=[Segment(
                            node_1=(G.es)()[eid].source,
                            node_1_is_gst=False,
                            node_2=(G.es)()[eid].target,
                            node_2_is_gst=False,
                            distance=(G.es)()[eid]["weight"],
                            bandwidth=self.bandwidth,
                            delay=(G.es)()[eid]["weight"] * self.islpropagation,
                        ) for eid in G.get_eids(path=path)],
                    ) for path in sp
                ]

                def __calc_distance(p: Path) -> Path:
                    p.distance = sum([x.distance for x in p.segments])
                    p.delay = p.distance * self.islpropagation

                    return p

                return list(map(__calc_distance, sat_paths))

            for sub_paths in map(__get_paths, tqdm.tqdm(targets)):
                paths.extend(sub_paths)

            print("done with igraph\n")

            # generate an array of active satellites
            active = [x for x in self.satellites_array if x["in_bbox"]]

            start_time = tm.time()

            # get all links a ground station has
            # thankfully these are appended into the list in order
            start, end = 0, 0
            while start < self.total_gst_links:

                source_gst = self.gst_links_array[start]["gst"]

                while end < self.total_gst_links and self.gst_links_array[end]["gst"] == source_gst:
                    end += 1

                for sat in active:

                    best_sat_path: typing.Optional[Path] = None

                    for sat_link in self.gst_links_array[start:end]:

                        first_leg = Segment(
                            node_1=source_gst,
                            node_1_is_gst=True,
                            node_2=sat_link["sat"],
                            node_2_is_gst=False,
                            distance=sat_link["distance"],
                            bandwidth=sat_link["bandwidth"],
                            delay=sat_link["delay"],
                        )

                        segments = [first_leg]
                        if sat_link["sat"] != sat["ID"]:
                            source, target = sat_link["sat"], sat["ID"]

                            if source > target:
                                source, target = target, source

                            # check our path list for that
                            filtered_path_list = [x for x in self.paths if x.node_1 == source and x.node_2 == target]

                            # there is no path? just continue
                            if len(filtered_path_list) == 0:
                                continue

                            # there is more than one path? this should never happen
                            assert len(filtered_path_list) <= 1

                            segments += filtered_path_list[0].segments

                        path = Path(
                            node_1=source_gst,
                            node_1_is_gst=True,
                            node_2=sat["ID"],
                            node_2_is_gst=False,
                            distance=sum(s.distance for s in segments),
                            bandwidth=min(s.bandwidth for s in segments),
                            delay=sum(s.delay for s in segments),
                            segments=segments,
                        )

                        if best_sat_path is None or path.delay < best_sat_path.delay or (path.delay == best_sat_path.delay and path.bandwidth > best_sat_path.bandwidth):
                            best_sat_path = path

                    if best_sat_path is not None:
                        gst_sat_paths.append(best_sat_path)

                start = end

            gst_sat_time = tm.time()

            # get all links a ground station has
            # thankfully these are appended into the list in order
            outer_start, outer_end = 0, 0
            while outer_start < self.total_gst_links:

                source_gst = self.gst_links_array[outer_start]["gst"]
                while outer_end < self.total_gst_links and self.gst_links_array[outer_end]["gst"] == source_gst:
                    outer_end += 1

                #do stuff

                inner_start, inner_end = outer_end, outer_end

                while inner_start < self.total_gst_links:

                    target_gst = self.gst_links_array[inner_start]["gst"]
                    while inner_end < self.total_gst_links and self.gst_links_array[inner_end]["gst"] == target_gst:
                        inner_end += 1

                    best_path: typing.Optional[Path] = None

                    for l1 in self.gst_links_array[outer_start:outer_end]:

                        first_leg = Segment(
                            node_1=l1["gst"],
                            node_1_is_gst=True,
                            node_2=l1["sat"],
                            node_2_is_gst=False,
                            distance=l1["distance"],
                            bandwidth=l1["bandwidth"],
                            delay=l1["delay"],
                        )

                        for l2 in self.gst_links_array[inner_start:inner_end]:

                            last_leg = Segment(
                                node_1=l2["gst"],
                                node_1_is_gst=True,
                                node_2=l2["sat"],
                                node_2_is_gst=False,
                                distance=l2["distance"],
                                bandwidth=l2["bandwidth"],
                                delay=l2["delay"],
                            )

                            segments = [first_leg]
                            if l1["sat"] != l2["sat"]:

                                source, target = l1["sat"], l2["sat"]

                                if source > target:
                                    source, target = target, source

                                # check our path list for that
                                filtered_path_list = [x for x in self.paths if x.node_1 == source and x.node_2 == target]

                                # there is no path? just continue
                                if len(filtered_path_list) == 0:
                                    continue

                                # there is more than one path? this should never happen
                                assert len(filtered_path_list) <= 1

                                segments += filtered_path_list[0].segments

                            segments += [last_leg]

                            path = Path(
                                node_1=l1["gst"],
                                node_1_is_gst=True,
                                node_2=l2["gst"],
                                node_2_is_gst=True,
                                distance=sum(s.distance for s in segments),
                                bandwidth=min(s.bandwidth for s in segments),
                                delay=sum(s.delay for s in segments),
                                segments=segments,
                            )

                            if best_path is None or path.delay < best_path.delay or (path.delay == best_path.delay and path.bandwidth > best_path.bandwidth):
                                best_path = path

                    if best_path is not None:
                        gst_paths.append(best_path)

                    inner_start = inner_end

                outer_start = outer_end

            gst_time = tm.time()

            if self.profile_time:
                print("⏱ GST SAT Paths: %.3f" % (gst_sat_time - start_time))
                print("⏱ GST Paths %.3f" % (gst_time - gst_sat_time))

        print("found %d paths" % len(paths))
        print("expected %d paths" % len_path_array)
        assert len(paths) == len_path_array

        self.paths = paths
        print("found %d gst_paths" % len(gst_paths))
        self.gst_paths = gst_paths
        print("found %d gst_sat_paths" % len(gst_sat_paths))
        self.gst_sat_paths = gst_sat_paths

    def get_paths(self) -> typing.List[Path]:
        return self.paths

    def get_gst_paths(self) -> typing.List[Path]:
        """
        Returns
        -------
        paths : np array
            contains all links including their total distance
        """
        return self.gst_paths

    def get_gst_sat_paths(self) -> typing.List[Path]:
        """
        Returns
        -------
        paths : np array
            contains all links including their total distance
        """
        return self.gst_sat_paths

    def calculate_max_ISL_distance(self) -> int:
        """
        ues some trig to calculate the max coms range between satellites
        based on some minium communications altitude

        Returns
        -------
        max distance : int
            max distance in meters

        """

        c = EARTH_RADIUS + self.min_communication_altitude
        b = self.semi_major_axis
        B = math.radians(90)
        C = math.asin((c * math.sin(B)) / b)
        A = math.radians(180) - B - C
        a = (b * math.sin(A)) / math.sin(B)
        return int(a * 2)

    def calculate_max_space_to_gst_distance(self, min_elevation: int) -> int:
        """
        Return max satellite to ground coms distance

        Uses some trig to calculate the max space to ground communications
        distance given a field of view for groundstations defined by an
        minimum elevation angle above the horizon.
        Uses a circle & line segment intercept calculation.

        Parameters
        ----------
        min_elevation : int
            min elevation in degrees, range: 0<val<90

        Returns
        -------
        max distance : int
            max coms distance in meters

        """

        # TODO
        # make a drawing explaining this

        # note from Tobias: this seems awfully complicated

        full_line = False
        tangent_tol = 1e-9

        # point 1 of line segment, representing groundstation
        p1x, p1y = (0, EARTH_RADIUS)

        # point 2 of line segment, representing really far point
        # at min_elevation slope from point 1
        slope = math.tan(math.radians(min_elevation))
        run = 384748000  # meters, sma of moon
        rise = slope * run + EARTH_RADIUS
        p2x, p2y = (run, rise)

        # center of orbit circle = earth center
        # radius = orbit radius
        cx, cy = (0, 0)
        circle_radius = self.semi_major_axis

        (x1, y1), (x2, y2) = (p1x - cx, p1y - cy), (p2x - cx, p2y - cy)
        dx, dy = (x2 - x1), (y2 - y1)
        dr = (dx ** 2 + dy ** 2)**.5
        big_d = x1 * y2 - x2 * y1
        discriminant = circle_radius ** 2 * dr ** 2 - big_d ** 2

        if discriminant < 0:  # No intersection between circle and line
            print("❌ ERROR! problem with calculateMaxSpaceToGstDistance, no intersection")
            return 0
        else:  # There may be 0, 1, or 2 intersections with the segment
            intersections = [
                (cx+(big_d*dy+sign*(-1 if dy < 0 else 1)*dx*discriminant**.5)/dr**2,
                 cy + (-big_d * dx + sign * abs(dy) * discriminant**.5) / dr ** 2)
                for sign in ((1, -1) if dy < 0 else (-1, 1))]

            # This makes sure the order along the segment is correct
            if not full_line:
                # Filter out intersections that do not fall within the segment
                fraction_along_segment = [(xi - p1x) / dx if abs(dx) > abs(dy)
                                          else (yi - p1y) / dy for xi, yi in intersections]

                intersections = [pt for pt, frac in
                                 zip(intersections, fraction_along_segment)
                                 if 0 <= frac <= 1]

            if len(intersections) == 2 and abs(discriminant) <= tangent_tol:
                # If line is tangent to circle, return just one point
                print("❌ ERROR!, got 2 intersections, expecting 1")
                return 0
            else:
                ints_lst = intersections

        # assuming 2 intersections were found...
        for i in ints_lst:
            if i[1] < 0:
                continue
            else:
                # calculate dist to this intersection
                d = math.sqrt(
                    math.pow(i[0]-p1x, 2) +
                    math.pow(i[1]-p1y, 2)
                )
                return int(d)

        return 0

    def init_plus_grid_links(self, crosslink_interpolation: int = 1) -> None:
        self.number_of_isl_links = 0

        temp = self.numba_init_plus_grid_links(
            self.link_array,
            self.link_array_size,
            self.number_of_planes,
            self.nodes_per_plane,
            crosslink_interpolation=crosslink_interpolation)
        if temp is not None:
            self.number_of_isl_links = temp[0]
            self.total_links = self.number_of_isl_links

    @staticmethod
    @numba.njit # type: ignore
    def numba_init_plus_grid_links(
            link_array: np.ndarray,
            link_array_size: int,
            number_of_planes: int,
            nodes_per_plane: int,
            crosslink_interpolation: int = 1) -> typing.Tuple[int]:

        link_idx = 0

        # add the intra-plane links
        for plane in range(number_of_planes):
            for node in range(nodes_per_plane):
                node_1 = node + (plane * nodes_per_plane)
                if node == nodes_per_plane - 1:
                    node_2 = plane * nodes_per_plane
                else:
                    node_2 = node + (plane * nodes_per_plane) + 1

                if link_idx < link_array_size - 1:
                    link_array[link_idx]['node_1'] = np.int16(node_1)
                    link_array[link_idx]['node_2'] = np.int16(node_2)
                    link_idx = link_idx + 1
                else:
                    print('❌ ERROR! ran out of room in the link array for intra-plane links')
                    return (0,)

        # add the cross-plane links
        for plane in range(number_of_planes):
            if plane == number_of_planes - 1:
                plane2 = 0
            else:
                plane2 = plane + 1
            for node in range(nodes_per_plane):
                node_1 = node + (plane * nodes_per_plane)
                node_2 = node + (plane2 * nodes_per_plane)
                if link_idx < link_array_size - 1:
                    if (node_1 + 1) % crosslink_interpolation == 0:
                        link_array[link_idx]['node_1'] = np.int16(node_1)
                        link_array[link_idx]['node_2'] = np.int16(node_2)
                        link_idx = link_idx + 1
                else:
                    print('❌ ERROR! ran out of room in the link array for cross-plane links')
                    return (0,)

        number_of_isl_links = link_idx

        return (number_of_isl_links,)

    def update_plus_grid_links(self) -> None:
        """
        connect satellites in a +grid network

        Parameters
        ----------
        initialize : bool
            Because PlusGrid ISL are static, they only need to be generated once,
            If initialize=False, only update link distances, do not regererate
        crosslink_interpolation : int
            This value is used to make only 1 out of every crosslink_interpolation
            satellites able to have crosslinks. For example, with a interpolation
            value of '2', only every other satellite will have crosslinks, the rest
            will have only intra-plane links

        """

        temp = self.numba_update_plus_grid_links(
            total_sats=self.total_sats,
            satellites_array=self.satellites_array,
            link_array=self.link_array,
            link_array_size=self.link_array_size,
            number_of_isl_links=self.number_of_isl_links,
            gst_array=self.gst_array,
            gst_links_array=self.gst_links_array,
            bandwidth=self.bandwidth,
            islpropagation=self.islpropagation,
            max_isl_range=self.max_isl_range)

        self.total_gst_links = temp[0]

    @staticmethod
    @numba.njit # type: ignore
    def numba_update_plus_grid_links(
            total_sats: int,
            satellites_array: np.ndarray,
            link_array: np.ndarray,
            link_array_size: int,
            number_of_isl_links: int,
            gst_array: np.ndarray,
            gst_links_array: np.ndarray,
            bandwidth: int,
            islpropagation: float,
            max_isl_range: int = (2**31)-1) -> typing.Tuple[int]:

        for isl_idx in range(number_of_isl_links):
            sat_1 = link_array[isl_idx]['node_1']
            sat_2 = link_array[isl_idx]['node_2']
            d = int(math.sqrt(
                math.pow(satellites_array[sat_1]['x'] - satellites_array[sat_2]['x'], 2) +
                math.pow(satellites_array[sat_1]['y'] - satellites_array[sat_2]['y'], 2) +
                math.pow(satellites_array[sat_1]['z'] - satellites_array[sat_2]['z'], 2)))
            link_array[isl_idx]['active'] = (d <= max_isl_range)
            link_array[isl_idx]['distance'] = np.int32(d)
            link_array[isl_idx]['delay'] = np.float64(d) * np.float64(islpropagation)

        gst_link_id = 0
        for gst in gst_array:

            shortest_d = np.inf

            for sat_idx in range(total_sats):
                # only proceed if sat is active
                #if not satellites_array[sat_idx]["in_bbox"]:
                #    continue

                # calculate distance
                d = int(math.sqrt(
                    math.pow(satellites_array[sat_idx]["x"] - gst["x"], 2) +
                    math.pow(satellites_array[sat_idx]["y"] - gst["y"], 2) +
                    math.pow(satellites_array[sat_idx]["z"] - gst["z"], 2)))

                # decide if link is valid or not
                if d <= gst["max_stg_range"]:

                    if gst_link_id < link_array_size - 1:
                        # if we allow only one link and the one we found is shorter than the old one overwrite the old one
                        if gst["conn_type"] == 1:
                            if d > shortest_d:
                                continue

                            # but can't overwrite if we're haven't written anything yet
                            if shortest_d != np.inf:
                                gst_link_id -= 1

                            shortest_d = d

                        gst_id = gst["ID"]
                        sat_id = satellites_array[sat_idx]["ID"]

                        gst_links_array[gst_link_id]["gst"] = gst_id
                        gst_links_array[gst_link_id]["sat"] = sat_id
                        gst_links_array[gst_link_id]["distance"] = np.int32(d)
                        gst_links_array[gst_link_id]["delay"] = np.float64(d) * np.float64(gst["gstpropagation"])
                        gst_links_array[gst_link_id]["bandwidth"] = min(np.int32(bandwidth), gst["bandwidth"])

                        gst_link_id = gst_link_id + 1

                    else:
                        print("❌ ERROR! ran out of room in the link array")
                        return (0,)

        total_gst_links = gst_link_id

        return (total_gst_links,)
