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

from math import ceil
import typing

from .types import BoundingBoxConfig, ShellConfig, GroundstationConfig


def lat_dist(x1: float, x2: float) -> float:
    if x2 < x1:
        return (180 - abs(x2)) - x1

    return x2 - x1


def lon_dist(x1: float, x2: float) -> float:
    if x2 < x1:
        return (360 - abs(x2)) - x1

    return x2 - x1


def resource_estimate(
    bbox: BoundingBoxConfig,
    shells: typing.List[ShellConfig],
    groundstations: typing.List[GroundstationConfig],
    cpus: int,
    mem: float,
) -> float:
    # 1. calculate area of bounding box

    width = lon_dist(bbox.lon1, bbox.lon2)
    height = lat_dist(bbox.lat1, bbox.lat2)

    S_bbox = width * height

    # 2. divide by area of earth
    S_earth = 360.0 * 180.0

    ratio = S_bbox / S_earth

    # look. you might see this and think to yourself: "what the hell? this
    # isn't at all how you calculate this! you have to account for different
    # distances between longitude lines near the poles! this doesn't make any
    # sense! you're not even factoring in the earth's radius in any way! how
    # did you get a CS degree?!" and you'd be kind of right. however, here is
    # the thing: we're not trying to calculate the actual earth area here. what
    # we're actually trying to do is estimate how many satellites are in our
    # area compared to the total number of satellites. and at least for orbits
    # with inclinations above ~45°, satellites are also more dense near the
    # poles. so this kind of evens out, doesn't it? no, it doesn't exactly,
    # but we're actually more correct than the old approach where we went by
    # actual earth area. it's good enough. don't believe me? please provide
    # evidence.
    #
    # (no, like actually: please someone actually calculate this)

    total_cpus = sum(s.total_sats * s.computeparams.vcpu_count for s in shells)
    total_mem = sum(s.total_sats * s.computeparams.mem_size_mib for s in shells)

    gst_required_cpu = sum(g.computeparams.vcpu_count for g in groundstations)
    gst_required_mem = sum(g.computeparams.mem_size_mib for g in groundstations)

    required_cpu = total_cpus * ratio
    required_mem = total_mem * ratio

    if required_cpu + gst_required_cpu > cpus:
        print(
            "\033[93m⚠️  You have %d CPUs available but require approx. %d CPUs (%d for satellites and %d for ground stations)\033[0m"
            % (
                ceil(cpus),
                ceil(required_cpu + gst_required_cpu),
                ceil(required_cpu),
                ceil(gst_required_cpu),
            )
        )
    else:
        print(
            "\033[92m✅ You have %d CPUs available and require approx. %d CPUs (%d for satellites and %d for ground stations)\033[0m"
            % (
                ceil(cpus),
                ceil(required_cpu + gst_required_cpu),
                ceil(required_cpu),
                ceil(gst_required_cpu),
            )
        )

    if required_mem + gst_required_mem > mem:
        print(
            "\033[93m⚠️  You have %dGB memory available but require approx. %dGB memory (%dGB for satellites and %dGB for ground stations)\033[0m"
            % (
                ceil(mem / 1024),
                ceil((required_mem + gst_required_mem) / 1024),
                ceil(required_mem / 1024),
                ceil(gst_required_mem / 1024),
            )
        )
    else:
        print(
            "\033[92m✅ You have %dGB memory and require approx. %dGB memory (%dGB for satellites and %dGB for ground stations)\033[0m"
            % (
                ceil(mem / 1024),
                ceil((required_mem + gst_required_mem) / 1024),
                ceil(required_mem / 1024),
                ceil(gst_required_mem / 1024),
            )
        )

    utilization = max(
        required_cpu / (max(0.001, cpus - gst_required_cpu)),
        required_mem / (max(0.001, mem - gst_required_mem)),
    )

    return utilization
