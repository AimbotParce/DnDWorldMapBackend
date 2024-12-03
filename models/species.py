from typing import TypedDict


class SpeciesState(TypedDict):
    image: str
    width: int
    height: int


class Species(TypedDict):
    name: str
    id: str
    states: dict[str, SpeciesState]
