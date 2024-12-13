import pathlib

import yaml
from shapely import LineString
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


def loadWorlds() -> list[World]:
    worlds: list[World] = []
    for world_folder in pathlib.Path(WORLDS_FOLDER).glob("*"):
        world_file = world_folder / "world.yaml"
        if not (world_file.exists() and world_file.is_file()):
            continue
        world_data = yaml.safe_load(world_file.read_text())
        worlds.append(World(**world_data))
    return worlds


def loadWorld() -> World:
    world_data = yaml.safe_load((getWorldPath() / "world.yaml").read_text())
    return World(**world_data)


def loadVisibleWorld() -> VisibleWorld:
    world = loadWorld()
    return VisibleWorld(name=world["name"])


def updateWorld(data: World) -> None:
    (getWorldPath() / "world.yaml").write_text(yaml.dump(data))


def loadAllRegions() -> list[Region]:
    regions_path = getWorldPath() / "regions"
    if not regions_path.exists() and regions_path.is_dir():
        raise FileNotFoundError(f"Regions folder not found: {regions_path}")
    regions = []
    for region_file in regions_path.glob("*.yaml"):
        region_data = yaml.safe_load(region_file.read_text())
        regions.append(Region(**region_data))

    return regions


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
        fog_of_war = Polygon()
    else:
        top_left = img_data["top_left_corner"]
        width = img_data["width"]
        height = img_data["height"]
        fog_of_war = Polygon(
            [
                tuple(top_left),
                (top_left[0] + width, top_left[1]),
                (top_left[0] + width, top_left[1] + height),
                (top_left[0], top_left[1] + height),
            ]
        )

    for subregion in region["subregions"]:
        region_polygon = Polygon(subregion["polygon"])
        if subregion["visible"]:
            fog_of_war = fog_of_war.difference(region_polygon)
        else:
            fog_of_war = fog_of_war.union(region_polygon)

    for hole in fog_of_war.interiors:
        # Add a small incision from the centroid of the hole to the exterior
        centroid = hole.centroid
        incision = LineString([centroid, (centroid.coords[0][0], 9999999999)]).buffer(0.0001)
        fog_of_war = fog_of_war.difference(incision)

    fog_of_war = fog_of_war.exterior.coords[:-1]

    return VisibleRegion(name=region["name"], grid=region["grid"], image=img_data, fog_of_war=[fog_of_war])


def updateRegion(region: Region) -> None:
    region_path = (getWorldPath() / "regions" / region["id"]).with_suffix(".yaml")
    region_path.write_text(yaml.dump(region))


def loadCreatures(region: str) -> list[Creature]:
    creatures_path = getWorldPath() / "creatures"
    if not creatures_path.exists():
        raise FileNotFoundError(f"Creatures folder not found: {creatures_path}")
    creatures = []
    for creature_file in creatures_path.glob("*.yaml"):
        creature_data = Creature(**yaml.safe_load(creature_file.read_text()))
        if creature_data["current_region"] == region:
            creatures.append(creature_data)

    return creatures


def loadAllCreatures() -> list[Creature]:
    creatures_path = getWorldPath() / "creatures"
    if not creatures_path.exists():
        raise FileNotFoundError(f"Creatures folder not found: {creatures_path}")
    creatures = []
    for creature_file in creatures_path.glob("*.yaml"):
        creature_data = Creature(**yaml.safe_load(creature_file.read_text()))
        creatures.append(creature_data)

    return creatures


def loadSpecies(species: str) -> Species:
    species_path = (getWorldPath() / "species" / species).with_suffix(".yaml")
    if not species_path.exists():
        raise FileNotFoundError(f"Species folder not found: {species_path}")
    species_data = yaml.safe_load(species_path.read_text())
    return Species(**species_data)


def loadAllSpecies() -> list[Species]:
    species_path = getWorldPath() / "species"
    if not species_path.exists():
        raise FileNotFoundError(f"Species folder not found: {species_path}")
    species = []
    for species_file in species_path.glob("*.yaml"):
        species_data = Species(**yaml.safe_load(species_file.read_text()))
        species.append(species_data)

    return species


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
