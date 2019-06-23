#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets
import random

conversation = ["I don't understand", "Hi", "How are you", "What's that", "Ha Ha Ha", "Sleepy", "Yee-haa cowboy"]

logging.basicConfig()

STATE = {'value': "waiting..."}
USERS = set()

def state_event():
    return json.dumps({'type': 'reply', **STATE})
def users_event():
    return json.dumps({'type': 'users', 'count': len(USERS)})

async def notify_state():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_msg():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = message_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS.add(websocket)
    await notify_users()

async def unregister(websocket):
    USERS.remove(websocket)
    await notify_users()

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            if data['action'] == 'submit':
                index = random.randint(0,len(conversation) - 1)
                reply = conversation[index]
                if index == 0 or index == 2:
                    reply = " '" +  data['message'] +  "' ??? " + reply
                STATE['value'] = reply
                await notify_state()
            elif data['action'] == 'plus':
                STATE['value'] += 1
                await notify_state()
            else:
                logging.error(
                    "unsupported event: {}", data)
    finally:
        await unregister(websocket)

asyncio.get_event_loop().run_until_complete(
    websockets.serve(counter, 'localhost', 6789))
asyncio.get_event_loop().run_forever()
