from pydantic import BaseModel

from ._basic import Point2D


class Creature(BaseModel):
    name: str
    id: str
    species: str
    current_state: str
    visible: bool
    current_region: str
    position: Point2D


class VisibleCreature(BaseModel):
    name: str
    position: Point2D
    image: str
    height: int
    width: int
