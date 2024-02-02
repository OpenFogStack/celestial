import math
import numpy as np
import numpy.typing as npt
import numba
import typing

import celestial.config
import celestial.sgp4_solver
import celestial.types

### CONSTANTS ###
EARTH_RADIUS_M = 6_371_000  # meters
SECONDS_PER_DAY = 86_400
MIN_COMMS_ALTITUDE_M = 80_000  # meters, height of thermosphere
LINK_PROPAGATION_S_M = 3.336e-9  # s/m, about 1/c
CROSSLINK_INTERPOLATION = 1

### DTYPES ###
SATELLITE_DTYPE = np.dtype(
    [
        ("ID", np.int16),  # ID number, unique, = array index
        ("plane_number", np.int16),  # which orbital plane is the satellite in?
        ("offset_number", np.int16),  # What satellite within the plane?
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
        ("conn_type", np.uint32),  # connection type of the ground station
        # 0 = all, 1 = one
        ("max_stg_range", np.uint32),  # max stg range of ground stations
        # depends on minelevation
        (
            "bandwidth_kbits",
            np.uint32,
        ),  # bandwidth this ground station supports in Kbps
        ("init_x", np.int32),  # initial x position in meters
        ("init_y", np.int32),  # initial y position in meters
        ("init_z", np.int32),  # initial z position in meters
        ("x", np.int32),  # x position in meters
        ("y", np.int32),  # y position in meters
        ("z", np.int32),  # z position in meters
    ]
)

# The numpy data type used to store link data
# each index is 8 bytes
SAT_LINK_DTYPE = np.dtype(
    [
        ("node_1", np.int16),  # an endpoint of the link
        ("node_2", np.int16),  # the other endpoint of the link
        ("active", np.bool_),  # can this link be active?
        ("distance_m", np.uint32),  # distance of the link in meters
    ]
)

GST_SAT_LINK_DTYPE = np.dtype(
    [
        ("gst", np.int16),  # ground station this link refers to
        ("sat", np.int16),  # satellite endpoint of the link
        ("distance_m", np.uint32),  # distance of the link in meterss
    ]
)

PATH_DTYPE = np.dtype(
    [
        ("active", np.bool_),  # can this link be active?
        ("next_hop", np.int16),  # the next node in the path
        ("bandwidth_kbits", np.uint32),  # distance of the link in meters
        ("delay_us", np.uint32),  # delay of this link in microseconds
    ]
)

PATH_LINK_DTYPE = np.dtype(
    [
        ("node_1", np.int16),  # an endpoint of the link
        ("node_2", np.int16),  # the other endpoint of the link
        ("path", PATH_DTYPE),  # the path between the two endpoints
    ]
)


