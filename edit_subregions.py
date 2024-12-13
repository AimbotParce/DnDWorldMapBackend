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
from models.region import RegionImage, Subregion

WORLDS_FOLDER = Path(WORLDS_FOLDER)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--world", type=str, required=True, choices=list(map(lambda w: w["id"], loadWorlds())))
    parser.add_argument("--region", type=str, required=True)
    args = parser.parse_args()

    WORLD: str = args.world
    REGION: str = args.region

    # Check if the region exists
    region_path = WORLDS_FOLDER / WORLD / "regions" / f"{REGION}.yaml"
    if not region_path.exists():
        raise FileNotFoundError(f"Region not found: {region_path}")
    # Load the region yaml file
    region = yaml.safe_load(region_path.read_text())
    # Get the image path
    image_data = region["states"]["default"]["image"]

    image_path = WORLDS_FOLDER / WORLD / "images" / image_data["path"]
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    class InteractiveSubregionPlacing:
        def __init__(
            self,
            image_path: Path,
            top_left_corner: list[float, float],
            height: float,
            width: float,
            subregions: list[Subregion],
        ):
            self.fig, self.ax = plt.subplots()
            self.ax.set_aspect("equal")

            self.image_data = plt.imread(str(image_path))
            self.image = self.ax.imshow(
                self.image_data,
                extent=[
                    top_left_corner[0],
                    top_left_corner[0] + width,
                    top_left_corner[1] + height,
                    top_left_corner[1],
                ],
            )

            self.subregions = subregions
            self.selected_subregion: int = None
            self.dragging_point: tuple[int, int] = None  # (subregion index, point index)
            self.scatters: list[plt.PathCollection] = [None] * len(subregions)
            self.fills: list[plt.Polygon] = [None] * len(subregions)

            # Connect mouse events
            self.cid_click = self.fig.canvas.mpl_connect("button_press_event", self.on_click)
            self.cid_release = self.fig.canvas.mpl_connect("button_release_event", self.on_release)
            self.cid_motion = self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
            self.cid_scroll = self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
            self.cid_move_map = self.fig.canvas.mpl_connect("key_press_event", self.on_key_press)

        def draw_all(self):
            for scatter in self.scatters:
                if scatter is not None:
                    scatter.remove()
            for fill in self.fills:
                if fill is not None:
                    fill.remove()
            self.scatters = [None] * len(self.subregions)
            self.fills = [None] * len(self.subregions)

            for i, subregion in enumerate(self.subregions):
                if len(subregion["polygon"]) == 0:
                    continue
                if i == self.selected_subregion:
                    if subregion["visible"]:
                        color = "lightgreen"
                    else:
                        color = "pink"
                else:
                    if subregion["visible"]:
                        color = "green"
                    else:
                        color = "red"

                if len(subregion["polygon"]) >= 3:
                    self.fills[i] = self.ax.fill(*zip(*subregion["polygon"]), color=color, alpha=0.2)[0]
                self.scatters[i] = self.ax.plot(*zip(*subregion["polygon"]), color=color, marker="o")[0]
            self.fig.canvas.draw_idle()

        def on_click(self, event: MouseEvent):
            if event.inaxes != self.ax:
                return

            elif event.button == 1:
                size = 0.02 * (self.ax.get_xlim()[1] - self.ax.get_xlim()[0])
                # Check whether I am dragging
                for i, subregion in enumerate(self.subregions):
                    for j, point in enumerate(subregion["polygon"]):
                        if np.linalg.norm(np.array([event.xdata, event.ydata]) - np.array(point)) < size:
                            if event.button == 3:
                                self.dragging_point = None
                            self.dragging_point = [i, j]
                            return

                # Add a point to the selected subregion
                if self.selected_subregion is not None:
                    self.subregions[self.selected_subregion]["polygon"].append(
                        [float(event.xdata), float(event.ydata)]
                    )
                    self.draw_all()

            elif event.button == 3:  # Right click
                # Remove last point from the selected subregion
                if self.selected_subregion is not None:
                    self.subregions[self.selected_subregion]["polygon"].pop()
                    self.draw_all()

        def on_release(self, event: MouseEvent):
            self.dragging_point = None

        def on_motion(self, event: MouseEvent):
            if self.dragging_point is not None and event.inaxes == self.ax:
                # Update position of the dragged point
                i, j = self.dragging_point
                self.subregions[i]["polygon"][j] = [float(event.xdata), float(event.ydata)]
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
            elif event.key == "m":
                # Next subregion
                if len(self.subregions) == 0:
                    return
                if self.selected_subregion is not None:
                    self.selected_subregion = (self.selected_subregion + 1) % len(self.subregions)
                else:
                    self.selected_subregion = 0

                self.draw_all()
            elif event.key == "n":
                # Previous subregion
                if len(self.subregions) == 0:
                    return
                if self.selected_subregion is not None:
                    self.selected_subregion = (self.selected_subregion - 1) % len(self.subregions)
                else:
                    self.selected_subregion = 0

                self.draw_all()

            elif event.key == "enter":
                # Prompt for subregion name
                region_name = input("Subregion name: ")
                if region_name == "":
                    region_name = None

                self.subregions.append(
                    Subregion(
                        region=region_name,
                        polygon=[],
                        visible=True,
                    )
                )
                self.selected_subregion = len(self.subregions) - 1
                self.draw_all()

            self.fig.canvas.draw_idle()

        def show(self):
            plt.show()

    plot = InteractiveSubregionPlacing(
        image_path=image_path,
        height=image_data["height"],
        width=image_data["width"],
        top_left_corner=image_data["top_left_corner"],
        subregions=region["subregions"],
    )
    plot.show()

    # Save the region
    region_path = WORLDS_FOLDER / WORLD / "regions" / f"{region['id']}.yaml"
    region_path.write_text(yaml.dump(region))
    print(f"Region saved at {region_path}")
