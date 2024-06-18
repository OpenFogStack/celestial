#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Ben S. Kempton, Tobias Pfandzelter, The OpenFogStack Team.
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

"""Animation of the constellation"""

import vtk
import threading as td
import seaborn as sns
import numpy as np
from multiprocessing.connection import Connection as MultiprocessingConnection
import types
import typing

import celestial.config
import celestial.types
import celestial.shell

EARTH_RADIUS_M = 6371000  # radius of Earth in meters

LANDMASS_OUTLINE_COLOR = (0.0, 0.0, 0.0)  # black, best contrast
EARTH_LAND_OPACITY = 1.0

EARTH_BASE_COLOR = (0.9, 0.9, 1.0)  # light blue, like water!
EARTH_OPACITY = 1.0

BACKGROUND_COLOR = (1.0, 1.0, 1.0)  # white

# SAT_COLOR = (1.0, 0.0, 0.0)  # red, color of satellites
SAT_OPACITY = 1.0
SAT_INACTIVE_OPACITY = 0.5

GST_COLOR = (0.0, 1.0, 0.0)  # green, color of groundstations
GST_OPACITY = 10.0

ISL_LINK_COLOR = (0.9, 0.5, 0.1)  # yellow-brown, satellite-satellite links
ISL_LINK_OPACITY = 1.0
ISL_LINE_WIDTH = 1  # how wide to draw line in pixels

GST_LINK_COLOR = (0.5, 0.9, 0.5)  # greenish? satellite-groundstation links
GST_LINK_OPACITY = 0.75
GST_LINE_WIDTH = 2  # how wide to draw line in pixels

PATH_LINK_COLOR = (0.8, 0.2, 0.8)  # purpleish? path links
PATH_LINK_OPACITY = 0.7
PATH_LINE_WIDTH = 13  # how wide to draw line in pixels

EARTH_SPHERE_POINTS = 5000  # higher = smoother earth model, slower to generate

SAT_POINT_SIZE = 8  # how big satellites are in (probably) screen pixels
GST_POINT_SIZE = 8  # how big ground points are in (probably) screen pixels

SECONDS_PER_DAY = 86400  # number of seconds per earth rotation (day)


class AnimationConstellation:
    """
    Animation constellation that advances shells and updates VTK animation
    """

    def __init__(
        self,
        config: celestial.config.Config,
        conn: MultiprocessingConnection,
    ):
        """
        Animation constellation initialization

        :param config: The configuration of the constellation.
        :param conn: The connection to the animation process.
        """
        self.conn = conn
        self.config = config

        self.current_time: celestial.types.timestamp_s = 0
        self.shells: typing.List[celestial.shell.Shell] = []

        for i, sc in enumerate(config.shells):
            s = celestial.shell.Shell(
                shell_identifier=i + 1,
                planes=sc.planes,
                sats=sc.sats,
                altitude_km=sc.altitude_km,
                inclination=sc.inclination,
                arc_of_ascending_nodes=sc.arc_of_ascending_nodes,
                eccentricity=sc.eccentricity,
                isl_bandwidth_kbits=sc.isl_bandwidth_kbits,
                bbox=config.bbox,
                ground_stations=config.ground_stations,
            )

            self.shells.append(s)

        for s in self.shells:
            s.step(self.current_time, calculate_diffs=False)

        self.conn.send(
            {
                "type": "init",
                "num_shells": len(self.shells),
                "total_sats": [s.total_sats for s in self.shells],
                "sat_positions": [s.get_sat_positions() for s in self.shells],
                "links": [s.get_links() for s in self.shells],
                "gst_positions": self.shells[0].get_gst_positions(),
                "gst_links": [s.get_gst_links() for s in self.shells],
            }
        )

    def step(self, t: celestial.types.timestamp_s) -> None:
        """
        Advance the constellation to the given time.

        :param t: The time to advance to.
        """
        self.current_time = t

        for s in self.shells:
            s.step(self.current_time)

        self.conn.send(
            {
                "type": "time",
                "time": self.current_time,
            }
        )

        for i in range(len(self.shells)):
            self.conn.send(
                {
                    "type": "shell",
                    "shell": i,
                    "sat_positions": self.shells[i].get_sat_positions(),
                    "links": self.shells[i].get_links(),
                    "gst_positions": self.shells[i].get_gst_positions(),
                    "gst_links": self.shells[i].get_gst_links(),
                }
            )