class Shell:
    def __init__(
        self,
        shell_identifier: int,
        planes: int,
        sats: int,
        altitude_km: float,
        inclination: float,
        arc_of_ascending_nodes: float,
        eccentricity: float,
        isl_bandwidth_kbits: int,
        bbox: celestial.config.BoundingBox,
        ground_stations: typing.List[celestial.config.GroundStation],
    ):
        self.shell_identifier = shell_identifier

        self.current_timestep: celestial.types.timestamp_s = 0

        self.number_of_planes = planes
        self.nodes_per_plane = sats
        self.total_sats = planes * sats

        LINK_ARRAY_SIZE = self.total_sats * 2  # + (len(ground_stations) * 16)
        GST_LINK_ARRAY_SIZE = len(ground_stations) * self.total_sats
        PATH_MATRIX_SIZE = self.total_sats + len(ground_stations)

        # orbit options
        self.altitude_km = altitude_km

        self.semi_major_axis = float(self.altitude_km) * 1000 + EARTH_RADIUS_M

        # bounding box
        self.bbox = bbox

        self.isl_bandwidth_kbits = isl_bandwidth_kbits

        self.satellites_array = np.empty(self.total_sats, dtype=SATELLITE_DTYPE)

        self.link_array = np.zeros(LINK_ARRAY_SIZE, dtype=SAT_LINK_DTYPE)

        self.total_isl_links = 0

        self.total_gst = len(ground_stations)

        self.gst_array = np.zeros(self.total_gst, dtype=GROUNDPOINT_DTYPE)

        self.gst_names: typing.List[str] = [""] * self.total_gst

        self.gst_links_array = np.zeros(GST_LINK_ARRAY_SIZE, dtype=GST_SAT_LINK_DTYPE)

        self.total_gst_links = 0

        self.path_matrix = np.zeros(
            (PATH_MATRIX_SIZE, PATH_MATRIX_SIZE), dtype=PATH_DTYPE
        )

        self.curr_paths = np.zeros(
            (PATH_MATRIX_SIZE, PATH_MATRIX_SIZE), dtype=PATH_DTYPE
        )

        self.link_diff: celestial.types.LinkDiff = {}

        self.nodes_diff: celestial.types.MachineDiff = {}

        # init nodes
        for plane in range(0, self.number_of_planes):
            for node in range(0, self.nodes_per_plane):
                unique_id = (plane * self.nodes_per_plane) + node
                self.satellites_array[unique_id]["ID"] = np.int16(unique_id)
                self.satellites_array[unique_id]["plane_number"] = np.int16(plane)
                self.satellites_array[unique_id]["offset_number"] = np.int16(node)

        self.solver = celestial.sgp4_solver.SGP4Solver(
            planes=self.number_of_planes,
            sats=self.nodes_per_plane,
            altitude_km=self.altitude_km,
            inclination=inclination,
            arc_of_ascending_nodes=arc_of_ascending_nodes,
            eccentricity=eccentricity,
        )

        self.satellites_array = self.solver.init_sat_array(self.satellites_array)

        for sat in self.satellites_array:
            sat["in_bbox"] = False

        self.init_ground_stations(ground_stations)

        self.init_plus_grid_links()

        self.max_isl_range = self.calculate_max_ISL_distance()

    def step(
        self,
        time: celestial.types.timestamp_s,
        calculate_diffs: bool = False,
        delay_update_threshold_us: int = 0,
    ) -> None:
        self.current_time = int(time)

        self.old_machines = self.satellites_array.copy()

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

        if not calculate_diffs:
            return

        self.nodes_diff = {}
        # calculate the node diffs
        for sat in self.satellites_array:
            if sat["in_bbox"] != self.old_machines[sat["ID"]]["in_bbox"]:
                m_id = celestial.types.MachineID(
                    group=self.shell_identifier, id=sat["ID"]
                )

                self.nodes_diff[m_id] = (
                    celestial.types.VMState.ACTIVE
                    if sat["in_bbox"]
                    else celestial.types.VMState.STOPPED
                )

        self.update_paths()

        self.link_diff = {}

        path_diff = np.zeros(
            (self.total_sats + self.total_gst) ** 2, dtype=PATH_LINK_DTYPE
        )

        total_link_diff = self.numba_get_link_diff(
            delay_update_threshold_us=delay_update_threshold_us,
            total_sats=self.total_sats,
            total_gst=self.total_gst,
            curr_paths=self.curr_paths,
            path_matrix=self.path_matrix,
            path_diff=path_diff,
        )[0]

        for link in path_diff[:total_link_diff]:
            n1 = (
                celestial.types.MachineID(self.shell_identifier, link["node_1"])
                if link["node_1"] < self.total_sats
                else celestial.types.MachineID(
                    group=0,
                    id=link["node_1"] - self.total_sats,
                    name=self.gst_names[link["node_1"] - self.total_sats],
                )
            )

            n2 = (
                celestial.types.MachineID(self.shell_identifier, link["node_2"])
                if link["node_2"] < self.total_sats
                else celestial.types.MachineID(
                    group=0,  # leaky abstraction but it works
                    id=link["node_2"] - self.total_sats,
                    name=self.gst_names[link["node_2"] - self.total_sats],
                )
            )

            self.link_diff.setdefault(n1, {})[n2] = celestial.types.Link(
                latency_us=link["path"]["delay_us"],
                bandwidth_kbits=link["path"]["bandwidth_kbits"],
                blocked=not link["path"]["active"],
                next_hop=celestial.types.MachineID(
                    group=self.shell_identifier, id=link["path"]["next_hop"]
                ),
            )

            self.curr_paths[link["node_1"]][link["node_2"]] = link["path"]

    def get_sat_node_diffs(self) -> celestial.types.MachineDiff:
        return self.nodes_diff

    def get_link_diff(self) -> celestial.types.LinkDiff:
        return self.link_diff

    def get_sat_positions(self) -> np.ndarray:  # type: ignore
        sat_positions: np.ndarray = np.copy(  # type: ignore
            self.satellites_array[["ID", "x", "y", "z", "in_bbox"]]
        )  # type: ignore

        return sat_positions

    def get_gst_positions(self) -> np.ndarray:  # type: ignore
        ground_positions: np.ndarray = np.copy(self.gst_array[["x", "y", "z"]])  # type: ignore

        return ground_positions

    def get_links(self) -> np.ndarray:  # type: ignore
        links: np.ndarray = np.copy(self.link_array[: self.total_isl_links])  # type: ignore

        return links

    def get_gst_links(self) -> np.ndarray:  # type: ignore
        gst_links: np.ndarray = np.copy(self.gst_links_array[: self.total_gst_links])  # type: ignore

        return gst_links

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
        xyz_pos = np.dot(rotation_matrix, np.array(pos))

        x = xyz_pos[0]
        y = xyz_pos[1]
        z = xyz_pos[2]

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
        self, groundstations: typing.List[celestial.config.GroundStation]
    ) -> None:
        for i in range(len(groundstations)):
            g = groundstations[i]

            init_pos = [0.0, 0.0, 0.0]

            latitude = math.radians(g.lat)
            longitude = math.radians(g.lng)

            init_pos[0] = (
                (EARTH_RADIUS_M + 100.0) * math.cos(latitude) * math.cos(longitude)
            )
            init_pos[1] = (
                (EARTH_RADIUS_M + 100.0) * math.cos(latitude) * math.sin(longitude)
            )
            init_pos[2] = (EARTH_RADIUS_M + 100.0) * math.sin(latitude)

            temp: npt.NDArray[GROUNDPOINT_DTYPE] = np.zeros(1, dtype=GROUNDPOINT_DTYPE)

            temp[0]["ID"] = np.int16(-i - 1)

            temp[0]["conn_type"] = g.connection_type.value

            temp[0]["max_stg_range"] = self.calculate_max_space_to_gst_distance(
                g.min_elevation
            )

            temp[0]["bandwidth_kbits"] = g.gts_bandwidth_kbits
            temp[0]["init_x"] = np.int32(init_pos[0])
            temp[0]["init_y"] = np.int32(init_pos[1])
            temp[0]["init_z"] = np.int32(init_pos[2])
            temp[0]["x"] = np.int32(init_pos[0])
            temp[0]["y"] = np.int32(init_pos[1])
            temp[0]["z"] = np.int32(init_pos[2])

            self.gst_names[i] = g.name

            self.gst_array[i] = temp[0]

    def calculate_max_ISL_distance(self) -> int:
        c = EARTH_RADIUS_M + MIN_COMMS_ALTITUDE_M
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
        b = EARTH_RADIUS_M

        alpha = math.radians(min_elevation + 90)

        beta = math.asin(math.sin(alpha) * b / a)

        c = math.sin(math.radians(180) - alpha - beta) * a / math.sin(alpha)
        return int(c)

    def init_plus_grid_links(self) -> None:
        temp = self.numba_init_plus_grid_links(
            link_array=self.link_array,
            number_of_planes=self.number_of_planes,
            nodes_per_plane=self.nodes_per_plane,
        )
        if temp is not None:
            self.total_isl_links = temp[0]

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
            total_isl_links=self.total_isl_links,
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
        total_isl_links: int,
        gst_array: np.ndarray,  # type: ignore
        gst_links_array: np.ndarray,  # type: ignore
        max_isl_range: int = (2**31) - 1,
    ) -> typing.Tuple[int]:
        for isl_idx in range(total_isl_links):
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
            link_array[isl_idx]["distance_m"] = np.uint32(d)

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
                if (
                    gst["conn_type"]
                    == celestial.config.GroundStationConnectionType.ONE.value
                ):
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
                gst_links_array[gst_link_id]["distance_m"] = np.uint32(d)

                gst_link_id = gst_link_id + 1

        total_gst_links = gst_link_id

        return (total_gst_links,)

    def update_paths(self) -> None:
        self.numba_update_paths(
            sat_link_array=self.link_array,
            total_isl_links=self.total_isl_links,
            total_sats=self.total_sats,
            path_matrix=self.path_matrix,
            gst_array=self.gst_array,
            total_gst=self.total_gst,
            gst_links_array=self.gst_links_array,
            total_gst_links=self.total_gst_links,
            isl_bandwidth_kbits=self.isl_bandwidth_kbits,
        )

    @staticmethod
    @numba.njit  # type: ignore
    def numba_update_paths(
        sat_link_array: np.ndarray,  # type: ignore
        total_isl_links: int,
        total_sats: int,
        path_matrix: np.ndarray,  # type: ignore
        gst_array: np.ndarray,  # type: ignore
        total_gst: int,
        gst_links_array: np.ndarray,  # type: ignore
        total_gst_links: int,
        isl_bandwidth_kbits: int,
    ) -> None:
        dist_matrix = np.zeros((total_sats, total_sats), dtype=np.float64)
        next_hops = np.zeros((total_sats, total_sats), dtype=np.int16)

        for i in range(total_sats):
            for j in range(total_sats):
                dist_matrix[i, j] = np.inf
                next_hops[i, j] = -1

        for link in sat_link_array[:total_isl_links]:
            if not link["active"]:
                continue

            dist_matrix[link["node_1"], link["node_2"]] = link["distance_m"]
            next_hops[link["node_1"], link["node_2"]] = link["node_2"]

        for i in range(total_sats):
            dist_matrix[i, i] = 0
            next_hops[i, i] = i

        # Floyd-Warshall algorithm
        for k in range(total_sats):
            for i in range(total_sats):
                # it should be possible to optimize this for symmetric graphs
                for j in range(i + 1, total_sats):
                    if dist_matrix[i, j] > dist_matrix[i, k] + dist_matrix[k, j]:
                        dist_matrix[i, j] = dist_matrix[i, k] + dist_matrix[k, j]
                        next_hops[i, j] = next_hops[i, k]

        for i in range(total_sats):
            for j in range(i + 1, total_sats):
                path_matrix[i, j]["active"] = dist_matrix[i, j] != np.inf
                path_matrix[i, j]["next_hop"] = np.int16(next_hops[i, j])
                path_matrix[i, j]["delay_us"] = np.uint32(
                    dist_matrix[i, j] * (LINK_PROPAGATION_S_M * 1e6)
                )
                # print(path_matrix[i, j]["delay_us"])
                path_matrix[i, j]["bandwidth_kbits"] = np.uint32(isl_bandwidth_kbits)

        for g in range(total_gst):
            for s1 in range(total_sats):
                _min_dist = np.inf
                _min_x = -1

                for x in range(total_gst_links):
                    if gst_links_array[x]["gst"] != gst_array[g]["ID"]:
                        # print(
                        # f"path from gst {gst_links_array[x]['gst']} not relevant for {g}"
                        # )
                        continue

                    _s2 = gst_links_array[x]["sat"]

                    d = dist_matrix[s1, _s2] if s1 < _s2 else dist_matrix[_s2, s1]

                    _path_dist = d + gst_links_array[x]["distance_m"]

                    if _path_dist >= _min_dist:
                        # new path is not better than old path
                        # checking for equal is important as we may have both paths being inf
                        continue

                    _min_dist = _path_dist
                    # print("new min dist", _min_dist)
                    _min_x = x

                    if _s2 == s1:
                        break

                i = g + total_sats
                j = s1

                path_matrix[i, j]["active"] = _min_x != -1
                path_matrix[j, i]["active"] = _min_x != -1

                if _min_x == -1:
                    continue

                path_matrix[i, j]["next_hop"] = np.int16(gst_links_array[_min_x]["sat"])

                path_matrix[i, j]["delay_us"] = np.uint32(
                    _min_dist * (LINK_PROPAGATION_S_M * 1e6)
                )

                path_matrix[i, j]["bandwidth_kbits"] = np.uint32(
                    min(gst_array[g]["bandwidth_kbits"], isl_bandwidth_kbits)  # type: ignore
                )

        for g1 in range(total_gst):
            for g2 in range(g1 + 1, total_gst):
                _min_dist = np.inf
                _min_x1 = -1

                for x1 in range(total_gst_links):
                    if gst_links_array[x1]["gst"] != g1:
                        continue
                    for x2 in range(total_gst_links):
                        if gst_links_array[x2]["gst"] != g2:
                            continue

                    _s1 = gst_links_array[x1]["sat"]
                    _s2 = gst_links_array[x2]["sat"]

                    d = dist_matrix[_s1, _s2] if _s1 < _s2 else dist_matrix[_s2, _s1]

                    path_dist = (
                        d
                        + gst_links_array[x1]["distance_m"]
                        + gst_links_array[x2]["distance_m"]
                    )

                    if path_dist >= _min_dist:
                        continue

                    _min_dist = path_dist
                    _min_x1 = x1

                i = g1 + total_sats
                j = g2 + total_sats

                path_matrix[i, j]["active"] = _min_x1 != -1

                if _min_x1 == -1:
                    continue

                path_matrix[i, j]["next_hop"] = np.int16(
                    gst_links_array[_min_x1]["sat"]
                )

                path_matrix[i, j]["delay_us"] = np.uint32(
                    _min_dist * (LINK_PROPAGATION_S_M * 1e6)
                )
                print(path_matrix[i, j]["delay_us"])

                path_matrix[i, j]["bandwidth_kbits"] = np.uint32(
                    min(
                        gst_array[g1]["bandwidth_kbits"],
                        isl_bandwidth_kbits,
                        gst_array[g2]["bandwidth_kbits"],
                    )  # type: ignore
                )

    @staticmethod
    @numba.njit  # type: ignore
    def numba_get_link_diff(
        delay_update_threshold_us: int,
        total_sats: int,
        total_gst: int,
        curr_paths: np.ndarray,  # type: ignore
        path_matrix: np.ndarray,  # type: ignore
        path_diff: np.ndarray,  # type: ignore
    ) -> typing.Tuple[int]:
        total_link_diff = 0

        # path diff for satellites
        for n1 in range(total_sats):
            for n2 in range(n1 + 1, total_sats):
                p1 = curr_paths[n1][n2]
                p2 = path_matrix[n1][n2]

                if (
                    # note that converting to int32 is necessary for subtraction to work correctly
                    np.abs(np.int32(p1["delay_us"]) - np.int32(p2["delay_us"]))
                    > delay_update_threshold_us
                    or p1["active"] != p2["active"]
                    or p1["bandwidth_kbits"] != p2["bandwidth_kbits"]
                    or p1["next_hop"] != p2["next_hop"]
                ):
                    path_diff[total_link_diff]["node_1"] = np.int16(n1)
                    path_diff[total_link_diff]["node_2"] = np.int16(n2)
                    path_diff[total_link_diff]["path"] = p2
                    total_link_diff += 1

        # path diff for ground stations to all
        for n1 in range(total_sats, total_sats + total_gst):
            for n2 in range(total_sats + total_gst):
                if n1 == n2:
                    continue

                p1 = curr_paths[n1][n2]
                p2 = path_matrix[n1][n2]

                if (
                    np.abs(np.int32(p1["delay_us"]) - np.int32(p2["delay_us"]))
                    > delay_update_threshold_us
                    or p1["active"] != p2["active"]
                    or p1["bandwidth_kbits"] != p2["bandwidth_kbits"]
                    or p1["next_hop"] != p2["next_hop"]
                ):
                    # print(f"n1 {n1} n2 {n2} changed")
                    path_diff[total_link_diff]["node_1"] = np.int16(n1)
                    path_diff[total_link_diff]["node_2"] = np.int16(n2)
                    path_diff[total_link_diff]["path"] = p2
                    total_link_diff += 1

        return (total_link_diff,)
