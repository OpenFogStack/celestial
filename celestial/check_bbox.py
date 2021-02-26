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

from celestial.types import BoundingBoxConfig, GroundstationConfig, ShellConfig
import numpy as np
import typing

EARTH_RADIUS = 6371000
def sat_dist(altitude: float, elevation: float) -> float:
    A = EARTH_RADIUS/1000.0
    B = EARTH_RADIUS/1000.0 + altitude
    b = np.radians(90.0 + elevation)
    a = np.arcsin(A * np.sin(b) / B)
    c = np.radians(180) - a - b

    return float(2.0 * np.pi * EARTH_RADIUS/1000.0 * c/np.radians(360.0))

def earth_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlon = np.radians(lon2 - lon1)
    dlat = np.radians(lat2 - lat1)

    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2
    c = float(2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))

    return EARTH_RADIUS/1000.0 * c

# https://gis.stackexchange.com/questions/5821/calculating-latitude-longitude-x-miles-from-point
def displace(lat: float, lon: float, theta: float, distance: float) -> typing.Tuple[float, float]:
    """
    Displace a LatLng theta degrees counterclockwise and some
    meters in that direction.
    Notes:
        http://www.movable-type.co.uk/scripts/latlong.html
        0 DEGREES IS THE VERTICAL Y AXIS! IMPORTANT!
    Args:
        theta:    A number in degrees.
        distance: A number in kilometers.
    Returns:
        A new LatLng.
    """

    delta = np.divide(distance, EARTH_RADIUS/1000)

    theta =  np.radians(theta)
    lat1 = np.radians(lat)
    lng1 =  np.radians(lon)

    lat2 = np.arcsin( np.sin(lat1) * np.cos(delta) +
                      np.cos(lat1) * np.sin(delta) * np.cos(theta) )

    lon2 = lng1 + np.arctan2( np.sin(theta) * np.sin(delta) * np.cos(lat1),
                              np.cos(delta) - np.sin(lat1) * np.sin(lat2))

    lon2 = (lon2 + 3 * np.pi) % (2 * np.pi) - np.pi

    return (np.rad2deg(lat2), np.rad2deg(lon2))

def is_in_bbox(lat: float, lon: float, bbox: BoundingBoxConfig) -> bool:
    if bbox.lon2 < bbox.lon1:
        if lon < bbox.lon1 and lon > bbox.lon2:
            return False
    else:
        if lon < bbox.lon1 or lon > bbox.lon2:
            return False

    return bool(lat >= bbox.lat1 and lat <= bbox.lat2)

def check_bbox(bbox: BoundingBoxConfig, shells: typing.List[ShellConfig], groundstations: typing.List[GroundstationConfig]) -> bool:

    ok = True

    sugg_lat1 = bbox.lat1
    sugg_lon1 = bbox.lon1
    sugg_lat2 = bbox.lat2
    sugg_lon2 = bbox.lon2

    # 1. find max altitude
    # if we can cover the max altitude, we also cover everything else
    # is in kilometers
    max_altitude = 0

    for shell in shells:
        max_altitude = max(max_altitude, shell.altitude)

    # 2. for each ground station:
    #   2.1 calculate distance from bbox borders
    #   2.2 check GROUND distance to furthest possible satellite (at minelevation)

    for g in groundstations:

        if not is_in_bbox(g.lat, g.lng, bbox):
            print("\033[91m❌ Ground station %s is not within your bounding box!\033[0m" % g.name)
            return False

        d = sat_dist(max_altitude, g.networkparams.minelevation)

        north = earth_dist(g.lat, g.lng, bbox.lat2, g.lng)
        #print("North: %.1fkm" % north)

        east = earth_dist(g.lat, g.lng, g.lat, bbox.lon2)
        #print("East: %.1fkm" % east)

        south = earth_dist(bbox.lat1, g.lng, g.lat, g.lng)
        #print("South: %.1fkm" % south)

        west = earth_dist(g.lat, bbox.lon1, g.lat, g.lng)
        #print("West: %.1fkm" % west)

        if north <= d:
            print("\033[93m⚠️  Your bounding box does not cover all satellites reachable to the north of ground station %s, you should extend it by %.1fkm to the north\033[0m" % (g.name, d - north))
            sugg_lat2 = max(displace(g.lat, g.lng, 0.0, d + 10.0)[0], sugg_lat2)
            ok = False

        if east <= d:
            print("\033[93m⚠️  Your bounding box does not cover all satellites reachable to the east of ground station %s, you should extend it by %.1fkm to the east\033[0m" % (g.name, d - east))
            ok = False
            sugg_lon2 = max(displace(g.lat, g.lng, 270.0, d + 10.0)[1], sugg_lon2)

        if south <= d:
            print("\033[93m⚠️  Your bounding box does not cover all satellites reachable to the south of ground station %s, you should extend it by %.1fkm to the south\033[0m" % (g.name, d - south))
            ok = False
            sugg_lat1 = min(displace(g.lat, g.lng, 180.0, d + 10.0)[0], sugg_lat1)

        if west <= d:
            print("\033[93m⚠ Your bounding box does not cover all satellites reachable to the west of ground station %s, you should extend it by %.1fkm to the west\033[0m" % (g.name, d - west))
            ok = False
            sugg_lon1 = min(displace(g.lat, g.lng, 90.0, d + 10.0)[1], sugg_lon1)

    if not ok:
        print("\033[93m⚠️  Your suggested bounding box is [%.4f, %.4f, %.4f, %.4f]\033[0m" % (sugg_lat1, sugg_lon1, sugg_lat2, sugg_lon2))

    return ok