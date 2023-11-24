import math
import numpy as np
import numpy.typing as npt
import scipy.sparse

import typing

import satgen.config
import satgen.sgp4_solver
import satgen.types

### CONSTANTS ###
EARTH_RADIUS = 6_371_000  # meters
SECONDS_PER_DAY = 86_400
MIN_COMMS_ALTITUDE = 80_000  # meters, height of thermosphere
ISL_PROPAGATION = 3.336e-6  # ms/m, about 1/c
CROSSLINK_INTERPOLATION = 1

### DTYPES ###
SATELLITE_DTYPE = np.dtype(
    [
        ("ID", np.int16),  # ID number, unique, = array index
        ("plane_number", np.int16),  # which orbital plane is the satellite in?
        ("offset_number", np.int16),  # What satellite withen the plane?
        ("in_bbox", np.bool_),  # is sat in bbox?
        ("x", np.int32),  # x position in meters
        ("y", np.int32),  # y position in meters
        ("z", np.int32),  # z position in meters
    ]
)

# The numpy data type used to store ground point data
# ground points have negative unique IDs
# positions are always calculated from the initial position
# to keep rounding error from compounding
GROUNDPOINT_DTYPE = np.dtype(
    [
        ("ID", np.int16),  # ID number, unique, = array index
        ("conn_type", np.int32),  # connection type of the ground station
        # 0 = all, 1 = one
        ("max_stg_range", np.int32),  # max stg range of ground stations
        # depends on minelevation
        ("bandwidth", np.int32),  # bandwidth this ground station supports in Kbps
        ("init_x", np.int32),  # initial x position in meters
        ("init_y", np.int32),  # initial y position in meters
        ("init_z", np.int32),  # initial z position in meters
        ("x", np.int32),  # x position in meters
        ("y", np.int32),  # y position in meters
        ("z", np.int32),  # z position in meters
        ("name", str),  # name of the ground station
    ]
)

# The numpy data type used to store link data
# each index is 8 bytes
SAT_LINK_DTYPE = np.dtype(
    [
        ("node_1", np.int16),  # an endpoint of the link
        ("node_2", np.int16),  # the other endpoint of the link
        ("active", np.bool_),  # can this link be active?
        ("distance", np.int32),  # distance of the link in meters
    ]
)

GST_SAT_LINK_DTYPE = np.dtype(
    [
        ("gst", np.int16),  # ground station this link refers to
        ("sat", np.int16),  # satellite endpoint of the link
        ("distance", np.float64),  # distance of the link in meterss
    ]
)

PATH_DTYPE = np.dtype(
    [
        ("node_1", np.int16),  # an endpoint of the link
        ("node_2", np.int16),  # the other endpoint of the link
        ("next", np.int16),  # the next node in the path
        ("active", np.bool_),  # can this link be active?
        ("bandwidth", np.int32),  # distance of the link in meters
        ("delay", np.float64),  # delay of this link in ms
    ]
)