class Animation:
    """
    VTK animation of the constellation
    """

    def __init__(
        self,
        animation_conn: MultiprocessingConnection,
        draw_links: bool = True,
        frequency: int = 7,
    ):
        """
        Initialize the animation

        Like me, you might wonder what the numerous vkt calls are for.
        Answer: you need to manually configure a render pipeline for
        each object (vtk actor) in the scene.
        A typical VTK render pipeline:

        point data array   <-- set/update position data
            |
        poly data array
            |
        poly data mapper
            |
        object actor   <-- edit color/size/opacity, apply rotations/translations
            |
        vtk renderer
            |
        vkt render window
        vkt render interactor   <-- trigger events, animate
            |
        Your computer screen

        :param animation_conn: The connection to the animation process.
        :param draw_links: Whether to draw links in the animation.
        :param frequency: The frequency of the animation.
        """
        self.initialized = False
        self.conn = animation_conn
        init = self.conn.recv()
        if init["type"] != "init":
            raise ValueError("Animation: did not receive init message first!")

        num_shells: int = init["num_shells"]
        total_sats: typing.List[int] = init["total_sats"]
        sat_positions: typing.List[
            typing.List[typing.Dict[str, typing.Union[float, bool]]]
        ] = init["sat_positions"]
        links: typing.List[
            typing.List[typing.Dict[str, typing.Union[float, int, bool]]]
        ] = init["links"]

        # print(f"Animation: initializing with links {links}")

        gst_positions: typing.List[typing.Dict[str, float]] = init["gst_positions"]
        gst_links: typing.List[
            typing.List[typing.Dict[str, typing.Union[float, int, bool]]]
        ] = init["gst_links"]

        self.num_shells = num_shells

        # print(f"Animation: initializing with {num_shells} shells")

        self.shell_sats = total_sats
        self.sat_positions = sat_positions
        self.links = links

        self.gst_positions = gst_positions
        self.gst_links = gst_links

        self.current_simulation_time = 0
        self.last_animate = 0
        self.frequency = frequency
        self.frameCount = 0

        self.makeEarthActor(EARTH_RADIUS_M)

        self.shell_actors = []
        self.shell_inactive_actors = []

        self.isl_actors = []

        for i in range(self.num_shells):
            self.shell_actors.append(types.SimpleNamespace())
            self.shell_inactive_actors.append(types.SimpleNamespace())
            self.isl_actors.append(types.SimpleNamespace())

        self.sat_colors = sns.color_palette(n_colors=self.num_shells)
        self.isl_colors = sns.color_palette(n_colors=self.num_shells, desat=0.5)

        self.draw_links = draw_links

        for shell in range(self.num_shells):
            self.makeSatsActor(shell, self.shell_sats[shell])
            self.makeInactiveSatsActor(shell, self.shell_sats[shell])
            if self.draw_links:
                self.makeLinkActors(shell, self.shell_sats[shell])

        self.gst_num = len(self.gst_positions)
        self.gst_actor = types.SimpleNamespace()
        self.gst_link_actor = types.SimpleNamespace()

        self.lock = td.Lock()

        # print(f"Animation: initializing with {self.gst_num} ground stations")

        self.makeGstActor(self.gst_num)
        if self.draw_links:
            self.makeGstLinkActors(self.gst_num)

        self.controlThread = td.Thread(target=self.controlThreadHandler)
        self.controlThread.start()

        self.makeRenderWindow()

    ###############################################################################
    #                           ANIMATION FUNCTIONS                               #
    ###############################################################################

    """
 
    """

    def _updateAnimation(self, obj: typing.Any, event: typing.Any) -> None:
        """
        This function is a wrapper to call the updateAnimation function with a lock.

        :param obj: The object that generated the event, probably vtk render window.
        :param event: The event that triggered this function.
        """
        with self.lock:
            self.updateAnimation(obj, event)

    def updateAnimation(self, obj: typing.Any, event: typing.Any) -> None:
        """
        This function takes in new position data and updates the render window

        :param obj: The object that generated the event, probably vtk render window.
        :param event: The event that triggered this function.
        """

        # rotate earth and land

        steps_to_animate = self.current_simulation_time - self.last_animate

        self.last_animate = self.current_simulation_time

        rotation_per_time_step = 360.0 / (SECONDS_PER_DAY) * steps_to_animate
        self.earthActor.RotateZ(rotation_per_time_step)
        self.sphereActor.RotateZ(rotation_per_time_step)

        # update sat points
        for s in range(self.num_shells):
            for i in range(self.shell_sats[s]):
                x = float(self.sat_positions[s][i]["x"])
                y = float(self.sat_positions[s][i]["y"])
                z = float(self.sat_positions[s][i]["z"])

                if self.sat_positions[s][i]["in_bbox"]:
                    self.shell_actors[s].satVtkPts.SetPoint(
                        self.shell_actors[s].satPointIDs[i], x, y, z
                    )
                    self.shell_inactive_actors[s].satVtkPts.SetPoint(
                        self.shell_actors[s].satPointIDs[i], 0, 0, 0
                    )
                else:
                    self.shell_actors[s].satVtkPts.SetPoint(
                        self.shell_actors[s].satPointIDs[i], 0, 0, 0
                    )
                    self.shell_inactive_actors[s].satVtkPts.SetPoint(
                        self.shell_actors[s].satPointIDs[i], x, y, z
                    )

            self.shell_actors[s].satPolyData.GetPoints().Modified()
            self.shell_inactive_actors[s].satPolyData.GetPoints().Modified()

            if self.draw_links:
                # grab the arrays of connections
                links = [x for x in self.links[s] if x["active"]]

                # build a vtkPoints object from array
                self.isl_actors[s].linkPoints = vtk.vtkPoints()
                self.isl_actors[s].linkPoints.SetNumberOfPoints(self.shell_sats[s])
                for i in range(self.shell_sats[s]):
                    x = self.sat_positions[s][i]["x"]
                    y = self.sat_positions[s][i]["y"]
                    z = self.sat_positions[s][i]["z"]
                    self.isl_actors[s].linkPoints.SetPoint(i, x, y, z)

                # make clean line arrays
                self.isl_actors[s].islLinkLines = vtk.vtkCellArray()

                # fill isl and gsl arrays
                for i in range(len(links)):
                    e1 = links[i]["node_1"]
                    e2 = links[i]["node_2"]
                    # must translate link endpoints to point names
                    self.isl_actors[s].islLinkLines.InsertNextCell(2)
                    self.isl_actors[s].islLinkLines.InsertCellPoint(e1)
                    self.isl_actors[s].islLinkLines.InsertCellPoint(e2)

                self.isl_actors[s].islPolyData.SetPoints(self.isl_actors[s].linkPoints)
                self.isl_actors[s].islPolyData.SetLines(self.isl_actors[s].islLinkLines)

        # update gst points and links
        for i in range(len(self.gst_positions)):
            x = self.gst_positions[i]["x"]
            y = self.gst_positions[i]["y"]
            z = self.gst_positions[i]["z"]
            self.gst_actor.gstVtkPts.SetPoint(self.gst_actor.gstPointIDs[i], x, y, z)

        self.gst_actor.gstPolyData.GetPoints().Modified()

        if self.draw_links:
            # build a vtkPoints object from array
            self.gst_link_actor.gstLinkPoints = vtk.vtkPoints()
            self.gst_link_actor.gstLinkPoints.SetNumberOfPoints(
                self.gst_num + sum(self.shell_sats)
            )

            for i in range(self.gst_num):
                x = self.gst_positions[i]["x"]
                y = self.gst_positions[i]["y"]
                z = self.gst_positions[i]["z"]
                self.gst_link_actor.gstLinkPoints.SetPoint(i, x, y, z)

            num_points = self.gst_num

            for s in range(self.num_shells):
                for i in range(self.shell_sats[s]):
                    x = self.sat_positions[s][i]["x"]
                    y = self.sat_positions[s][i]["y"]
                    z = self.sat_positions[s][i]["z"]
                    self.gst_link_actor.gstLinkPoints.SetPoint(num_points, x, y, z)
                    num_points += 1

            # make clean line arrays
            self.gst_link_actor.gstLinkLines = vtk.vtkCellArray()

            # fill gsl arrays
            offset = self.gst_num

            for s in range(self.num_shells):
                for i in range(len(self.gst_links[s])):
                    e1 = self.gst_links[s][i]["gst"] * -1 - 1

                    e2 = self.gst_links[s][i]["sat"] + offset

                    # must translate link endpoints to point names
                    self.gst_link_actor.gstLinkLines.InsertNextCell(2)
                    self.gst_link_actor.gstLinkLines.InsertCellPoint(e1)
                    self.gst_link_actor.gstLinkLines.InsertCellPoint(e2)

                offset += self.shell_sats[s]

            self.gst_link_actor.gstLinkPolyData.SetPoints(
                self.gst_link_actor.gstLinkPoints
            )

            self.gst_link_actor.gstLinkPolyData.SetLines(
                self.gst_link_actor.gstLinkLines
            )

        # #
        self.frameCount += 1

        obj.GetRenderWindow().Render()

    def makeRenderWindow(self) -> None:
        """
        Makes a render window object using vtk.

        This should not be called until all the actors are created.
        """

        # create a renderer object
        self.renderer = vtk.vtkRenderer()
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)

        # create an interactor object, to interact with the window... duh
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.interactor.SetRenderWindow(self.renderWindow)

        # add the actor objects
        for actor in self.shell_actors:
            self.renderer.AddActor(actor.satsActor)

        for actor in self.shell_inactive_actors:
            self.renderer.AddActor(actor.inactiveSatsActor)

        self.renderer.AddActor(self.earthActor)
        self.renderer.AddActor(self.sphereActor)

        if self.draw_links:
            for actor in self.isl_actors:
                self.renderer.AddActor(actor.islActor)

        self.renderer.AddActor(self.gst_actor.gstsActor)

        if self.draw_links:
            self.renderer.AddActor(self.gst_link_actor.gstLinkActor)

        # white background, makes it easier to
        # put screenshots of animation into papers/presentations
        self.renderer.SetBackground(BACKGROUND_COLOR)

        self.interactor.Initialize()
        # set up a timer to call the update function at a max rate
        # of every 7 ms (~144 hz)

        self.interactor.AddObserver("TimerEvent", self._updateAnimation)
        self.interactor.CreateRepeatingTimer(self.frequency)

        # start the model
        self.renderWindow.SetSize(2048, 2048)
        self.renderWindow.Render()

        # print("🖍  Animation: ready to return control...")
        # self.conn.send(True)

        self.initialized = True

        self.interactor.Start()

    def makeSatsActor(self, shell_no: int, shell_total_sats: int) -> None:
        """
        generate the point cloud to represent satellites

        :param shell_no: index of this shell
        :param shell_total_satellites: number of satellites in the shell
        """

        # declare a points & cell array to hold position data
        self.shell_actors[shell_no].satVtkPts = vtk.vtkPoints()
        self.shell_actors[shell_no].satVtkVerts = vtk.vtkCellArray()

        # init a array for IDs
        self.shell_actors[shell_no].satPointIDs = [None] * shell_total_sats

        # initialize all the positions
        for i in range(len(self.sat_positions[shell_no])):
            self.shell_actors[shell_no].satPointIDs[i] = self.shell_actors[
                shell_no
            ].satVtkPts.InsertNextPoint(
                self.sat_positions[shell_no][i]["x"],
                self.sat_positions[shell_no][i]["y"],
                self.sat_positions[shell_no][i]["z"],
            )

            self.shell_actors[shell_no].satVtkVerts.InsertNextCell(1)
            self.shell_actors[shell_no].satVtkVerts.InsertCellPoint(
                self.shell_actors[shell_no].satPointIDs[i]
            )

        # convert points into poly data
        # (because that's what they do in the vtk examples)
        self.shell_actors[shell_no].satPolyData = vtk.vtkPolyData()
        self.shell_actors[shell_no].satPolyData.SetPoints(
            self.shell_actors[shell_no].satVtkPts
        )
        self.shell_actors[shell_no].satPolyData.SetVerts(
            self.shell_actors[shell_no].satVtkVerts
        )

        # create mapper object and connect to the poly data
        self.shell_actors[shell_no].satsMapper = vtk.vtkPolyDataMapper()
        self.shell_actors[shell_no].satsMapper.SetInputData(
            self.shell_actors[shell_no].satPolyData
        )

        # create actor, and connect to the mapper
        # (again, its just what you do to make a vtk render pipeline)
        self.shell_actors[shell_no].satsActor = vtk.vtkActor()
        self.shell_actors[shell_no].satsActor.SetMapper(
            self.shell_actors[shell_no].satsMapper
        )

        # edit appearance of satellites
        self.shell_actors[shell_no].satsActor.GetProperty().SetOpacity(SAT_OPACITY)
        self.shell_actors[shell_no].satsActor.GetProperty().SetColor(
            self.sat_colors[shell_no]
        )
        self.shell_actors[shell_no].satsActor.GetProperty().SetPointSize(SAT_POINT_SIZE)

    def makeInactiveSatsActor(self, shell_no: int, shell_total_sats: int) -> None:
        """
        generate the point cloud to represent inactive satellites

        :param shell_no: index of this shell
        :param shell_total_satellites: number of satellites in the shell
        """

        # declare a points & cell array to hold position data
        self.shell_inactive_actors[shell_no].satVtkPts = vtk.vtkPoints()
        self.shell_inactive_actors[shell_no].satVtkVerts = vtk.vtkCellArray()

        # init a array for IDs
        self.shell_inactive_actors[shell_no].satPointIDs = [None] * shell_total_sats

        # initialize all the positions
        for i in range(len(self.sat_positions[shell_no])):
            self.shell_inactive_actors[shell_no].satPointIDs[i] = (
                self.shell_inactive_actors[shell_no].satVtkPts.InsertNextPoint(0, 0, 0)
            )

            self.shell_inactive_actors[shell_no].satVtkVerts.InsertNextCell(1)
            self.shell_inactive_actors[shell_no].satVtkVerts.InsertCellPoint(
                self.shell_inactive_actors[shell_no].satPointIDs[i]
            )

        # convert points into poly data
        # (because that's what they do in the vtk examples)
        self.shell_inactive_actors[shell_no].satPolyData = vtk.vtkPolyData()
        self.shell_inactive_actors[shell_no].satPolyData.SetPoints(
            self.shell_inactive_actors[shell_no].satVtkPts
        )
        self.shell_inactive_actors[shell_no].satPolyData.SetVerts(
            self.shell_inactive_actors[shell_no].satVtkVerts
        )

        # create mapper object and connect to the poly data
        self.shell_inactive_actors[shell_no].satsMapper = vtk.vtkPolyDataMapper()
        self.shell_inactive_actors[shell_no].satsMapper.SetInputData(
            self.shell_inactive_actors[shell_no].satPolyData
        )

        # create actor, and connect to the mapper
        # (again, its just what you do to make a vtk render pipeline)
        self.shell_inactive_actors[shell_no].inactiveSatsActor = vtk.vtkActor()
        self.shell_inactive_actors[shell_no].inactiveSatsActor.SetMapper(
            self.shell_inactive_actors[shell_no].satsMapper
        )

        # edit appearance of satellites
        self.shell_inactive_actors[shell_no].inactiveSatsActor.GetProperty().SetOpacity(
            SAT_INACTIVE_OPACITY
        )
        self.shell_inactive_actors[shell_no].inactiveSatsActor.GetProperty().SetColor(
            self.sat_colors[shell_no]
        )
        self.shell_inactive_actors[
            shell_no
        ].inactiveSatsActor.GetProperty().SetPointSize(SAT_POINT_SIZE)

    def makeLinkActors(self, shell_no: int, shell_total_satellites: int) -> None:
        """
        generate the lines to represent links

        source:
        https://vtk.org/Wiki/VTK/Examples/Python/GeometricObjects/Display/PolyLine

        :param shell_no: index of this shell
        :param shell_total_satellites: number of satellites in the shell
        """

        # build a vtkPoints object from array
        self.isl_actors[shell_no].linkPoints = vtk.vtkPoints()
        self.isl_actors[shell_no].linkPoints.SetNumberOfPoints(shell_total_satellites)

        for i in range(len(self.sat_positions[shell_no])):
            self.isl_actors[shell_no].linkPoints.SetPoint(
                i,
                self.sat_positions[shell_no][i]["x"],
                self.sat_positions[shell_no][i]["y"],
                self.sat_positions[shell_no][i]["z"],
            )

        # build a cell array to represent connectivity
        self.isl_actors[shell_no].islLinkLines = vtk.vtkCellArray()
        for i in range(len(self.links[shell_no])):
            e1 = self.links[shell_no][i]["node_1"]
            e2 = self.links[shell_no][i]["node_2"]
            # must translate link endpoints to point names
            self.isl_actors[shell_no].islLinkLines.InsertNextCell(2)
            self.isl_actors[shell_no].islLinkLines.InsertCellPoint(e1)
            self.isl_actors[shell_no].islLinkLines.InsertCellPoint(e2)

        self.isl_actors[
            shell_no
        ].pathLinkLines = vtk.vtkCellArray()  # init, but do not fill this one

        # #

        self.isl_actors[shell_no].islPolyData = vtk.vtkPolyData()
        self.isl_actors[shell_no].islPolyData.SetPoints(
            self.isl_actors[shell_no].linkPoints
        )
        self.isl_actors[shell_no].islPolyData.SetLines(
            self.isl_actors[shell_no].islLinkLines
        )

        # #

        self.isl_actors[shell_no].islMapper = vtk.vtkPolyDataMapper()
        self.isl_actors[shell_no].islMapper.SetInputData(
            self.isl_actors[shell_no].islPolyData
        )

        # #

        self.isl_actors[shell_no].islActor = vtk.vtkActor()
        self.isl_actors[shell_no].islActor.SetMapper(
            self.isl_actors[shell_no].islMapper
        )

        # #

        self.isl_actors[shell_no].islActor.GetProperty().SetOpacity(ISL_LINK_OPACITY)
        self.isl_actors[shell_no].islActor.GetProperty().SetColor(
            self.isl_colors[shell_no]
        )
        self.isl_actors[shell_no].islActor.GetProperty().SetLineWidth(ISL_LINE_WIDTH)

        # #

    def makeGstActor(self, gst_num: int) -> None:
        """
        generate the point cloud to represent ground stations

        :param gst_num: number of ground stations
        """

        # declare a points & cell array to hold position data
        self.gst_actor.gstVtkPts = vtk.vtkPoints()
        self.gst_actor.gstVtkVerts = vtk.vtkCellArray()

        # init a array for IDs
        self.gst_actor.gstPointIDs = [None] * gst_num

        # initialize all the positions
        for i in range(len(self.gst_positions)):
            self.gst_actor.gstPointIDs[i] = self.gst_actor.gstVtkPts.InsertNextPoint(
                self.gst_positions[i]["x"],
                self.gst_positions[i]["y"],
                self.gst_positions[i]["z"],
            )

            self.gst_actor.gstVtkVerts.InsertNextCell(1)
            self.gst_actor.gstVtkVerts.InsertCellPoint(self.gst_actor.gstPointIDs[i])

        # convert points into poly data
        # (because that's what they do in the vtk examples)
        self.gst_actor.gstPolyData = vtk.vtkPolyData()
        self.gst_actor.gstPolyData.SetPoints(self.gst_actor.gstVtkPts)
        self.gst_actor.gstPolyData.SetVerts(self.gst_actor.gstVtkVerts)

        # create mapper object and connect to the poly data
        self.gst_actor.gstsMapper = vtk.vtkPolyDataMapper()
        self.gst_actor.gstsMapper.SetInputData(self.gst_actor.gstPolyData)

        # create actor, and connect to the mapper
        # (again, its just what you do to make a vtk render pipeline)
        self.gst_actor.gstsActor = vtk.vtkActor()
        self.gst_actor.gstsActor.SetMapper(self.gst_actor.gstsMapper)

        # edit appearance of satellites
        self.gst_actor.gstsActor.GetProperty().SetOpacity(GST_OPACITY)
        self.gst_actor.gstsActor.GetProperty().SetColor(GST_COLOR)
        self.gst_actor.gstsActor.GetProperty().SetPointSize(GST_POINT_SIZE)

        # #

    # make this for all shells as well?
    def makeGstLinkActors(self, gst_num: int) -> None:
        """
        generate the links to represent ground stations links

        :param gst_num: number of ground stations
        """

        # build a vtkPoints object from array
        self.gst_link_actor.gstLinkPoints = vtk.vtkPoints()
        self.gst_link_actor.gstLinkPoints.SetNumberOfPoints(
            gst_num + sum(self.shell_sats)
        )

        # add gsts
        for i in range(self.gst_num):
            x = self.gst_positions[i]["x"]
            y = self.gst_positions[i]["y"]
            z = self.gst_positions[i]["z"]
            self.gst_link_actor.gstLinkPoints.SetPoint(i, x, y, z)

        # add all satellites?
        num_points = self.gst_num

        for s in range(self.num_shells):
            for i in range(self.shell_sats[s]):
                x = self.sat_positions[s][i]["x"]
                y = self.sat_positions[s][i]["y"]
                z = self.sat_positions[s][i]["z"]
                self.gst_link_actor.gstLinkPoints.SetPoint(num_points, x, y, z)
                num_points += 1

        # build a cell array to represent connectivity
        self.gst_link_actor.gstLinkLines = vtk.vtkCellArray()

        offset = self.gst_num

        for s in range(self.num_shells):
            for i in range(len(self.gst_links[s])):
                e1 = self.gst_links[s][i]["gst"] * -1 - 1

                e2 = self.gst_links[s][i]["sat"] + offset

                # must translate link endpoints to point names
                self.gst_link_actor.gstLinkLines.InsertNextCell(2)
                self.gst_link_actor.gstLinkLines.InsertCellPoint(e1)
                self.gst_link_actor.gstLinkLines.InsertCellPoint(e2)

            offset += self.shell_sats[s]

        # #

        self.gst_link_actor.gstLinkPolyData = vtk.vtkPolyData()
        self.gst_link_actor.gstLinkPolyData.SetPoints(self.gst_link_actor.gstLinkPoints)
        self.gst_link_actor.gstLinkPolyData.SetLines(self.gst_link_actor.gstLinkLines)

        # #

        self.gst_link_actor.gstLinkMapper = vtk.vtkPolyDataMapper()
        self.gst_link_actor.gstLinkMapper.SetInputData(
            self.gst_link_actor.gstLinkPolyData
        )

        # #

        self.gst_link_actor.gstLinkActor = vtk.vtkActor()
        self.gst_link_actor.gstLinkActor.SetMapper(self.gst_link_actor.gstLinkMapper)

        # #

        self.gst_link_actor.gstLinkActor.GetProperty().SetOpacity(GST_LINK_OPACITY)
        self.gst_link_actor.gstLinkActor.GetProperty().SetColor(GST_LINK_COLOR)
        self.gst_link_actor.gstLinkActor.GetProperty().SetLineWidth(GST_LINE_WIDTH)

        # #

    def makeEarthActor(self, earth_radius: int) -> None:
        """
        generate the earth sphere, and the landmass outline

        :param earth_radius: radius of the earth in meters
        """

        self.earthRadius = earth_radius

        # Create earth map
        # a point cloud that outlines all the earths landmass
        self.earthSource = vtk.vtkEarthSource()
        # draws as an outline of landmass, rather than fill it in
        # self.earthSource.OutlineOn()

        # want this to be slightly larger than the sphere it sits on
        # so that it is not occluded by the sphere
        self.earthSource.SetRadius(self.earthRadius * 1.001)

        # controles the resolution of surface data (1 = full resolution)
        self.earthSource.SetOnRatio(1)

        # Create a mapper
        self.earthMapper = vtk.vtkPolyDataMapper()
        self.earthMapper.SetInputConnection(self.earthSource.GetOutputPort())

        # Create an actor
        self.earthActor = vtk.vtkActor()
        self.earthActor.SetMapper(self.earthMapper)

        # set color
        self.earthActor.GetProperty().SetColor(LANDMASS_OUTLINE_COLOR)
        self.earthActor.GetProperty().SetOpacity(EARTH_LAND_OPACITY)

        # make sphere data
        num_pts = EARTH_SPHERE_POINTS
        indices = np.arange(0, num_pts, dtype=float) + 0.5
        phi = np.arccos(1 - 2 * indices / num_pts)
        theta = np.pi * (1 + 5**0.5) * indices
        x = np.cos(theta) * np.sin(phi) * self.earthRadius
        y = np.sin(theta) * np.sin(phi) * self.earthRadius
        z = np.cos(phi) * self.earthRadius

        # x,y,z is coordination of evenly distributed sphere
        # I will try to make poly data use this x,y,z
        points = vtk.vtkPoints()
        for i in range(len(x)):
            points.InsertNextPoint(x[i], y[i], z[i])

        poly = vtk.vtkPolyData()
        poly.SetPoints(points)

        # To create surface of a sphere we need to use Delaunay triangulation
        d3D = vtk.vtkDelaunay3D()
        d3D.SetInputData(poly)  # This generates a 3D mesh

        # We need to extract the surface from the 3D mesh
        dss = vtk.vtkDataSetSurfaceFilter()
        dss.SetInputConnection(d3D.GetOutputPort())
        dss.Update()

        # Now we have our final polydata
        spherePoly = dss.GetOutput()

        # Create a mapper
        sphereMapper = vtk.vtkPolyDataMapper()
        sphereMapper.SetInputData(spherePoly)

        # Create an actor
        self.sphereActor = vtk.vtkActor()
        self.sphereActor.SetMapper(sphereMapper)

        # set color
        self.sphereActor.GetProperty().SetColor(EARTH_BASE_COLOR)
        self.sphereActor.GetProperty().SetOpacity(EARTH_OPACITY)

    def controlThreadHandler(self) -> None:
        """
        Start a thread to deal with inter-process communications
        """
        while not self.initialized:
            pass

        while True:
            received_data = self.conn.recv()
            # either update constellation time
            # or update status of a shell
            command = received_data["type"]
            if command == "time":
                with self.lock:
                    self.current_simulation_time = received_data["time"]
                    # print(f"Animation: time is now {self.current_simulation_time}")
            if command == "shell":
                with self.lock:
                    shell = received_data["shell"]
                    # print(f"Animation: updating shell {shell}")
                    self.sat_positions[shell] = received_data["sat_positions"]
                    # print(
                    #     f"Animation: updated shell {shell} sat positions: {self.sat_positions[shell]}"
                    # )
                    self.links[shell] = received_data["links"]
                    # print(f"Animation: updated shell {shell} links: {self.links[shell]}")
                    self.gst_links[shell] = received_data["gst_links"]
                    # print(
                    #     f"Animation: updated shell {shell} gst links: {self.gst_links[shell]}"
                    # )

                    if shell == 0:
                        self.gst_positions = received_data["gst_positions"]
