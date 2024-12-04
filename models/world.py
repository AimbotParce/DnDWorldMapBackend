from typing import TypedDict


class World(TypedDict):
    name: str
    current_region: str


class VisibleWorld(TypedDict):
    name: str
