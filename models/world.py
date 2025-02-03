from pydantic import BaseModel


class World(BaseModel):
    id: str
    name: str
    current_region: str


class VisibleWorld(BaseModel):
    name: str
