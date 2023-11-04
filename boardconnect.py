import asyncio
import websockets
import json
import random

pong = {
    "type": 'pong',
    'message': 'pong',
}
board_state = {
    "type": "board_update",
    "message": "update",
}

async def chat(websocket, path):
    while(True):
        msg = await websocket.recv()
        try:
            msg_obj = json.loads(msg)
            # Should always have 'type' field
            #if msg_obj["type"] == "ping":
            #    print(f"From Client: {msg}")
            #    smsg = json.dumps(pong)
            #else:
            board_state["dv1"] = str(random.randint(1,6))
            board_state["dv2"] = str(random.randint(1,6))
            board_state["robber_loc"] = str(random.randint(0,18))
            smsg = json.dumps(board_state)
        except Exception as e:
            smsg = json.dumps({"type":"error"})
            print(e)
        await websocket.send(smsg)

start_server = websockets.serve(chat, 'localhost', 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
