from flask import request
from flask_socketio import disconnect, emit

from .app import app, socketio
from .helper_functions import *


@socketio.on("connect", namespace="/dm")
def dm_connect():
    password = request.headers.get("Authorization")
    if password != app.config["DM_PASSWORD"]:
        disconnect()
    else:
        emit("connected", {"message": "Admin Connected"}, to=request.sid)


@socketio.on("connect", namespace="/display")
def display_connect():
    emit("connected", {"message": "Display Connected"}, to=request.sid)
    if app.config["WORLD"] is not None:
        world = loadWorld()
        region_id = world["current_region"]
        emit("change_world", world, to=request.sid)
        emit("change_region", loadVisibleRegion(region_id), to=request.sid)
        emit("update_creatures", loadVisibleCreatures(region_id), to=request.sid)


@socketio.on("disconnect", namespace="/dm")
def dm_disconnect():
    pass


@socketio.on("disconnect", namespace="/display")
def display_disconnect():
    pass


@socketio.on("change_world", namespace="/dm")
def change_world(world_id: str):
    if not request.headers.get("Authorization") == app.config["DM_PASSWORD"]:
        disconnect()
    app.config["WORLD"] = world_id
    world = loadWorld()
    region_id = world["current_region"]
    emit("change_world", world, broadcast=True)
    emit("change_region", loadVisibleRegion(region_id), namespace="/display", broadcast=True)
    emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display", broadcast=True)


@socketio.on("change_region", namespace="/dm")
def change_region(region_id: str):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    if not request.headers.get("Authorization") == app.config["DM_PASSWORD"]:
        disconnect()
    world = loadWorld()
    world["current_region"] = region_id
    updateWorld(world)
    emit("change_region", loadVisibleRegion(region_id), namespace="/display", broadcast=True)
    emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display", broadcast=True)


@socketio.on("update_region", namespace="/dm")
def update_region(region: Region):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    if not request.headers.get("Authorization") == app.config["DM_PASSWORD"]:
        disconnect()
    updateRegion(region)
    region_id = region["id"]
    world = loadWorld()
    if world["current_region"] == region_id:
        emit("update_region", loadVisibleRegion(region_id), namespace="/display", broadcast=True)


@socketio.on("update_creature", namespace="/dm")
def update_creature(creature: Creature):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    if not request.headers.get("Authorization") == app.config["DM_PASSWORD"]:
        disconnect()
    updateCreature(creature)
    region_id = creature["current_region"]
    world = loadWorld()
    if world["current_region"] == region_id:
        emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display", broadcast=True)


@app.get("/images/<path:path>")
def send_image(path):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    return app.send_static_file(pathlib.Path(app.config["WORLD"]) / "images" / path)
