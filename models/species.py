from pydantic import BaseModel


class SpeciesState(BaseModel):
    image: str
    width: int
    height: int


class Species(BaseModel):
    name: str
    id: str
    states: dict[str, SpeciesState]
