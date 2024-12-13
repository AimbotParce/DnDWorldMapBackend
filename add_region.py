import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.backend_bases import KeyEvent, MouseEvent
from matplotlib.ticker import MultipleLocator

from api.constants import WORLDS_FOLDER
from api.helper_functions import loadWorlds

WORLDS_FOLDER = Path(WORLDS_FOLDER)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--world", type=str, required=True, choices=list(map(lambda w: w["id"], loadWorlds())))
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--id", type=str, required=False, default=None, help="If not provided, it will be generated")
    parser.add_argument("--grid-type", type=str, required=False, choices=["hex", "square", "none"], default="none")
    parser.add_argument("--grid-size", type=float, required=False, default=1.0)
    parser.add_argument("--image-path", type=Path, required=True)
    parser.add_argument("--fogged", "-f", action="store_true")
    args = parser.parse_args()

    WORLD: str = args.world
    NAME: str = args.name
    ID: str = args.id
    GRID_TYPE: Literal["hex", "square", "none"] = args.grid_type
    GRID_SIZE: float = args.grid_size
    IMAGE_PATH: Path = args.image_path
    FOGGED: bool = args.fogged

    region = {
        "name": NAME,
        "grid": None,
        "current_state": "default",
        "states": {},
        "visible": not FOGGED,
        "subregions": [],
    }

    if ID is not None:
        region["id"] = ID
    else:
        region["id"] = NAME.lower().replace(" ", "_")

    if GRID_TYPE != "none":
        region["grid"] = {"type": GRID_TYPE, "size": GRID_SIZE}

    new_image_path = (WORLDS_FOLDER / WORLD / "images" / "regions" / f"{region['id']}_default").with_suffix(
        IMAGE_PATH.suffix
    )

    # Setup the default_state
    default_state_image = {
        # Change the sep to be "/"
        "path": str(new_image_path.relative_to(WORLDS_FOLDER / WORLD / "images")).replace(os.sep, "/"),
        # "top_left_corner": [0, 0],
        # "width": 0,
        # "height": 0,
    }

    # Make the user place the image on top of the grid

    class InteractiveMapPlacing:
        def __init__(self, image_path: Path, grid_size: float = 1.0):
            self.fig, self.ax = plt.subplots()
            self.ax.grid(True)
            self.ax.set_aspect("equal")

            self.image_data = plt.imread(str(image_path))
            self.image: plt.AxesImage = None
            self.top_left_corner: list[float, float] = None
            self.bottom_right_corner: list[float, float] = None
            self.top_left_scatter: plt.PathCollection = None
            self.bottom_right_scatter: plt.PathCollection = None

            self.dragging_point = None

            self.ax.set_xlim(0, 20)
            self.ax.set_ylim(20, 0)

            self.ax.xaxis.set_major_locator(MultipleLocator(grid_size))
            self.ax.yaxis.set_major_locator(MultipleLocator(grid_size))

            # Connect mouse events
            self.cid_click = self.fig.canvas.mpl_connect("button_press_event", self.on_click)
            self.cid_release = self.fig.canvas.mpl_connect("button_release_event", self.on_release)
            self.cid_motion = self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
            self.cid_scroll = self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
            self.cid_move_map = self.fig.canvas.mpl_connect("key_press_event", self.on_key_press)

        def draw_all(self):
            if self.top_left_scatter:
                self.top_left_scatter.remove()
                self.top_left_scatter = None
            if self.bottom_right_scatter:
                self.bottom_right_scatter.remove()
                self.bottom_right_scatter = None
            if self.image:
                self.image.remove()
                self.image = None

            if self.top_left_corner:
                self.top_left_scatter = self.ax.scatter(*self.top_left_corner, color="red")
            if self.bottom_right_corner:
                self.bottom_right_scatter = self.ax.scatter(*self.bottom_right_corner, color="blue")
            if self.top_left_corner and self.bottom_right_corner:
                self.image = self.ax.imshow(
                    self.image_data,
                    extent=[
                        self.top_left_corner[0],
                        self.bottom_right_corner[0],
                        self.bottom_right_corner[1],
                        self.top_left_corner[1],
                    ],
                )
            elif self.top_left_corner:
                self.image = self.ax.imshow(
                    self.image_data,
                    extent=[
                        self.top_left_corner[0],
                        self.top_left_corner[0] + self.image_data.shape[1] / 100,
                        self.top_left_corner[1] + self.image_data.shape[0] / 100,
                        self.top_left_corner[1],
                    ],
                )

            self.fig.canvas.draw_idle()

        def on_click(self, event: MouseEvent):
            if event.inaxes != self.ax:
                return

            if event.button == 3:
                if self.bottom_right_corner is not None:
                    self.bottom_right_corner = None
                elif self.top_left_corner is not None:
                    self.top_left_corner = None
            elif event.button == 1:
                size = 0.02 * (self.ax.get_xlim()[1] - self.ax.get_xlim()[0])
                # Check whether I am dragging
                if (
                    self.top_left_corner is not None
                    and np.linalg.norm(np.array([event.xdata, event.ydata]) - np.array(self.top_left_corner)) < size
                ):
                    self.dragging_point = "top_left"
                elif (
                    self.bottom_right_corner is not None
                    and np.linalg.norm(np.array([event.xdata, event.ydata]) - np.array(self.bottom_right_corner))
                    < size
                ):
                    self.dragging_point = "bottom_right"
                else:
                    self.dragging_point = None
                    if self.top_left_corner is None:
                        self.top_left_corner = [event.xdata, event.ydata]
                    elif self.bottom_right_corner is None:
                        self.bottom_right_corner = [event.xdata, event.ydata]
            self.draw_all()

        def on_release(self, event: MouseEvent):
            self.dragging_point = None

        def on_motion(self, event: MouseEvent):
            if self.dragging_point is not None and event.inaxes == self.ax:
                # Update position of the dragged point
                if self.dragging_point == "top_left":
                    self.top_left_corner = [event.xdata, event.ydata]
                elif self.dragging_point == "bottom_right":
                    self.bottom_right_corner = [event.xdata, event.ydata]
                self.draw_all()

        def on_scroll(self, event: MouseEvent):
            if event.inaxes == self.ax:
                if event.button == "up":
                    self.ax.set_xlim(self.ax.get_xlim()[0] * 0.9, self.ax.get_xlim()[1] * 0.9)
                    self.ax.set_ylim(self.ax.get_ylim()[0] * 0.9, self.ax.get_ylim()[1] * 0.9)
                elif event.button == "down":
                    self.ax.set_xlim(self.ax.get_xlim()[0] * 1.1, self.ax.get_xlim()[1] * 1.1)
                    self.ax.set_ylim(self.ax.get_ylim()[0] * 1.1, self.ax.get_ylim()[1] * 1.1)
                self.fig.canvas.draw_idle()

        def on_key_press(self, event: KeyEvent):
            deltay = (self.ax.get_ylim()[1] - self.ax.get_ylim()[0]) / 20
            deltax = (self.ax.get_xlim()[1] - self.ax.get_xlim()[0]) / 20
            if event.key == "up":
                self.ax.set_ylim(self.ax.get_ylim()[0] + deltay, self.ax.get_ylim()[1] + deltay)
            elif event.key == "down":
                self.ax.set_ylim(self.ax.get_ylim()[0] - deltay, self.ax.get_ylim()[1] - deltay)
            elif event.key == "left":
                self.ax.set_xlim(self.ax.get_xlim()[0] - deltax, self.ax.get_xlim()[1] - deltax)
            elif event.key == "right":
                self.ax.set_xlim(self.ax.get_xlim()[0] + deltax, self.ax.get_xlim()[1] + deltax)

            self.fig.canvas.draw_idle()

        def show(self):
            plt.show()

    plot = InteractiveMapPlacing(image_path=IMAGE_PATH, grid_size=GRID_SIZE)
    plot.show()

    if plot.top_left_corner is not None:
        width = plot.image_data.shape[1] / 100
        height = plot.image_data.shape[0] / 100
        if plot.bottom_right_corner is not None:
            width = plot.bottom_right_corner[0] - plot.top_left_corner[0]
            height = plot.bottom_right_corner[1] - plot.top_left_corner[1]
        default_state_image["top_left_corner"] = list(map(float, plot.top_left_corner))
        default_state_image["width"] = float(width)
        default_state_image["height"] = float(height)
    else:
        raise ValueError("You need to place the image on the map")

    region["states"]["default"] = {"image": default_state_image}

    # Copy the image to the world folder
    new_image_path.parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(new_image_path, plot.image_data)
    print(f"Image saved at {new_image_path}")
    # Save the region
    region_path = WORLDS_FOLDER / WORLD / "regions" / f"{region['id']}.yaml"
    region_path.write_text(yaml.dump(region))
    print(f"Region saved at {region_path}")
