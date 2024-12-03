from flask import request
from flask_socketio import disconnect, emit

from .app import app, socketio
from .helper_functions import *


@socketio.on("connect", namespace="/dm")
def dm_connect():
    auth = request.headers.get("Authorization")
    password = auth.split(" ")[1] if auth else None
    if password != app.config["DM_PASSWORD"]:
        disconnect()
    else:
        emit("connected", namespace="/dm")


@socketio.on("connect", namespace="/display")
def display_connect():
    emit("connected", namespace="/display")


@socketio.on("change_world", namespace="/dm")
def change_world(world_id: str):
    app.config["WORLD"] = world_id
    world = loadWorld()
    region_id = world["current_region"]
    emit("change_world", world, broadcast=True)
    emit("change_region", loadVisibleRegion(region_id), namespace="/display")
    emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display")


@socketio.on("change_region", namespace="/dm")
def change_region(region_id: str):
    world = loadWorld()
    world["current_region"] = region_id
    updateWorld(world)
    emit("change_region", loadVisibleRegion(region_id), namespace="/display")
    emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display")


@socketio.on("update_region", namespace="/dm")
def update_region(region: Region):
    updateRegion(region)
    region_id = region["id"]
    world = loadWorld()
    if world["current_region"] == region_id:
        emit("update_region", loadVisibleRegion(region_id), namespace="/display")


@socketio.on("update_creature", namespace="/dm")
def update_creature(creature: Creature):
    updateCreature(creature)
    region_id = creature["current_region"]
    world = loadWorld()
    if world["current_region"] == region_id:
        emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display")


@app.get("/images/<path:path>")
def send_image(path):
    return app.send_static_file(pathlib.Path(app.config["WORLD"]) / "images" / path)
