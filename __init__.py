#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example node communicating between ComfyUI Javascript and Python.
"""

import time
from typing import Any
from aiohttp import web #, ClientSession
from server import PromptServer

EVENT_COZY_UPDATE = "cozy-event-combo-update"

# ==============================================================================
# === SUPPORT ===
# ==============================================================================

class TimedOutException(Exception): pass

class ComfyAPIMessage:
    """
    This is to collect messages from JS for nodes that are parsing/looking
    for messages.
    """
    MESSAGE = {}

    @classmethod
    def poll(cls, ident, period=0.01, timeout=3) -> Any:
        _t = time.monotonic()
        if isinstance(ident, (set, list, tuple, )):
            ident = ident[0]

        sid = str(ident)
        while not (sid in cls.MESSAGE) and time.monotonic() - _t < timeout:
            time.sleep(period)

        if not (sid in cls.MESSAGE):
            raise TimedOutException
        dat = cls.MESSAGE.pop(sid)
        return dat

# Generic function to send messages to Javascript
def comfy_message(route:str, ident:str, data:dict) -> None:
    data['id'] = ident
    PromptServer.instance.send_sync(route, data)

@PromptServer.instance.routes.get("/cozy_spoke")
async def route_cozy_spoke(request) -> Any:
    """A simple lookup for the data provided.
    The function names need to be unique for each 'route'.
    Returns all messages stored in the Message Bus `ComfyAPIMessage.MESSAGE`."""
    return web.json_response(ComfyAPIMessage.MESSAGE)

@PromptServer.instance.routes.post("/cozy_spoke")
async def route_cozy_spoke_combo(request) -> Any:
    """A catch all route to pass messages for specific node messages needed
    during node execution. The node itself will search the message bucket
    `ComfyAPIMessage.MESSAGE` and can process during its run function call."""
    json_data = await request.json()
    if (did := json_data.get("id")) is not None:
        # stores the data-call for the instanced node (by id) to check on execute
        ComfyAPIMessage.MESSAGE[str(did)] = json_data
        return web.json_response(json_data)
    return web.json_response({})

@PromptServer.instance.routes.post("/cozy_spoke/node")
async def route_cozy_spoke(request) -> Any:
    """A specific route for a specific node to process outside of an execution run.
    Here we manipulate the values output based on the selection in ComboA
    """
    json_data = await request.json()
    result = {}
    if (data := json_data.get("data")) is not None:
        match data.lower():
            case 'option1':
                result = {'data': ["Option1 - Sub-option 1", "Option1 - Sub-option 2"]}
            case 'option2':
                result = {'data': ["Option2 - Sub-option 1", "Option2 - Sub-option 2"]}
            case 'option3':
                result = {'data': ["Option3 - Sub-option 1", "Option3 - Sub-option 2"]}

    return web.json_response(result)

# ==============================================================================
# === NODE ===
# ==============================================================================

class CozySpokeNode:
    CATEGORY = "comfy-ext"
    RETURN_TYPES = ()
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls) -> None:
        return {
            "required": {},
            "optional": {
                "DropDownA": (["Option1", "Option2", "Option3"], {"default": ""}),
                "DropDownB": (["Other1", "Other2"], {"default": ""}),
            },
            "hidden": {
                "ident": "UNIQUE_ID"
            }
        }

    def run(self, ident, DropDownA="", DropDownB="") -> None:
        comfy_message(EVENT_COZY_UPDATE, ident, {
            "id": ident,
            "a": DropDownA,
            "b": DropDownB
        })
        return ()

# ==============================================================================
# === MAPPING ===
# ==============================================================================

NODE_CLASS_MAPPINGS = {
    "CozySpoke": CozySpokeNode,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CozySpoke": "Realtime Python <-> Javascript Example Node"
}
WEB_DIRECTORY = "./web"
