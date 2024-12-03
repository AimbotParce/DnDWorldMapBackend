import pathlib

import yaml
from shapely.geometry import Polygon

from models import *
from models._basic import Point2D

from .app import app
from .constants import WORLDS_FOLDER


def getWorldPath() -> pathlib.Path:
    world: str | None = app.config["WORLD"]
    if world is None:
        raise ValueError("No world selected")

    res = (pathlib.Path(WORLDS_FOLDER) / world).resolve()
    if not res.exists() and res.is_dir():
        raise FileNotFoundError(f"World folder not found: {res}")
    return res


def loadWorld() -> World:
    world_data = yaml.safe_load((getWorldPath() / "world.yaml").read_text())
    return World(**world_data)


def updateWorld(data: World) -> None:
    (getWorldPath() / "world.yaml").write_text(yaml.dump(data))


def loadFullRegion(region: str) -> Region:
    region_path = (getWorldPath() / "regions" / region).with_suffix(".yaml")
    if not region_path.exists() and region_path.is_file():
        raise FileNotFoundError(f"Region folder not found: {region_path}")
    region_data = yaml.safe_load(region_path.read_text())
    return Region(**region_data)


def loadVisibleRegion(region_name: str) -> VisibleRegion:
    region = loadFullRegion(region_name)
    img_data = region["states"][region["current_state"]]["image"]
    if region["visible"]:
        top_left = img_data["top_left_corner"]
        width = img_data["width"]
        height = img_data["height"]
        visible_polygon = Polygon(
            [
                tuple(top_left),
                (top_left[0] + width, top_left[1]),
                (top_left[0] + width, top_left[1] + height),
                (top_left[0], top_left[1] + height),
            ]
        )
    else:
        visible_polygon = Polygon()

    for subregion in region["subregions"]:
        region_polygon = Polygon(subregion["polygon"])
        if subregion["visible"]:
            visible_polygon = visible_polygon.union(region_polygon)
        else:
            visible_polygon = visible_polygon.difference(region_polygon)

    return VisibleRegion(
        name=region["name"],
        grid=region["grid"],
        image=img_data,
        visible_polygon=visible_polygon.exterior.coords[:-1],  # TO DO: This isn't a single polygon!
    )


def updateRegion(region: Region) -> None:
    region_path = (getWorldPath() / "regions" / region["id"]).with_suffix(".yaml")
    region_path.write_text(yaml.dump(region))


def loadCreatures(region: str) -> list[Creature]:
    creatures_path = getWorldPath() / "creatures"
    if not creatures_path.exists():
        raise FileNotFoundError(f"Creatures folder not found: {creatures_path}")
    creatures = []
    for creature_file in creatures_path.iterdir():
        creature_data = Creature(**yaml.safe_load(creature_file.read_text()))
        if creature_data["current_region"] == region:
            creatures.append(creature_data)

    return creatures


def loadSpecies(species: str) -> Species:
    species_path = (getWorldPath() / "species" / species).with_suffix(".yaml")
    if not species_path.exists():
        raise FileNotFoundError(f"Species folder not found: {species_path}")
    species_data = yaml.safe_load(species_path.read_text())
    return Species(**species_data)


def loadVisibleCreatures(region: str) -> list[VisibleCreature]:
    creatures = loadCreatures(region)
    visible_creatures: list[VisibleCreature] = []
    loaded_species: dict[str, Species] = {}
    for creature in creatures:
        if creature["visible"]:
            if creature["species"] not in loaded_species:
                loaded_species[creature["species"]] = loadSpecies(creature["species"])
            species = loaded_species[creature["species"]]
            visible_creatures.append(
                VisibleCreature(
                    name=creature["name"],
                    position=creature["position"],
                    image=species["states"][creature["current_state"]]["image"],
                    height=species["states"][creature["current_state"]]["height"],
                    width=species["states"][creature["current_state"]]["width"],
                )
            )

    return visible_creatures


def updateCreature(creature: Creature) -> None:
    creature_path = (getWorldPath() / "creatures" / creature["id"]).with_suffix(".yaml")
    creature_path.write_text(yaml.dump(creature))
