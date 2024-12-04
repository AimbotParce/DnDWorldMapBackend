from typing import TypedDict


class World(TypedDict):
    id: str
    name: str
    current_region: str


class VisibleWorld(TypedDict):
    name: str
