import asyncio
import websockets
import json
import random
from util import generate_new_board
#  For debugging:
import sys, os

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
            if msg_obj["type"] == "ping":
                smsg = json.dumps(pong)
            elif msg_obj["type"] == "new_board_request":
                brd = generate_new_board()
                brd["type"] = "new_board"
                smsg = json.dumps(brd)
            else:
                board_state["type"] = "board_update"
                board_state["dv1"] = str(random.randint(1,6))
                board_state["dv2"] = str(random.randint(1,6))
                board_state["robber_loc"] = str(random.randint(0,18))
                smsg = json.dumps(board_state)
        except Exception as e:
            smsg = json.dumps({"type":"error"})
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            # print(e)
        await websocket.send(smsg)

if __name__ == "__main__":
    start_server = websockets.serve(chat, 'localhost', 8080)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
