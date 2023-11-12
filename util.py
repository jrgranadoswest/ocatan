import random
import json
from GameBoard import Act, HIdx
from constants import HAND_OFFSET, BOARD_STATES_DIR, BMAP, RMAP


# New board state generation methods
def generate_new_board():
    """
    Generates a new board state (complete) for a game of Catan.
    """
    new_brd = {
        # "vertices": {
        #     (0, 0): (0, 0, 0, 0, 0, 0, 0),
        # },
        # Board state representation (currently static, filled with arbitrary board)
        # 0123456789..18
        "hex_state": gen_tile_arrangement(),
        "dv1": str(random.randint(1, 6)),
        "dv2": str(random.randint(1, 6)),
        # orientation values for ports at each hex idx, 6 means no port
        "port_orients": "6343665266661665610",
        # map dice sums (dicesum-2 = idx) to vertex beneficiaries
        "diceMap": [(), (), (), (), (), None, (), (), (), (), ()],
        "bank": [20, 20, 20, 20, 20,  # Brick grain lumber ore wool
                 14, 5, 2, 2, 2,
                 1, 1,  # Largest army in bank, longest road in bank
                 ],  # Knights vp ...
        "hands": [0, 0, 0, 0, 0,  # curr resources
                  0, 0, 0, 0, 0,  # curr dev cards
                  0, 0,  # has largest army, has longest road (bool: 1 or 0)
                  0,  # playable dev card types bmap (previously bought) (1<<devcard_id)
                  0,  # played dev card this turn (bool: 1 or 0)
                  0,  # color idx
                  0,  # num played knights
                  0, 0, 0,  # other played dev cards (tracking all for stats)
                  0,  # ports; uint_8; bool bit at: (1<<resource_idx) (3:1 at 1<<6)
                  2,  # current true victory points

                  # Player 2 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  2,

                  # Player 3 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  2,
                  # Player 4 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  2,
                  ],

        "btypemap": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap0": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap1": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap2": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap3": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # TODO: should the 'anded together' map be stored in the board state?
        "built_map": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # all player developments anded together
        # "btypemap": [
        #     0,
        #     0b00000000000000000010000000000000,
        #     0,
        #     0b00000000000000000000000000000000,
        #     0,
        #     0b00000000000000000000000000100000,
        #     0,
        #     0b00000000000000000000000000000000,
        #     0,
        #     0b00000000000000000000000000001000,
        #     0,
        #     0b00000000000000000000000000000000,
        #     0,
        # ],
        # "rbmap0": [
        #     0,
        #     0b00000000000000110111011000000000,
        #     0b00000000000000100000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000100000000000000000,
        #     0b00000000000000110000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0,
        # ],
        # "rbmap1": [
        #     0,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000111011000,
        #     0b00000000000000000000000010001000,
        #     0b00000000000000000000000001110000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0,
        # ],
        # "rbmap2": [
        #     0,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000001101110111000000000000,
        #     0b00000000001000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000001011000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0,
        # ],
        # "rbmap3": [
        #     0,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0b00000000001100000000000011010110,
        #     0b00000000000010000000000000001000,
        #     0b00000000000010000000000000001000,
        #     0b00000000000000000000000000000000,
        #     0b00000000000000000000000000000000,
        #     0,
        # ],
    }
    # TODO: assumes at least one desert in board arrangement; implement flexibility for no desert
    new_brd["robber_loc"] = new_brd["hex_state"].index("D")
    # port types for port at each hex idx, 6: no port
    new_brd["port_type_state"] = gen_port_types(new_brd["port_orients"])
    # hex codes for different chance values, 0 means no token (desert)
    new_brd["tkn_state"] = gen_token_arrangement(new_brd["hex_state"])
    place_init_settlements(new_brd)
    return new_brd


def gen_token_arrangement(hex_arrangement: str) -> str:
    """
    Generates a string of characters representing the dice value token arrangement for a game of Catan.
    e.g. "B655438830B9A46C92A",
    """
    # NOTE: currently assumes 19 tiles, exactly one desert
    chars = list("B65543883B9A46C92A")
    random.shuffle(chars)
    # insert 0 at desert location
    chars.insert(hex_arrangement.index('D'), '0')
    return "".join(chars)


# Static lookup table for port locations; each entry is a tuple of (hex_idx, port_orientation)
# PORT_LOOKUP = [(0, 2), (0, 3), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4), (6, 4), (6, 5), (11, 4), (11, 5), (11, 0),
#                (15, 5), (15, 0), (18, 5), (18, 0), (18, 1), (17, 0), (17, 1), (16, 0), (16, 1), (16, 2), (12, 1),
#                (12, 2), (7, 1), (7, 2), (7, 3), (3, 2), (3, 3)]

def gen_port_types(port_orients="6343665266661665610") -> str:
    """
    Generates a list of port types for a game of Catan.
    """
    assert len(port_orients) == 19
    port_types = ['0', '1', '2', '3', '4', '5', '5', '5', '5']
    random.shuffle(port_types)
    port_type_idx = 0
    port_types_result = []
    for idx, orient in enumerate(port_orients):
        if orient != '6':
            port_types_result.append(port_types[port_type_idx])
            port_type_idx += 1
        else:
            port_types_result.append('6')
    return "".join(port_types_result)


