from enum import Enum
import random
from constants import HAND_OFFSET


class Act(Enum):
    END_TURN = 0
    ROAD = 1
    SETTLEMENT = 2
    CITY = 3
    DEV_CARD = 4
    PLAY_DEV = 5
    BANK_TRADE = 6
    # PLAYER_TRADE = 7


class HIdx(Enum):
    B = 0  # Brick resource cards
    G = 1  # Grain resource cards
    L = 2  # Lumber resource cards
    O = 3  # Ore resource cards
    W = 4  # Wool resource cards

    KNIGHT = 5  # Knight dev cards
    VP_CRD = 6  # Victory Point dev cards
    RD_BLDR = 7  # Road builder dev cards 
    MONO = 8  # Monopoly dev cards
    YOP = 9  # Year of Plenty dev cards
    
    LRGST_ARMY = 10  # 1/0: has/doesn't have Largest Army
    LNGST_ROAD = 11  # 1/0: has/doesn't have Longest Road
    # 8-bit map of playable dev card types (previously bought) (1<<devcard_id)
    # 0 -> can't play dev card type, 1 -> at least on playable dc
    PLAYABLE_DEV_MAP = 12 
    PLAYED_DEV = 13
    COLOR_IDX = 14  # or player id
    
    KNIGHTS_PLYD = 15  # Total knights played in game thus far
    # Other played devs tracked for stats
    PLAYED_RD = 16
    PLAYED_MONO = 17
    PLAYED_YOP = 18
    
    PORTS = 19  # 8-bit map of ports
    TRUE_VP = 20  # player's current victory points


def roll_dice() -> tuple:
    dv1 = random.randint(1, 6)
    dv2 = random.randint(1, 6)
    # Distribute resources:

    return (dv1, dv2)

# def find_moves(gb: dict, turn: int) -> tuple:
#     """
#     For current player, find all possible moves
#     gb: Read "GameBoard"; current game state
#     turn: int [0, <num players>)
#     """
#     """
#     [END_TURN, CITY, DEV_CARD] -> given they chose city, choose where to build
#     [END_TURN, CITY0, CITY1, CITY2, CITY3, DEV_CARD] -> already chose where to build when deciding
#     """
#     # TODO: to what extent should flexible recipes be supported?
#     # TODO: check for possible building positions
#     gen_moves = [Act.END_TURN]
#     e_moves = [(Act.END_TURN, ), ]  # exact moves: each move is a tuple, with the first item being the general move type id
#     offset = HAND_OFFSET * turn
#     if gb["hands"][offset + HIdx.BRK.value] >= 1 and gb["hands"][offset + HIdx.LMBR.value] >= 1:
#         gen_moves.append(Act.ROAD)
#         if gb["hands"][offset + HIdx.GRN.value] >= 1 and gb["hands"][offset + HIdx.WOOL.value] >= 1:
#             gen_moves.append(Act.SETTLEMENT)
#     if gb["hands"][offset + HIdx.ORE.value] >= 3 and gb["hands"][offset + HIdx.GRN.value] >= 2:
#         gen_moves.append(Act.CITY)
#     if gb["hands"][offset + HIdx.ORE.value] >= 1 and gb["hands"][offset + HIdx.GRN.value] >= 1 and gb["hands"][offset+HIdx.WOOL.value] >= 1:
#         gen_moves.append(Act.DEV_CARD)
#
#     # TODO: below logic is based on false premise that only one dev card can be bought per turn; fix this
#     # Check for playable dev cards
#     playable_devs = []
#     if gb["hands"][offset + HIdx.PLAYED_DEV.value] == 0:
#         # Check for dev cards not bought on this turn
#         for i in range(HIdx.KNIGHT.value, HIdx.KNIGHT.value+5):
#             if gb["hands"][offset + i] > 0:
#                 # if we didn't just buy the dev card, or if there is more than one of this dev card
#                 if gb["hands"][offset + HIdx..value] != i or gb["hands"][offset + i] > 1:
#                     playable_devs.append(i)
#                 playable_devs.append(i)
#         #     gen_moves.append(Act.PLAY_DEV)
#         if playable_devs:
#             gen_moves.append(Act.PLAY_DEV)
#
#     # Check ports and cards to determine bank trades:
#     # port types: 0: brick, 1: grain, 2: lumber, 3: ore, 4: wool, 5: 3:1, 6: 4:1
#     gen_trade_type = 5 if (gb["hands"][offset + HIdx.PORTS.value] & (1<<5)) else 6  # See if player has 3:1 port
#     trade_types = []
#     gen_trade_possible = False
#     # TODO: if a player has a 3:1, are they allowed to choose a 4:1 bank trade?; currently not allowed
#     # TODO: compute possible all trade types here, or in separate function?
#     # Check all 2:1 ports
#     for i in range(5):
#         if gb["hands"][offset + HIdx.PORTS.value] & (1 << i):  # Check for player's access to port
#             if gb["hands"][offset + i] >= 2:
#                 trade_types.append(i)
#         if gb["hands"][offset + i] >= (3 if gen_trade_type == 5 else 4):
#             gen_trade_possible = True
#     if gen_trade_possible:
#         trade_types.append(gen_trade_type)
#         # TODO: make use of trade_types list
#     if trade_types:
#         gen_moves.append(Act.BANK_TRADE)
#
#     return tuple(gen_moves)