class Shell:
    def __init__(
        self,
        shell_identifier: int,
        planes: int,
        sats: int,
        altitude: float,
        inclination: float,
        arc_of_ascending_nodes: float,
        eccentricity: float,
        isl_bandwidth: int,
        bbox: satgen.config.BoundingBox,
        ground_stations: typing.List[satgen.config.GroundStation],
    ):
        self.shell_identifier = shell_identifier

        self.current_timestep: satgen.types.timestep = 0

        self.number_of_planes = planes
        self.nodes_per_plane = sats
        self.total_sats = planes * sats

        LINK_ARRAY_SIZE = (self.total_sats * 4) + (len(ground_stations) * 16)
        PATH_ARRAY_SIZE = (self.total_sats + len(ground_stations)) ** 2

        # orbit options
        self.altitude = altitude

        self.semi_major_axis = float(self.altitude) * 1000 + EARTH_RADIUS

        # bounding box
        self.bbox = bbox

        self.isl_bandwidth = isl_bandwidth

        self.satellites_array = np.empty(self.total_sats, dtype=SATELLITE_DTYPE)

        self.link_array = np.zeros(LINK_ARRAY_SIZE, dtype=SAT_LINK_DTYPE)

        self.total_links = 0

        self.total_gst = len(ground_stations)

        self.gst_array = np.zeros(self.total_gst, dtype=GROUNDPOINT_DTYPE)

        self.gst_links_array = np.zeros(LINK_ARRAY_SIZE, dtype=GST_SAT_LINK_DTYPE)

        self.total_gst_links = 0

        self.path_array = np.zeros(PATH_ARRAY_SIZE, dtype=SAT_LINK_DTYPE)

        # init nodes
        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):
                unique_id = (plane * self.nodes_per_plane) + node
                self.satellites_array[unique_id]["ID"] = np.int16(unique_id)
                self.satellites_array[unique_id]["plane_number"] = np.int16(plane)
                self.satellites_array[unique_id]["offset_number"] = np.int16(node)

        self.solver = satgen.sgp4_solver.SGP4Solver(
            planes=self.number_of_planes,
            sats=self.nodes_per_plane,
            altitude=self.altitude,
            inclination=inclination,
            arc_of_ascending_nodes=arc_of_ascending_nodes,
            eccentricity=eccentricity,
        )

        self.satellites_array = self.solver.init_sat_array(self.satellites_array)

        neg_rotation_matrix = self.get_rotation_matrix(-0.0)

        for sat in self.satellites_array:
            sat["in_bbox"] = self.is_in_bbox(
                (sat["x"], sat["y"], sat["z"]), neg_rotation_matrix
            )

        self.init_ground_stations(ground_stations)

        self.init_plus_grid_links()

        self.max_isl_range = self.calculate_max_ISL_distance()

    def step(self, time: satgen.types.timestep) -> None:
        self.current_time = int(time)

        self.satellites_array = self.solver.set_time(time, self.satellites_array)

        degrees_to_rotate = 360.0 * (self.current_time / SECONDS_PER_DAY)

        rotation_matrix = self.get_rotation_matrix(degrees_to_rotate)
        neg_rotation_matrix = self.get_rotation_matrix(-degrees_to_rotate)

        for sat_id in range(len(self.satellites_array)):
            sat_is_in_bbox = self.is_in_bbox(
                (
                    self.satellites_array[sat_id]["x"],
                    self.satellites_array[sat_id]["y"],
                    self.satellites_array[sat_id]["z"],
                ),  # type: ignore
                neg_rotation_matrix,
            )

            self.satellites_array[sat_id]["in_bbox"] = sat_is_in_bbox

        for gst in self.gst_array:
            new_pos = np.dot(
                rotation_matrix, [gst["init_x"], gst["init_y"], gst["init_z"]]
            )
            gst["x"] = new_pos[0]
            gst["y"] = new_pos[1]
            gst["z"] = new_pos[2]

        self.update_plus_grid_links()

        self.update_paths()

    def get_sat_nodes(self) -> satgen.types.MachineState:
        sat_nodes: satgen.types.MachineState = {}

        for sat in self.satellites_array:
            sat_nodes[satgen.types.MachineID(group=1, id=sat["ID"])] = (
                satgen.types.VMState.ACTIVE
                if sat["in_bbox"]
                else satgen.types.VMState.STOPPED
            )

        return sat_nodes

    def get_sat_links(
        self
    ) -> typing.Dict[
        satgen.types.MachineID,
        typing.Dict[satgen.types.MachineID, satgen.types.Link],
    ]:
        links: typing.Dict[
            satgen.types.MachineID,
            typing.Dict[satgen.types.MachineID, satgen.types.Link],
        ] = {}

        for p in self.path_array[: self.total_paths]:
            if p["node_1"] < 0:
                continue

            n1 = satgen.types.MachineID(group=self.shell_identifier, id=p["node_1"])

            if n1 not in links:
                links[n1] = {}

            n2 = satgen.types.MachineID(group=self.shell_identifier, id=p["node_2"])

            links[n1][n2] = satgen.types.Link(
                latency=p["delay"],
                bandwidth=p["bandwidth"],
                blocked=not p["active"],
                next_hop=satgen.types.MachineID(
                    group=self.shell_identifier, id=p["next"]
                ),
            )

        return links

    def get_gst_links(
        self
    ) -> typing.Dict[
        satgen.types.MachineID,
        typing.Dict[satgen.types.MachineID, satgen.types.Link],
    ]:
        links: typing.Dict[
            satgen.types.MachineID,
            typing.Dict[satgen.types.MachineID, satgen.types.Link],
        ] = {}

        for p in self.path_array[: self.total_paths]:
            # skip sat nodes
            if p["node_1"] >= 0:
                continue

            n1 = satgen.types.MachineID(
                group=0, id=-p["node_1"], name=self.gst_array[-p["node_1"]]["name"]
            )

            if n1 not in links:
                links[n1] = {}

            n2 = (
                satgen.types.MachineID(group=self.shell_identifier, id=p["node_2"])
                if p["node_2"] >= 0
                else satgen.types.MachineID(
                    group=0, id=-p["node_2"], name=self.gst_array[-p["node_2"]]["name"]
                )
            )

            links[n1][n2] = satgen.types.Link(
                latency=p["delay"],
                bandwidth=p["bandwidth"],
                blocked=not p["active"],
                next_hop=satgen.types.MachineID(
                    group=self.shell_identifier, id=p["next"]
                ),
            )

        return links

    def get_rotation_matrix(self, degrees: float) -> npt.NDArray[np.float64]:
        theta = math.radians(degrees)
        # earth's z axis (eg a vector in the positive z direction)
        # EARTH_ROTATION_AXIS = [0, 0, 1]
        axis: npt.NDArray[np.float64] = np.asarray([0, 0, 1])
        axis = axis / math.sqrt(np.dot(axis, axis))
        a = math.cos(theta / 2.0)
        b, c, d = -axis * math.sin(theta / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array(
            [
                [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
            ],
        )

    def is_in_bbox(
        self,
        pos: typing.Tuple[np.int32, np.int32, np.int32],
        rotation_matrix: npt.NDArray[np.float64],
    ) -> np.bool_:
        # take cartesian coordinates and convert to lat long
        l = np.dot(rotation_matrix, np.array(pos))

        x = l[0]
        y = l[1]
        z = l[2]

        # convert that position into lat lon

        div = z / self.semi_major_axis
        if np.abs(div) > 1:
            lat = np.degrees(np.arccos(1 if div > 0 else -1))
        else:
            lat = np.degrees(np.arcsin(z / self.semi_major_axis))
        lon = np.degrees(np.arctan2(y, x))

        # check if lat long is in bounding box
        if self.bbox.lon2 < self.bbox.lon1:
            if lon < self.bbox.lon1 and lon > self.bbox.lon2:
                return np.bool_(False)
        else:
            if lon < self.bbox.lon1 or lon > self.bbox.lon2:
                return np.bool_(False)

        return np.bool_(lat >= self.bbox.lat1 and lat <= self.bbox.lat2)

    def init_ground_stations(
        self, groundstations: typing.List[satgen.config.GroundStation]
    ) -> None:
        for i in range(len(groundstations)):
            g = groundstations[i]

            init_pos = [0.0, 0.0, 0.0]

            latitude = math.radians(g.lat)
            longitude = math.radians(g.lng)

            init_pos[0] = (
                (EARTH_RADIUS + 100.0) * math.cos(latitude) * math.cos(longitude)
            )
            init_pos[1] = (
                (EARTH_RADIUS + 100.0) * math.cos(latitude) * math.sin(longitude)
            )
            init_pos[2] = (EARTH_RADIUS + 100.0) * math.sin(latitude)

            temp: npt.NDArray[GROUNDPOINT_DTYPE] = np.zeros(1, dtype=GROUNDPOINT_DTYPE)

            temp[0]["ID"] = np.int16(i)

            temp[0]["conn_type"] = satgen.config.GroundStationConnectionType.ALL

            temp[0]["max_stg_range"] = self.calculate_max_space_to_gst_distance(
                g.min_elevation
            )

            temp[0]["bandwidth"] = g.gts_bandwidth
            temp[0]["init_x"] = np.int32(init_pos[0])
            temp[0]["init_y"] = np.int32(init_pos[1])
            temp[0]["init_z"] = np.int32(init_pos[2])
            temp[0]["x"] = np.int32(init_pos[0])
            temp[0]["y"] = np.int32(init_pos[1])
            temp[0]["z"] = np.int32(init_pos[2])

            temp[0]["name"] = g.name

            self.gst_array[i] = temp[0]

    def calculate_max_ISL_distance(self) -> int:
        c = EARTH_RADIUS + MIN_COMMS_ALTITUDE
        b = self.semi_major_axis
        B = math.radians(90)
        C = math.asin((c * math.sin(B)) / b)
        A = math.radians(180) - B - C
        a = (b * math.sin(A)) / math.sin(B)
        return int(a * 2)

    def calculate_max_space_to_gst_distance(self, min_elevation: float) -> int:
        # we're just going to assume a spherical earth

        if min_elevation < 0 or min_elevation > 90:
            print("ERROR! min_elevation must be between 0 and 90 degrees")
            return 0

        # calculate triangle using law of sines
        a = self.semi_major_axis
        b = EARTH_RADIUS

        alpha = math.radians(min_elevation + 90)

        beta = math.asin(math.sin(alpha) * b / a)

        c = math.sin(math.radians(180) - alpha - beta) * a / math.sin(alpha)
        return int(c)

    def init_plus_grid_links(self) -> None:
        self.number_of_isl_links = 0

        temp = self.numba_init_plus_grid_links(
            self.link_array,
            self.number_of_planes,
            self.nodes_per_plane,
        )
        if temp is not None:
            self.number_of_isl_links = temp[0]
            self.total_links = self.number_of_isl_links

    @staticmethod
    @numba.njit  # type: ignore
    def numba_init_plus_grid_links(
        link_array: np.ndarray,  # type: ignore
        number_of_planes: int,
        nodes_per_plane: int,
    ) -> typing.Tuple[int]:
        link_idx = 0

        # add the intra-plane links
        for plane in range(number_of_planes):
            for node in range(nodes_per_plane):
                node_1 = node + (plane * nodes_per_plane)
                if node == nodes_per_plane - 1:
                    node_2 = plane * nodes_per_plane
                else:
                    node_2 = node + (plane * nodes_per_plane) + 1

            link_array[link_idx]["node_1"] = np.int16(node_1)
            link_array[link_idx]["node_2"] = np.int16(node_2)
            link_idx = link_idx + 1

        # add the cross-plane links
        for plane in range(number_of_planes):
            if plane == number_of_planes - 1:
                plane2 = 0
            else:
                plane2 = plane + 1
            for node in range(nodes_per_plane):
                node_1 = node + (plane * nodes_per_plane)
                node_2 = node + (plane2 * nodes_per_plane)

                if (node_1 + 1) % CROSSLINK_INTERPOLATION == 0:
                    link_array[link_idx]["node_1"] = np.int16(node_1)
                    link_array[link_idx]["node_2"] = np.int16(node_2)
                    link_idx = link_idx + 1

        number_of_isl_links = link_idx

        return (number_of_isl_links,)

    def update_plus_grid_links(self) -> None:
        temp = self.numba_update_plus_grid_links(
            total_sats=self.total_sats,
            satellites_array=self.satellites_array,
            link_array=self.link_array,
            number_of_isl_links=self.number_of_isl_links,
            gst_array=self.gst_array,
            gst_links_array=self.gst_links_array,
            max_isl_range=self.max_isl_range,
        )

        self.total_gst_links = temp[0]

    @staticmethod
    @numba.njit  # type: ignore
    def numba_update_plus_grid_links(
        total_sats: int,
        satellites_array: np.ndarray,  # type: ignore
        link_array: np.ndarray,  # type: ignore
        number_of_isl_links: int,
        gst_array: np.ndarray,  # type: ignore
        gst_links_array: np.ndarray,  # type: ignore
        max_isl_range: int = (2**31) - 1,
    ) -> typing.Tuple[int]:
        for isl_idx in range(number_of_isl_links):
            sat_1 = link_array[isl_idx]["node_1"]
            sat_2 = link_array[isl_idx]["node_2"]
            d = int(
                math.sqrt(
                    math.pow(
                        satellites_array[sat_1]["x"] - satellites_array[sat_2]["x"], 2
                    )
                    + math.pow(
                        satellites_array[sat_1]["y"] - satellites_array[sat_2]["y"], 2
                    )
                    + math.pow(
                        satellites_array[sat_1]["z"] - satellites_array[sat_2]["z"], 2
                    )
                )
            )
            link_array[isl_idx]["active"] = d <= max_isl_range
            link_array[isl_idx]["distance"] = np.int32(d)

        gst_link_id = 0
        for gst in gst_array:
            shortest_d = np.inf

            for sat_idx in range(total_sats):
                # calculate distance
                d = int(
                    math.sqrt(
                        math.pow(satellites_array[sat_idx]["x"] - gst["x"], 2)
                        + math.pow(satellites_array[sat_idx]["y"] - gst["y"], 2)
                        + math.pow(satellites_array[sat_idx]["z"] - gst["z"], 2)
                    )
                )

                # decide if link is valid or not
                if d > gst["max_stg_range"]:
                    continue

                # if we allow only one link and the one we found is shorter than the old one overwrite the old one
                if gst["conn_type"] == satgen.config.GroundStationConnectionType.ONE:
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

                gst_link_id = gst_link_id + 1

        total_gst_links = gst_link_id

        return (total_gst_links,)

    def update_paths(self) -> None:
        # TODO: make this a numba function

        g = np.zeros(
            (self.total_sats, self.total_sats),
        )

        for x in range(self.total_links):
            g[
                self.link_array[x]["node_1"], self.link_array[x]["node_2"]
            ] = self.link_array[x]["delay"]

        dist_matrix, predecessors = scipy.sparse.csgraph.floyd_warshall(
            scipy.sparse.csr_matrix(g),
            return_predecessors=True,
            directed=True,
        )

        temp = self.numba_update_paths(
            dist_matrix=dist_matrix,
            predecessors=predecessors,
            total_sats=self.total_sats,
            path_array=self.path_array,
            gst_array=self.gst_array,
            total_gst=self.total_gst,
            gst_links_array=self.gst_links_array,
            total_gst_links=self.total_gst_links,
            isl_bandwidth=self.isl_bandwidth,
        )

        self.total_paths = temp[0]

    @staticmethod
    @numba.njit  # type: ignore
    def numba_update_paths(
        dist_matrix: np.ndarray,  # type: ignore
        predecessors: np.ndarray,  # type: ignore
        total_sats: int,
        path_array: np.ndarray,  # type: ignore
        gst_array: np.ndarray,  # type: ignore
        total_gst: int,
        gst_links_array: np.ndarray,  # type: ignore
        total_gst_links: int,
        isl_bandwidth: int,
    ) -> typing.Tuple[int]:
        total_paths = 0

        for i in range(total_sats):
            for j in range(total_sats):
                if i == j:
                    continue

                total_paths += 1

                path_array[total_paths]["node_1"] = np.int16(i)
                path_array[total_paths]["node_2"] = np.int16(j)
                path_array[total_paths]["next"] = predecessors[i, j]
                path_array[total_paths]["active"] = dist_matrix[i, j] > 0
                path_array[total_paths]["delay"] = np.int32(
                    dist_matrix[i, j] * ISL_PROPAGATION
                )
                path_array[total_paths]["bandwidth"] = np.int32(isl_bandwidth)

        for x in range(total_gst_links):
            total_paths += 1

            path_array[total_paths]["node_1"] = np.int16(gst_links_array[x]["gst"])
            path_array[total_paths]["node_2"] = np.int16(gst_links_array[x]["sat"])
            path_array[total_paths]["next"] = np.int16(gst_links_array[x]["sat"])
            path_array[total_paths]["active"] = True
            path_array[total_paths]["delay"] = np.int32(gst_links_array[x]["delay"])
            path_array[total_paths]["bandwidth"] = np.int32(
                gst_links_array[x]["bandwidth"]
            )

        for g in range(total_gst):
            for s1 in range(total_sats):
                _min_dist = np.inf
                _min_x = -1

                for x in range(total_gst_links):
                    if gst_links_array[x]["gst"] != g:
                        continue

                    _path_dist = (
                        dist_matrix[gst_links_array[x]["sat"], s1]
                        + gst_links_array[x]["delay"]
                    )

                    if _path_dist > _min_dist:
                        continue

                    _min_dist = _path_dist
                    _min_x = x

                total_paths += 1

                path_array[total_paths]["node_1"] = np.int16(-g)
                path_array[total_paths]["node_2"] = np.int16(s1)
                path_array[total_paths]["next"] = np.int16(
                    gst_links_array[_min_x]["sat"] if _min_x != -1 else -1
                )
                path_array[total_paths]["active"] = _min_x != -1
                path_array[total_paths]["delay"] = np.int32(
                    _min_dist * ISL_PROPAGATION if _min_x != -1 else -1
                )

                path_array[total_paths]["bandwidth"] = np.int32(
                    min(gst_array[g]["bandwidth"], isl_bandwidth)  # type: ignore
                )

        for g1 in range(total_gst):
            for g2 in range(total_gst):
                if g1 > g2:
                    continue

                _min_dist = np.inf
                _min_x1 = -1
                _min_x2 = -1

                for x1 in range(total_gst_links):
                    if gst_links_array[x1]["gst"] != g1:
                        continue
                    for x2 in range(total_gst_links):
                        if gst_links_array[x2]["gst"] != g2:
                            continue

                    path_dist = (
                        dist_matrix[
                            gst_links_array[x1]["sat"],
                            gst_links_array[x2]["sat"],
                        ]
                        + gst_links_array[x1]["distance"]
                        + gst_links_array[x2]["distance"]
                    )

                    if path_dist > _min_dist:
                        continue

                    _min_dist = path_dist
                    _min_x1 = x1
                    _min_x1 = x2

                total_paths += 1

                path_array[total_paths]["node_1"] = np.int16(-g1)
                path_array[total_paths]["node_2"] = np.int16(-g2)
                path_array[total_paths]["next"] = np.int16(
                    gst_links_array[_min_x1]["sat"] if _min_x1 != -1 else -1
                )
                path_array[total_paths]["active"] = _min_x1 != -1
                path_array[total_paths]["delay"] = np.int32(
                    _min_dist * ISL_PROPAGATION if _min_x1 != -1 else -1
                )

                path_array[total_paths]["bandwidth"] = np.int32(
                    min(
                        gst_array[g1]["bandwidth"],
                        isl_bandwidth,
                        gst_array[g2]["bandwidth"],
                    )  # type: ignore
                )

                total_paths += 1

                path_array[total_paths]["node_1"] = np.int16(-g2)
                path_array[total_paths]["node_2"] = np.int16(-g1)
                path_array[total_paths]["next"] = np.int16(
                    gst_links_array[_min_x2]["sat"] if _min_x2 != -1 else -1
                )
                path_array[total_paths]["active"] = _min_x2 != -1
                path_array[total_paths]["delay"] = np.int32(
                    _min_dist * ISL_PROPAGATION if _min_x2 != -1 else -1
                )

                path_array[total_paths]["bandwidth"] = np.int32(
                    min(
                        gst_array[g2]["bandwidth"],
                        isl_bandwidth,
                        gst_array[g1]["bandwidth"],
                    )  # type: ignore
                )

        return (total_paths,)