def gen_tile_arrangement(tile_assortment=(3, 4, 4, 3, 4, 1), num_tiles=19) -> str:
    """
    Generates a string of characters representing the tile arrangement for a game of Catan.

    Tile assortment param in format (num_brick, num_grain, num_lumber, num_ore, num_wool, num_desert)
    """
    # pasture
    chars = "BGLOWD"
    possible_tiles = [chars[idx] for idx, count in enumerate(tile_assortment) for _ in range(count)]
    # Deal with special case non-default tile assortments which may have more tiles than will be used
    if len(possible_tiles) > num_tiles:
        # randomly sample to get right number
        possible_tiles = random.sample(possible_tiles, num_tiles)
    # Shuffle the tiles:
    random.shuffle(possible_tiles)
    return "".join(possible_tiles)


def place_init_settlements(brd_state):
    """
    Places initial settlements for each player on the board, for a brand new game of Catan.
    """
    # For now, just arbitrarily chosen
    place_settlement(brd_state, 0, 3, 3, False)
    place_settlement(brd_state, 0, 3, 7, False)
    place_road(brd_state, 0, 3, 4, False)
    place_road(brd_state, 0, 3, 8, False)
    place_settlement(brd_state, 1, 3, 9, False)
    place_settlement(brd_state, 1, 3, 13, False)
    place_road(brd_state, 1, 3, 10, False)
    place_road(brd_state, 1, 3, 14, False)
    place_settlement(brd_state, 2, 9, 3, False)
    place_settlement(brd_state, 2, 9, 7, False)
    place_road(brd_state, 2, 9, 4, False)
    place_road(brd_state, 2, 9, 8, False)
    place_settlement(brd_state, 3, 9, 9, False)
    place_settlement(brd_state, 3, 9, 13, False)
    place_road(brd_state, 3, 9, 10, False)
    place_road(brd_state, 3, 9, 14, False)

    # Distribute initial resources based on initial settlements


def is_adjacent_to_building(brd_state, vertex_r, vertex_c):
    """
    Checks if a vertex on the board is adjacent to a building (connected by single road/hex border).
    Note: in bmap, row, col+-2 is always an adjacent vertex, but row+-2, col is only adjacent if row+-1, col is a road
    Because the center of a hex will never be occupied, we do not have to treat this as a special case and just check
    north and south regardless

    Parameters:
    - brd_state (dict): The board state.
    - vertex_r (int): The row of the vertex on the board.
    - vertex_c (int): The column of the vertex on the board.
    """

    # Check east, west, north, and south vertices for buildings
    return brd_state["built_map"][vertex_r] & (1 << (vertex_c - 2)) or brd_state["built_map"][vertex_r] & (
                1 << (vertex_c + 2)) or brd_state["built_map"][vertex_r - 2] & (1 << vertex_c) or \
        brd_state["built_map"][vertex_r + 2] & (1 << vertex_c)


# def edge_road_buildable(brd_state, player_idx, row, col):
#     """
#     Checks if a road can be built at an edge on the board, for the given player.
#
#     Does not consider whether the player has sufficient resources to build the road.
#     """
#     # Check if location is valid edge, and that it is empty
#     if not RMAP[row] & (1 << col) or brd_state["built_map"][row] & (1 << col):
#         return False
#     # Check if adjacent to building
#     if not is_adjacent_to_building(brd_state, row, col):
#         return False
#     # TODO: create method for checking all possible colors that can build here?


