from pydantic import BaseModel

from ._basic import Point2D


class Grid(BaseModel):
    type: str
    size: int


class RegionImage(BaseModel):
    path: str
    top_left_corner: Point2D
    width: int
    height: int


class RegionState(BaseModel):
    image: RegionImage


class Subregion(BaseModel):
    region: str
    polygon: list[Point2D]
    visible: bool


class Region(BaseModel):
    name: str
    id: str
    grid: None | Grid
    states: dict[str, RegionState]
    current_state: str
    visible: bool
    subregions: list[Subregion]


class VisibleRegion(BaseModel):
    name: str
    grid: None | Grid
    image: RegionImage
    fog_of_war: list[list[Point2D]]