"""
Board state object, example format:
"""
"""
general board state: [
       0, 
        0b00000000000000111111111111100000,
        0b00000000000000100010001000100000, 
        0b00000000000011111111111111111000,
        0b00000000000010001000100010001000, 
        0b00000000001111111111111111111100, 
        0b00000000001000100010001000100010,
        0b00000000001111111111111111111100, 
        0b00000000000010001000100010001000, 
        0b00000000000011111111111111111000,
        0b00000000000000100010001000100000, 
        0b00000000000000111111111111100000, 
        0],
"""

def gen_vertices_map(brd_s_o: dict) -> dict:
    """
    Generate vertices map from board state object
    brd_s_o: board state object
    r and c are row and column indices, respectively
    row values increase from top to bottom
    column values increase from right to left (i.e. (0,0) is top right corner)
    """
    vertices = {}
    # TODO: implement this
    for r in range(13):
        for c in range(24):
            # Check if (r,c) is a vertex
            if brd_s_o["bmap"][r] & (1<<c):
                i = r*24 + c
                vertices[(i, 0)] = (brd_s_o["bmap"][i], brd_s_o["bmap"][i+1], brd_s_o["bmap"][i+2])
            if brd_s_o["bmap"][r] & (1<<c):
                i = r*24 + c

        vertices[(i, 0)] = (brd_s_o["bmap"][i], brd_s_o["bmap"][i+1], brd_s_o["bmap"][i+2])
    return vertices

# Vertex resources are stored in the format: (hex_1_type, hex_1_dice_val, hex_2_type, hex_2_dice_val, hex_3_type, hex_3_dice_val, port_type)
# hex_type is a number from 0-6, where 0 is desert, 1 is brick, 2 is grain, 3 is lumber, 4 is ore, 5 is wool, 6 is water (treated like desert)
# port_type is an integer (uint_8); bool bit at: (1<<resource_idx) (3:1 at 1<<6)
# brd_s_o = {
#     "vertices": {
#         (0, 0): (0,0,0,0,0,0,0),
#     },
#     # Board state representation (currently static, filled with arbitrary board)
#     # 0123456789..18
#     "hex_state": "WGBWGOLOLDLGBWBGLWO",
#     # hex codes for different chance values, 0 means no token (desert)
#     "tkn_state": "B655438830B9A46C92A",
#     # orientation values for ports at each hex idx, 6 means no port
#     "port_orients": "6343665266661665610",
#     # port types for port at each hex idx, 6: no port
#     "port_type_state": "6554660566663662615",
#     # map dice sums (dicesum-2 = idx) to vertex beneficiaries
#     "diceMap": [(), (), (), (), (), None, (), (), (), (), ()],
#     "robber_loc": 9,
#     "dv1": 3,
#     "dv2": 6,
#     "bank": [20,20,20,20,20,  # Brick grain lumber ore wool
#              14,5,2,2,2,
#              0,0,  # Largest army in bank, longest road in bank
#              ],  # Knights vp ...
#     "hands": [0,0,0,0,0,  # curr resources
#            5,0,0,0,0,  # curr dev cards
#            0,0,  # has largest army, has longest road (bool: 1 or 0)
#            0,  # playable dev card types bmap (previously bought) (1<<devcard_id)
#            0,  # played dev card this turn (bool: 1 or 0)
#            0,  # color idx
#            0,  # num played knights
#            0,0,0,  # other played dev cards (tracking all for stats)
#            0,  # ports; uint_8; bool bit at: (1<<resource_idx) (3:1 at 1<<6)
#            0,  # current true victory points
#
#            # Player 2 hand
#            2,6,0,2,0,
#            0,1,0,1,0,
#            0,0,0,0,0,
#            0,0,0,0,0,
#            5,
#
#            # Player 3 hand
#            3,1,0,2,0,
#            1,1,0,0,0,
#            0,1,0,0,0,
#            0,0,0,0,0,
#            7,
#            # Player 4 hand
#            0,2,7,0,0,
#            0,0,0,1,1,
#            1,0,0,0,0,
#            3,0,0,0,0,
#            8,
#            ],
#
#     "btypemap": [
#         0,
#         0b00000000000000000010000000000000,
#         0,
#         0b00000000000000000000000000000000,
#         0,
#         0b00000000000000000000000000100000,
#         0,
#         0b00000000000000000000000000000000,
#         0,
#         0b00000000000000000000000000001000,
#         0,
#         0b00000000000000000000000000000000,
#         0,
#     ],
#     "rbmap0": [
#        0,
#         0b00000000000000110111011000000000,
#         0b00000000000000100000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000100000000000000000,
#         0b00000000000000110000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0,
#     ],
#     "rbmap1": [
#        0,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000111011000,
#         0b00000000000000000000000010001000,
#         0b00000000000000000000000001110000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0,
#     ],
#     "rbmap2": [
#        0,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000001101110111000000000000,
#         0b00000000001000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000001011000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0,
#     ],
#     "rbmap3": [
#        0,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0b00000000001100000000000011010110,
#         0b00000000000010000000000000001000,
#         0b00000000000010000000000000001000,
#         0b00000000000000000000000000000000,
#         0b00000000000000000000000000000000,
#         0,
#     ],
# }
