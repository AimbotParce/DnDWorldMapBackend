import os

import flask
from flask import request
from flask_socketio import disconnect, emit

from .app import app, socketio
from .helper_functions import *

connected_displays = 0


@socketio.on("connect", namespace="/dm")
def dm_connect():
    password = request.headers.get("Authorization")
    if password != app.config["DM_PASSWORD"]:
        print(f"Admin attempted to connect with incorrect password", flush=True)
        disconnect()
    else:
        print("Admin connected", flush=True)
        emit("connected", {"message": "Admin Connected"}, to=request.sid)
        emit("update_display_counter", connected_displays, to=request.sid)
        emit("update_worlds", loadWorlds(), to=request.sid)
        if app.config["WORLD"] is not None:
            emit("change_world", loadVisibleWorld(), to=request.sid)
            emit("update_regions", loadAllRegions(), to=request.sid)
            emit("update_creatures", loadAllCreatures(), to=request.sid)


@socketio.on("connect", namespace="/display")
def display_connect():
    global connected_displays
    connected_displays += 1
    print(f"Display connected, total: {connected_displays}", flush=True)
    emit("update_display_counter", connected_displays, namespace="/dm", broadcast=True)
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
    global connected_displays
    connected_displays -= 1
    emit("update_display_counter", connected_displays, namespace="/dm", broadcast=True)


@socketio.on("change_world", namespace="/dm")
def change_world(world_id: str):
    if not request.headers.get("Authorization") == app.config["DM_PASSWORD"]:
        disconnect()
    if os.sep in world_id or "/" in world_id:
        return "Invalid world id", 400
    app.config["WORLD"] = world_id
    world = loadWorld()
    region_id = world["current_region"]
    emit("change_world", world, namespace="/dm", broadcast=True)
    emit("change_world", loadVisibleWorld(), namespace="/display", broadcast=True)
    emit("change_region", loadVisibleRegion(region_id), namespace="/display", broadcast=True)
    emit("update_creatures", loadVisibleCreatures(region_id), namespace="/display", broadcast=True)


@socketio.on("change_region", namespace="/dm")
def change_region(region_id: str):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    if os.sep in region_id or "/" in region_id:
        return "Invalid region id", 400
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
def send_image(path: str):
    if app.config["WORLD"] is None:
        return "No world selected", 400
    imgs_path = getWorldPath() / "images"
    full_path = (imgs_path / path).resolve()

    if not imgs_path in full_path.parents:
        return "Invalid path", 400
    return flask.send_file(full_path)
