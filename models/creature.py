from typing import TypedDict

from ._basic import Point2D


class Creature(TypedDict):
    name: str
    id: str
    species: str
    current_state: str
    visible: bool
    current_region: str
    position: Point2D


class VisibleCreature(TypedDict):
    name: str
    position: Point2D
    image: str
    height: int
    width: int