def find_buildable_roads(brd_state, player_idx) -> tuple:
    """
    Finds all buildable road locations for a player on the board.
    Useful note: All roads must be adjacent to another road; buildings need not be considered. Any building we may be
    building from must have had at least one connected road already
    TODO: doesn't consider blocking by enemy buildings

    Returns:
    - tuple: A tuple of tuples, each representing a buildable road location.
    """
    player_hand = "rbmap" + str(player_idx)
    buildable_roads = []
    # TODO: potentially switch between methods based on depth into current game (method 1 may be better when players
    #   have a lot of roads)
    # # METHOD 1: check all edges, and check if adjacent to road of given color
    # # Ignore water buffers; currently hard-coded for standard 19 tile board
    # for row in range(1, 12):  # 13 rows including water buffers
    #     for col in range(1, 22):  # 23 cols including water buffers
    #         # Valid edge, and empty
    #         if RMAP[row] & (1 << col) and brd_state["built_map"][row] & (1 << col) == 0:
    #             # Adjacent to road of given color
    #             # with even or odd rows, check NE, SE, SW, NW (true adjacents for even rows)
    #             if (brd_state[player_hand][row+1] & (1 << (col-1)) or
    #                     brd_state[player_hand][row - 1] & (1 << (col - 1)) or
    #                     brd_state[player_hand][row - 1] & (1 << (col + 1)) or
    #                     brd_state[player_hand][row + 1] & (1 << (col + 1))):
    #                 buildable_roads.append((row, col))
    #             if row % 2 != 0:  # with odd rows, check E & W as well
    #                 if brd_state[player_hand][row] & (1 << (col-2)) or brd_state[player_hand][row] & (1 << (col + 2)):
    #                     buildable_roads.append((row, col))

    # METHOD 2: Start from player's existing roads, and check adjacent edges
    # And with road map to get only player's roads
    curr_roads = [player_map_val & RMAP[idx] for idx, player_map_val in enumerate(brd_state[player_hand])]
    for row_idx, row in enumerate(curr_roads):
        if row != 0:  # if player has >= 1 road in this row
            for col in range(1, 22):  # 23 cols including water buffers
                if row & (1 << col):  # if player has road at this edge
                    # Check adjacent edges for valid and empty edges
                    # North is positive (row), West is positive (col)
                    # Check NE
                    if RMAP[row_idx+1] & (1 << (col - 1)) and brd_state["built_map"][row_idx+1] & (1 << (col - 1)) == 0:
                        buildable_roads.append((row_idx, col - 1))
                    # Check SE
                    if RMAP[row_idx-1] & (1 << (col - 1)) and brd_state["built_map"][row_idx-1] & (1 << (col - 1)) == 0:
                        buildable_roads.append((row_idx, col - 1))
                    # Check SW
                    if RMAP[row_idx-1] & (1 << (col + 1)) and brd_state["built_map"][row_idx-1] & (1 << (col + 1)) == 0:
                        buildable_roads.append((row_idx, col - 1))
                    # Check NW
                    if RMAP[row_idx+1] & (1 << (col + 1)) and brd_state["built_map"][row_idx+1] & (1 << (col + 1)) == 0:
                        buildable_roads.append((row_idx, col - 1))
                    if row % 2 != 0:  # with odd rows, E & W are adjacent edges
                        # Check E
                        if RMAP[row_idx] & (1 << (col - 2)) and brd_state["built_map"][row_idx] & (1 << (col - 2)) == 0:
                            buildable_roads.append((row_idx, col + 1))
                        # Check W
                        if RMAP[row_idx] & (1 << (col + 2)) and brd_state["built_map"][row_idx] & (1 << (col + 2)) == 0:
                            buildable_roads.append((row_idx, col - 2))

    return tuple(buildable_roads)


def place_settlement(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a settlement for a player at a vertex on the board.

    Parameters:
    - brd_state (dict): The board state.
    - player_idx (int): The index of the player placing the settlement.
    - v (int): The index of the vertex on the board at which to place the settlement.

    Preconditions:
    - The vertex is valid, and has no adjacent buildings.
    - The vertex is empty.
    - The player has sufficient resources.
    """
    hand = "rbmap" + str(player_idx)
    brd_state[hand][row] |= (1 << col)
    brd_state["built_map"][row] |= (1 << col)
    if consume_res:
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.B.value] -= 1
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.G.value] -= 1
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.L.value] -= 1
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.W.value] -= 1


def place_city(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a city for a player at a vertex on the board.

    Parameters:
    - brd_state (dict): The board state.
    - player_idx (int): The index of the player placing the city.
    - v (int): The index of the vertex on the board at which to place the city.

    Preconditions:
    - The vertex is valid, and has no adjacent buildings.
    - The vertex has a settlement of the player's color.
    - The player has sufficient resources.
    """
    hand = "rbmap" + str(player_idx)
    brd_state[hand][row] |= (1 << col)
    # NOTE: no need to set built_map here, since it is already set for settlements (unchecked precondition)
    # indicate city by setting bit in building type map
    brd_state["btypemap"][row] |= (1 << col)
    if consume_res:
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.G.value] -= 2
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.O.value] -= 3


def place_road(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a road for a player at an edge on the board.

    Parameters:
    - brd_state (dict): The board state.
    - player_idx (int): The index of the player placing the road.
    - row (int): The row of the edge on the board at which to place the road.
    - col (int): The column of the edge on the board at which to place the road.

    Preconditions:
    - The edge is valid, and has is connected to a building/road of the player's color.
    - The edge is empty.
    - The player has sufficient resources.
    """
    hand = "rbmap" + str(player_idx)
    brd_state[hand][row] |= (1 << col)
    brd_state["built_map"][row] |= (1 << col)
    if consume_res:
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.B.value] -= 1
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.L.value] -= 1


# Methods for saving/loading board state from file
def save_state_to_json(brd_state_object, fn="./boards/brd_state.json"):
    """
    Save the game state to a JSON file.

    Parameters:
    - game_state (dict): The game state to be saved.
    - file_path (str): The path to the JSON file.
    """
    with open(BOARD_STATES_DIR + fn, 'w') as json_file:
        json.dump(brd_state_object, json_file, indent=4)


def load_state_from_json(fn):
    """
    Load the game state from file.

    Parameters:
    - fn (str): The name of the JSON file.

    Returns:
    - dict: The loaded game state.
    """
    with open(BOARD_STATES_DIR + fn, 'r') as json_file:
        game_state = json.load(json_file)
    return game_state
