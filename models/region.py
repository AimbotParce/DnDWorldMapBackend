from typing import TypedDict

from ._basic import Point2D


class Grid(TypedDict):
    type: str
    size: int


class RegionImage(TypedDict):
    path: str
    top_left_corner: Point2D
    width: int
    height: int


class RegionState(TypedDict):
    image: RegionImage


class Subregion(TypedDict):
    region: str
    polygon: list[Point2D]
    visible: bool


class Region(TypedDict):
    name: str
    id: str
    grid: None | Grid
    states: dict[str, RegionState]
    current_state: str
    visible: bool
    subregions: list[Subregion]


class VisibleRegion(TypedDict):
    name: str
    grid: None | Grid
    image: RegionImage
    visible_polygon: list[list[Point2D]]
