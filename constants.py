from enum import Enum

# NON-CONSTANTS
global_verbose = False

# CONSTANTS
#                 0   1   2   3      4     5    6     7    8     9   10    11    12
DICE_SUM_PROBS = [0, 0, 1 / 36, 1 / 18, 1 / 12, 1 / 9, 5 / 36, 1 / 6, 5 / 36, 1 / 9, 1 / 12, 1 / 18, 1 / 36]
HAND_OFFSET = 25  # Offset in array storing info for players' hands
BOARD_STATES_DIR = './boards/'  # Directory for .json board states
GAME_STATES_DIR = './games/'  # Directory for saved .json game states
STAT_HEADER_STR = "player str, pidx, num wins, win %, avg vps, avg opp vps on plyr win\n"  # Saved game statistics
WINNING_VPS = 10  # Number of victory points needed to win
MAX_ROADS = 15  # Number of roads each player starts with
MAX_SETTLEMENTS = 5  # Number of settlements each player starts with
MAX_CITIES = 4  # Number of cities each player starts with

# Road map, 1 bit for road locations
RMAP = [
    0,
    0b00000000000000010101010101000000,
    0b00000000000000100010001000100000,
    0b00000000000001010101010101010000,
    0b00000000000010001000100010001000,
    0b00000000000101010101010101010100,
    0b00000000001000100010001000100010,
    0b00000000000101010101010101010100,
    0b00000000000010001000100010001000,
    0b00000000000001010101010101010000,
    0b00000000000000100010001000100000,
    0b00000000000000010101010101000000,
    0]

# Building map, 1 means vertex
# NOTE: water buffer is insufficient vertically; would need 2 rows to fix
# TODO: fix water buffer (make sufficiently large, or just remove altogether)
BMAP = [
    0,
    0b00000000000000101010101010100000,
    0,
    0b00000000000010101010101010101000,
    0,
    0b000000000010_1010_1010_1010_1010_1010,
    0,
    0b00000000001010101010101010101010,
    0,
    0b00000000000010101010101010101000,
    0,
    0b00000000000000101010101010100000,
    0,
]


class Act(Enum):
    RESET = -1
    END_TURN = 0
    ROAD = 1
    SETTLEMENT = 2
    CITY = 3
    DEV_CARD = 4
    PLAY_DEV = 5
    BANK_TRADE = 6
    PLACE_ROBBER = 7
    DICE_ROLL = 8  # Only used for certain player agents; not a valid action to take in-game
    # PLAYER_TRADE = 8


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

    PLAYED_KNIGHTS = 15  # Total knights played in game thus far
    # Other played devs tracked for stats
    PLAYED_RD = 16
    PLAYED_MONO = 17
    PLAYED_YOP = 18

    PORTS = 19  # 8-bit map of ports
    TRUE_VP = 20  # player's current victory points
    LEN_LNGST_ROAD = 21  # player's current longest road length

    RDS_BUILT = 22  # Total roads built in game thus far
    SMENTS_BUILT = 23  # Total settlements built in game thus far
    CITIES_BUILT = 24  # Total cities built in game thus far


HEX_LETTER_TO_RES_ID = {
    "B": HIdx.B.value,
    "G": HIdx.G.value,
    "L": HIdx.L.value,
    "O": HIdx.O.value,
    "W": HIdx.W.value,
    "D": -1,
}

# List of tuples: list index is the 0-18 hex idx, tuple is a list of adjacent vertices (r,c)
HEX_IDX_TO_VERTICES = [((9, 9), (9, 7), (9, 5), (11, 5), (11, 7), (11, 9)),
                       ((9, 13), (9, 11), (9, 9), (11, 9), (11, 11), (11, 13)),
                       ((9, 17), (9, 15), (9, 13), (11, 13), (11, 15), (11, 17)),
                       ((7, 7), (7, 5), (7, 3), (9, 3), (9, 5), (9, 7)),
                       ((7, 11), (7, 9), (7, 7), (9, 7), (9, 9), (9, 11)),
                       ((7, 15), (7, 13), (7, 11), (9, 11), (9, 13), (9, 15)),
                       ((7, 19), (7, 17), (7, 15), (9, 15), (9, 17), (9, 19)),
                       ((5, 5), (5, 3), (5, 1), (7, 1), (7, 3), (7, 5)),
                       ((5, 9), (5, 7), (5, 5), (7, 5), (7, 7), (7, 9)),
                       ((5, 13), (5, 11), (5, 9), (7, 9), (7, 11), (7, 13)),
                       ((5, 17), (5, 15), (5, 13), (7, 13), (7, 15), (7, 17)),
                       ((5, 21), (5, 19), (5, 17), (7, 17), (7, 19), (7, 21)),
                       ((3, 7), (3, 5), (3, 3), (5, 3), (5, 5), (5, 7)),
                       ((3, 11), (3, 9), (3, 7), (5, 7), (5, 9), (5, 11)),
                       ((3, 15), (3, 13), (3, 11), (5, 11), (5, 13), (5, 15)),
                       ((3, 19), (3, 17), (3, 15), (5, 15), (5, 17), (5, 19)),
                       ((1, 9), (1, 7), (1, 5), (3, 5), (3, 7), (3, 9)),
                       ((1, 13), (1, 11), (1, 9), (3, 9), (3, 11), (3, 13)),
                       ((1, 17), (1, 15), (1, 13), (3, 13), (3, 15), (3, 17))]
# CODE USED TO GENERATE ABOVE HEX_IDX_TO_VERTICES LIST
# HEX_IDX_TO_ROW_COL = [
#     [10, 7],
#     [10, 11],
#     [10, 15],
#     [8, 5],
#     [8, 9],
#     [8, 13],
#     [8, 17],
#     [6, 3],
#     [6, 7],
#     [6, 11],
#     [6, 15],
#     [6, 19],
#     [4, 5],
#     [4, 9],
#     [4, 13],
#     [4, 17],
#     [2, 7],
#     [2, 11],
#     [2, 15],
# ]
# def hex_rc_to_vertex_rc(hex_rc, vertex_idx):
#     if vertex_idx == 0:
#         return [hex_rc[0]-1, hex_rc[1]+2]
#     elif vertex_idx == 1:
#         return [hex_rc[0]-1, hex_rc[1]]
#     elif vertex_idx == 2:
#         return [hex_rc[0]-1, hex_rc[1]-2]
#     elif vertex_idx == 3:
#         return [hex_rc[0]+1, hex_rc[1]-2]
#     elif vertex_idx == 4:
#         return [hex_rc[0]+1, hex_rc[1]]
#     elif vertex_idx == 5:
#         return [hex_rc[0]+1, hex_rc[1]+2]
#
# for hex_idx, hex_rc in enumerate(HEX_IDX_TO_ROW_COL):
#     vertices = []
#     for vertex_idx in range(6):
#         vertices.append(hex_rc_to_vertex_rc(hex_rc, vertex_idx))
#     HEX_IDX_TO_VERTICES.append(vertices)
