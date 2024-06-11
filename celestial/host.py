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

"""Adapter for communication with the Celestial hosts over gRPC"""

import typing
import grpc
import time
import logging

import proto.celestial.celestial_pb2
import proto.celestial.celestial_pb2_grpc


class Host:
    """
    Communication link for a Celestial host.
    """

    def __init__(self, num: int, addr: str):
        """
        Initialize host communication.

        :param num: The host number.
        :param addr: The address of the host.
        """
        self.num = num
        self.addr = addr

        c = grpc.insecure_channel(self.addr)
        self.stub = proto.celestial.celestial_pb2_grpc.CelestialStub(c)

        self.public_key = ""

    def register(self) -> proto.celestial.celestial_pb2.RegisterResponse:
        """
        Send a `register` request to the host.

        :return: The response from the host.
        """
        try:
            request = proto.celestial.celestial_pb2.RegisterRequest(host=self.num)

            response: proto.celestial.celestial_pb2.RegisterResponse = (
                self.stub.Register(request)
            )

        except Exception as e:
            logging.error(f"Error registering host {self.num}: {e}")
            exit(1)

        # others currently not used
        self.peer_public_key = response.peer_public_key

        self.peer_listen_addr = (
            self.addr.split(":")[0] + ":" + response.peer_listen_addr.split(":")[1]
        )

        logging.debug(f"host {self.num} registered")
        logging.debug(f"memory: {response.available_ram}")
        logging.debug(f"cpu: {response.available_cpus}")

        return response

    def init(
        self,
        init_request: proto.celestial.celestial_pb2.InitRequest,
    ) -> None:
        """
        Send an `init` request to the host.

        :param hosts: A list of all hosts in the constellation.
        :param machines: A dictionary mapping host numbers to a list of machine ID and machine configuration tuples.
        """

        self.stub.Init(init_request)

        return

    def stop(self) -> None:
        """
        Send a `stop` request to the host.
        """
        self.stub.Stop(proto.celestial.celestial_pb2.Empty())

    def update(
        self,
        update_requests: typing.Iterator[
            proto.celestial.celestial_pb2.StateUpdateRequest
        ],
    ) -> None:
        """
        Send a `update` request to the host.

        :param machine_diff: An iterator of machine ID and machine state tuples.
        :param link_diff: An iterator of link tuples.
        """

        t1 = time.perf_counter()
        self.stub.Update(update_requests)
        t2 = time.perf_counter()
        logging.debug(f"update transmission took {t2-t1} seconds")

        return
