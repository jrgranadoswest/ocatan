import os
import random
import json
import time
from constants import *


# New board state generation methods
def generate_new_board(num_players=4):
    """
    Generates a new board state (complete).
    :param num_players: The number of players in the game.
    :return: A new board state, with randomized board arrangement, token arrangement, and port arrangement.
    """
    new_brd = {
        "game_cycle_status": 0,  # 0: normal part of turn, 1: placement of robber (& stealing), 2: road placement (for dev)
        # Board state representation (currently static, filled with arbitrary board)
        # 0123456789..18
        "num_players": num_players,
        "curr_turn": 0,  # player 0 arbitrarily goes first
        "hex_state": gen_tile_arrangement(),
        "dv1": random.randint(1, 6),
        "dv2": random.randint(1, 6),
        # TODO: define constants for below
        # orientation values for ports at each hex idx, 6 means no port
        "port_orients": "6343665266661665610",
        # map dice sums (dicesum-2 = idx) to vertex beneficiaries
        "bank": [19, 19, 19, 19, 19,  # Brick grain lumber ore wool
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
                  0,  # current true victory points
                  0,  # length of current longest road
                  0,  # roads made
                  0,  # settlements made
                  0,  # cities made

                  # Player 2 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,

                  # Player 3 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  # Player 4 hand
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  ],

        "btypemap": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap0": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap1": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap2": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap3": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # TODO: should the 'anded together' map be stored in the board state?
        "built_map": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # all player developments anded together
    }
    # TODO: assumes at least one desert in board arrangement; implement flexibility for no desert
    new_brd["robber_loc"] = new_brd["hex_state"].index("D")
    # port types for port at each hex idx, 6: no port
    new_brd["port_type_state"] = gen_port_types(new_brd["port_orients"])
    # hex codes for different chance values, 0 means no token (desert)
    new_brd["tkn_state"] = gen_token_arrangement(new_brd["hex_state"])
    new_brd["dice_sum"] = new_brd["dv1"] + new_brd["dv2"]
    # Map vertices to the resources they produce
    new_brd["vresmap"] = gen_vertex_resource_map(new_brd["hex_state"], new_brd["tkn_state"], new_brd["port_orients"],
                                                 new_brd["port_type_state"])
    new_brd["dv_to_hex_map"] = gen_dv_to_hex_map(new_brd["hex_state"], new_brd["tkn_state"])

    place_init_settlements(new_brd)
    for pidx in range(num_players):
        new_brd["hands"][pidx * HAND_OFFSET + HIdx.LEN_LNGST_ROAD.value] = 1  # Everyone has 1 road from each settlement
    return new_brd


#  TODO: don't pass entire board state when not necessary
def identify_built_players_robber(brd_state: dict, hex_idx: int, robber_pidx: int) -> list:
    """
    Returns a list of player indices who have built on the given hex index.
    Repeats indices if multiple buildings are built on the hex by the same player.
    :param brd_state: Board state.
    :param hex_idx: The hex index to check; potential robber location.
    :param robber_pidx: The player index of the player moving the robber.
    :return: A list of player indices who have built on the given hex index & can be stolen from.
    """
    # 24 loop iterations 4*6
    # Check if any players have built on the hex first: 6 checks, then 4 checks if true
    built_players = []
    for v in HEX_IDX_TO_VERTICES[hex_idx]:
        if brd_state["built_map"][v[0]] & (1 << v[1]):  # check if anyone has built on vertex
            for pidx in range(brd_state["num_players"]):  # Find which player
                # Because this is specifically for stealing, we only add a potential player if they have >0 resources,
                # they are not the player moving the robber, and they have built on the vertex
                if pidx != robber_pidx and brd_state["rbmap" + str(pidx)][v[0]] & (1 << v[1]) and sum(brd_state["hands"][pidx * HAND_OFFSET:pidx * HAND_OFFSET + 5]) > 0:
                    built_players.append(pidx)
                    break
    return built_players


def robber_steal(brd_state: dict, victim_idx: int, perpetrator_idx: int):
    """
    Steals a random resource from the victim and gives it to the perpetrator.
    Preconditions:
    - Assumes that the victim has at least one resource.
    :param brd_state: Board state.
    :param victim_idx: The player index of the player being stolen from.
    :param perpetrator_idx: The player index of the player stealing.
    """
    resource_val = random.choice([i for i, num in enumerate(brd_state["hands"][victim_idx * HAND_OFFSET:victim_idx * HAND_OFFSET + 5]) if num > 0])
    brd_state["hands"][victim_idx * HAND_OFFSET + resource_val] -= 1  # remove resource from victim's hand
    assert brd_state["hands"][victim_idx * HAND_OFFSET + resource_val] >= 0
    brd_state["hands"][perpetrator_idx * HAND_OFFSET + resource_val] += 1  # add resource to perpetrator's hand


def roll_dice(brd_s, dv1=None, dv2=None, conduct_robber=True):
    """
    Game logic for dice roll.
    :param brd_s: Board state.
    :param dv1: The first dice value; used for replay mode when we don't want to roll the dice.
    :param dv2: The second dice value; used for replay mode when we don't want to roll the dice.
    :param conduct_robber: Whether or not to conduct robber action; for use in some player agents.
    """
    if dv1 is None or dv2 is None:
        dv1 = random.randint(1, 6)
        dv2 = random.randint(1, 6)
    brd_s["dv1"] = dv1
    brd_s["dv2"] = dv2
    brd_s["dice_sum"] = dv1 + dv2
    harvest_roll_resources(brd_s, dv1 + dv2, conduct_robber)


# Tested
def gen_vertex_resource_map(hex_arrangement: str, token_arrangement: str, port_orients: str, port_types: str) -> dict:
    """
    Generates a dictionary of tuples representing the resources produced by each vertex on the board.
    key format: tuple: (row, col)
    Option 1: tuple: (res1, diceval1, res2, diceval2, res3, diceval3, porttype)
    Option 2: tuple: (hexidx1, hexidx2, hexidx3, porttype)
    :param hex_arrangement: A string of characters representing the tile arrangement.
    :param token_arrangement: A string of characters representing the dice value token arrangement.
    :param port_orients: A string of characters representing the port orientation arrangement.
    :param port_types: A string of characters representing the port type arrangement.
    :return: A dictionary of tuples representing the resources produced by each vertex on the board.
    """
    vresmap = dict()
    # Iterate over all vertices (the 1's in BMAP)
    for hex_idx, vertices in enumerate(HEX_IDX_TO_VERTICES):
        resource_id = HEX_LETTER_TO_RES_ID[hex_arrangement[hex_idx]]
        # Decode base 16 dice value character into int
        dice_val = int(token_arrangement[hex_idx], 16)
        for vertex in vertices:
            if vresmap.get(vertex) is None:
                vresmap[vertex] = [resource_id, dice_val]
            else:
                vresmap[vertex].extend([resource_id, dice_val])
    # add empty values for vertices bordering shoreline
    for key in vresmap.keys():
        if len(vresmap[key]) == 2:
            vresmap[key].extend([-1, 0, -1, 0])
        elif len(vresmap[key]) == 4:
            vresmap[key].extend([-1, 0])
        # else:
        #     assert len(vresmap[key]) == 6
    # Add port types & convert to tuple
    # For now, hardcoded due to constant port locations
    pts = [int(pt) for pt in port_types]
    vresmap[(11, 9)].append(pts[0])
    vresmap[(11, 11)].append(pts[0])
    vresmap[(11, 15)].append(pts[1])
    vresmap[(11, 17)].append(pts[1])
    vresmap[(9, 3)].append(pts[2])
    vresmap[(9, 5)].append(pts[2])
    vresmap[(9, 19)].append(pts[3])
    vresmap[(7, 19)].append(pts[3])
    vresmap[(7, 1)].append(pts[4])
    vresmap[(5, 1)].append(pts[4])
    vresmap[(5, 19)].append(pts[5])
    vresmap[(3, 19)].append(pts[5])
    vresmap[(3, 3)].append(pts[6])
    vresmap[(3, 5)].append(pts[6])
    vresmap[(1, 9)].append(pts[7])
    vresmap[(1, 11)].append(pts[7])
    vresmap[(1, 15)].append(pts[8])
    vresmap[(1, 17)].append(pts[8])
    for key in vresmap.keys():
        if len(vresmap[key]) == 6:
            vresmap[key].append(6)  # 6 means non-port
        vresmap[key] = tuple(vresmap[key])
    # for key in vresmap.keys():
    #     assert len(vresmap[key]) == 7
    return vresmap


def place_robber(brd_state: dict, hex_idx: int, steal_idx: int):
    """
    Places the robber on the given hex index, and steal from a random player on that hex
    :param brd_state: Board state.
    :param hex_idx: Hex index to place robber on.
    :param steal_idx: Player index of the player to steal from.
    """
    brd_state["robber_loc"] = hex_idx
    players_to_rob = identify_built_players_robber(brd_state, hex_idx, brd_state["curr_turn"])
    if len(players_to_rob) > 0:
        # Steal resource from player that has built on hex
        robber_steal(brd_state, random.choice(players_to_rob), brd_state["curr_turn"])
        # TODO: remove extraneous prints, or only use on verbose mode
        if global_verbose:
            print("Player " + str(brd_state["curr_turn"]) + " stole from player " + str(players_to_rob[0]))
    else:
        if global_verbose:
            print("Robber placed on hex with no opponent buildings")  # technically could have opponent buildings, but no resources


# Tested
def gen_dv_to_hex_map(hex_arrangement: str, token_arrangement: str) -> tuple:
    """
    Generates a mapping from dice sum to hex indices that produce for that dice roll.
    :param hex_arrangement: A string of characters representing the tile arrangement.
    :param token_arrangement: A string of characters representing the dice value token arrangement.
    :return: A tuple of tuples where the dice sum-2=index, and each tuple is a tuple of hex indices that produce.
    """
    dv_to_hex_map = [() for _ in range(11)]
    # Iterate over all hexes
    for hex_idx, hex_letter in enumerate(hex_arrangement):
        if hex_letter != "D":
            dv_to_hex_map[int(token_arrangement[hex_idx], 16) - 2] += (hex_idx,)
    return tuple(dv_to_hex_map)


def random_discard(brd_state: dict, player_idx: int, nd: int):
    """
    Randomly discards given number of cards from the player's hand
    Preconditions:
    - Assumes number of cards > nd
    :param brd_state: Board state.
    :param player_idx: Index of the player discarding.
    :param nd: Number of cards to discard.
    """
    card_vals = [brd_state["hands"][player_idx * HAND_OFFSET + i] for i in range(5)]
    card_cumul = [sum(card_vals[:i + 1]) for i in range(5)]
    discard_indices = random.sample(range(card_cumul[4]), nd)
    for i in discard_indices:
        if i < card_cumul[0]:
            card_vals[0] -= 1
            assert card_vals[0] >= 0
            brd_state["bank"][0] += 1
        elif i < card_cumul[1]:
            card_vals[1] -= 1
            assert card_vals[1] >= 0
            brd_state["bank"][1] += 1
        elif i < card_cumul[2]:
            card_vals[2] -= 1
            assert card_vals[2] >= 0
            brd_state["bank"][2] += 1
        elif i < card_cumul[3]:
            card_vals[3] -= 1
            assert card_vals[3] >= 0
            brd_state["bank"][3] += 1
        elif i < card_cumul[4]:
            card_vals[4] -= 1
            assert card_vals[4] >= 0
            brd_state["bank"][4] += 1
        else:
            print("ERROR")
    brd_state["hands"][player_idx * HAND_OFFSET:player_idx * HAND_OFFSET + 5] = card_vals


def enact_robber(brd_state: dict):
    """
    Carries out a roll of 7 on the board.
    :param brd_state: Board state.
    """
    # Iterate over player hands, checking for >7 cards
    for pidx in range(brd_state["num_players"]):
        # First 5 indices of player hand are resources
        n_cards = sum(brd_state["hands"][pidx * HAND_OFFSET:pidx * HAND_OFFSET + 5])
        if n_cards > 7:
            # divide by 2, round down
            random_discard(brd_state, pidx, n_cards // 2)
    # Set board state to reflect robber in action; current player will have to place robber & steal in next action
    brd_state["game_cycle_status"] = 1


# Partially tested (not tested for cities)
def harvest_roll_resources(brd_state: dict, dice_sum: int, conduct_robber=True):
    """
    Distributes resources to players based on the dice roll sum.
    Note: with current implementation, simply continues giving out resources until there are no more of that type in the
    bank. (No effort to distribute evenly or not at all when there are not enough resources in the bank)
    :param brd_state: Board state.
    :param dice_sum: Sum of the dice roll.
    :param conduct_robber: Whether to conduct robber action; for use in some player agents.
    """
    if dice_sum == 7:
        if conduct_robber:
            enact_robber(brd_state)
        return
    hex_ids = brd_state["dv_to_hex_map"][dice_sum - 2]
    # Iterate over all producing hexes
    for hex_id in hex_ids:
        if hex_id != brd_state["robber_loc"]:
            producing_vertices = HEX_IDX_TO_VERTICES[hex_id]
            # Iterate over all producing vertices
            for v in producing_vertices:
                # Could just iterate over all vertices using vresmap.keys(), but this is faster
                # obtain res_val by converting from hex letter to resource id
                res_val = HEX_LETTER_TO_RES_ID[brd_state["hex_state"][hex_id]]
                if res_val != -1:
                    for pidx in range(brd_state["num_players"]):
                        # Check if player has built on vertex
                        if brd_state["rbmap" + str(pidx)][v[0]] & (1 << v[1]) and brd_state["bank"][res_val] > 0:
                            brd_state["hands"][pidx * HAND_OFFSET + res_val] += 1
                            brd_state["bank"][res_val] -= 1
                            assert brd_state["bank"][res_val] >= 0
                            # Check if city is built on vertex
                            if brd_state["btypemap"][v[0]] & (1 << v[1]) and brd_state["bank"][res_val] > 0:
                                brd_state["hands"][pidx * HAND_OFFSET + res_val] += 1  # Add second resource for city
                                brd_state["bank"][res_val] -= 1
                                assert brd_state["bank"][res_val] >= 0


# Tested
def gen_token_arrangement(hex_arrangement: str) -> str:
    """
    Generates a string of characters representing the dice value token arrangement.
    e.g. "B655438830B9A46C92A",
    :param hex_arrangement: A string of characters representing the tile arrangement.
    :return: A string of hexadecimal characters representing the dice sum tile for each hex of the board.
    """
    # NOTE: currently assumes 19 tiles, exactly one desert
    chars = list("B65543883B9A46C92A")
    random.shuffle(chars)
    # insert 0 at desert location
    chars.insert(hex_arrangement.index('D'), '0')
    return "".join(chars)


def print_hands(gb: dict):
    """Prints out all values in the hands array in a readable format."""
    for i in range(len(gb["hands"]) // 5):
        i_mod = i % 5
        print(f"{gb['hands'][i*5:(i+1)*5]} :\t{[HIdx(j).name for j in range(i_mod*5, (i_mod+1)*5)]}")


# Static lookup table for port locations; each entry is a tuple of (hex_idx, port_orientation)
# PORT_LOOKUP = [(0, 2), (0, 3), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4), (6, 4), (6, 5), (11, 4), (11, 5), (11, 0),
#                (15, 5), (15, 0), (18, 5), (18, 0), (18, 1), (17, 0), (17, 1), (16, 0), (16, 1), (16, 2), (12, 1),
#                (12, 2), (7, 1), (7, 2), (7, 3), (3, 2), (3, 3)]

def gen_port_types(port_orients="6343665266661665610") -> str:
    """
    Generates a string of port types for board arrangement.
    :param port_orients: A string of characters representing the port orientation arrangement.
    :return: A string of characters representing the port type arrangement.
    """
    assert len(port_orients) == 19
    port_types = ['0', '1', '2', '3', '4', '5', '5', '5', '5']
    random.shuffle(port_types)
    return "".join(port_types)


def gen_tile_arrangement(tile_assortment=(3, 4, 4, 3, 4, 1), num_tiles=19) -> str:
    """
    Generates a string of characters representing the tile arrangement.
    Tile assortment param in format (num_brick, num_grain, num_lumber, num_ore, num_wool, num_desert)
    :param tile_assortment: A tuple of integers representing the number of each tile type to use.
    :param num_tiles: The number of tiles to use in the arrangement.
    :return: A string of characters representing the tile arrangement.
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


def generate_beginner_board(num_players=4):
    """
    Places initial settlements for each player on the board, based on the catan rulebook "Starting map for beginners"
    (Meant to be a relatively fair board)
    """
    new_brd = {
        "game_cycle_status": 0,
        "num_players": num_players,
        "curr_turn": 0,
        "hex_state": "WGBWGOLOLDLGBWBGLWO",
        "tkn_state": "B655438830B9A46C92A",
        "port_orients": "6343665266661665610",
        "port_type_state": "554053215",
        "dv1": random.randint(1, 6),
        "dv2": random.randint(1, 6),
        "bank": INIT_BANK[:],
        "hands": [0 for _ in range(HAND_OFFSET * num_players)],
        "btypemap": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap0": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap1": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap2": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "rbmap3": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "built_map": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    new_brd["robber_loc"] = new_brd["hex_state"].index("D")
    new_brd["dice_sum"] = new_brd["dv1"] + new_brd["dv2"]
    # Map vertices to the resources they produce
    new_brd["vresmap"] = gen_vertex_resource_map(new_brd["hex_state"], new_brd["tkn_state"], new_brd["port_orients"],
                                                 new_brd["port_type_state"])
    new_brd["dv_to_hex_map"] = gen_dv_to_hex_map(new_brd["hex_state"], new_brd["tkn_state"])

    for pidx in range(num_players):
        new_brd["hands"][pidx * HAND_OFFSET + HIdx.LEN_LNGST_ROAD.value] = 1  # Everyone has 1 road from each settlement

    # Orange
    place_settlement(new_brd, 0, 3, 7, False)
    place_road(new_brd, 0, 3, 8, False)
    place_settlement(new_brd, 0, 9, 11, False)
    place_road(new_brd, 0, 9, 10, False)
    # White
    place_settlement(new_brd, 1, 7, 5, False)
    place_road(new_brd, 1, 6, 5, False)
    place_settlement(new_brd, 1, 5, 15, False)
    place_road(new_brd, 1, 5, 16, False)
    if num_players > 2:
        # Blue
        place_settlement(new_brd, 2, 9, 7, False)
        place_road(new_brd, 2, 8, 7, False)
        place_settlement(new_brd, 2, 9, 15, False)
        place_road(new_brd, 2, 9, 14, False)
    if num_players > 3:
        # Red
        place_settlement(new_brd, 3, 3, 13, False)
        place_road(new_brd, 3, 3, 12, False)
        place_settlement(new_brd, 3, 7, 17, False)
        place_road(new_brd, 3, 7, 16, False)

    # Distribute initial resources based on initial settlements
    # step i: 0, 2, 4
    for i in range(0, 5, 2):
        for pidx, rc_tuple in enumerate([(9, 11), (5, 15), (9, 15), (7, 17)][0:num_players]):

            res_val = new_brd["vresmap"][rc_tuple][i]
            if res_val != -1:
                new_brd["hands"][pidx * HAND_OFFSET + res_val] += 1
                new_brd["bank"][res_val] -= 1

    return new_brd


def place_init_settlements(brd_state):
    """
    Places initial settlements for each player on the board, for a brand new game of Catan.
    Greedy placement version
    TODO: tie break randomly, rather than just based on list order
    Precondition: brd_state is a new board state with no buildings
    :param brd_state: Board state.
    """
    vertices = []
    for v in brd_state["vresmap"].keys():
        tup = brd_state["vresmap"][v]
        total_prob = DICE_SUM_PROBS[tup[1]] + DICE_SUM_PROBS[tup[3]] + DICE_SUM_PROBS[tup[5]]
        vertices.append((total_prob, v))
    vertices.sort(reverse=True)
    # First settlements placed in ascending order
    pidx = 0
    vidx = 0
    while pidx < brd_state["num_players"]:
        # Take available spot with highest probability of getting resources (tie break randomly)
        if not is_adjacent_to_building(brd_state, vertices[vidx][1][0], vertices[vidx][1][1]):
            place_settlement(brd_state, pidx, vertices[vidx][1][0], vertices[vidx][1][1], False)

            # Randomly place road:
            valid_road_rcs = []
            for r, c in [[vertices[vidx][1][0] + 1, vertices[vidx][1][1]],  # S
                         [vertices[vidx][1][0], vertices[vidx][1][1] + 1],  # W
                         [vertices[vidx][1][0], vertices[vidx][1][1] - 1],  # E
                         [vertices[vidx][1][0] - 1, vertices[vidx][1][1]]]:  # N
                if RMAP[r] & (1 << c):  # Don't need to check for init: and brd_state["built_map"][r] & (1 << c) == 0:
                    valid_road_rcs.append((r, c))
            road = random.choice(valid_road_rcs)
            place_road(brd_state, pidx, road[0], road[1], False)

            pidx += 1
        vidx += 1
    pidx -= 1
    # Second settlements placed in descending order
    while pidx > -1:
        if not is_adjacent_to_building(brd_state, vertices[vidx][1][0], vertices[vidx][1][1]):
            place_settlement(brd_state, pidx, vertices[vidx][1][0], vertices[vidx][1][1], False)
            # Distribute initial resources based on initial settlements
            for i in range(0, 5, 2):
                res_val = brd_state["vresmap"][vertices[vidx][1]][i]
                if res_val != -1:
                    brd_state["hands"][pidx * HAND_OFFSET + res_val] += 1
                    brd_state["bank"][res_val] -= 1

            # Randomly place road:
            valid_road_rcs = []
            for r, c in [[vertices[vidx][1][0] + 1, vertices[vidx][1][1]],  # S
                         [vertices[vidx][1][0], vertices[vidx][1][1] + 1],  # W
                         [vertices[vidx][1][0], vertices[vidx][1][1] - 1],  # E
                         [vertices[vidx][1][0] - 1, vertices[vidx][1][1]]]:  # N
                if RMAP[r] & (1 << c):  # Don't need to check for init: and brd_state["built_map"][r] & (1 << c) == 0:
                    valid_road_rcs.append((r, c))
            road = random.choice(valid_road_rcs)
            place_road(brd_state, pidx, road[0], road[1], False)

            pidx -= 1
        vidx += 1


def is_adjacent_to_building(brd_state, vertex_r, vertex_c):
    """
    Checks if a vertex on the board is adjacent to a building (connected by single road/hex border).
    Note: in bmap, row, col+-2 is always an adjacent vertex, but row+-2, col is only adjacent if row+-1, col is a road
    Because the center of a hex will never be occupied, we do not have to treat this as a special case and just check
    north and south regardless

    :param brd_state: Board state.
    :param vertex_r: The row of the vertex on the board.
    :param vertex_c: The column of the vertex on the board.
    :return: True if the vertex is adjacent to a building, else False.
    """
    # Check east, west, north, and south vertices for buildings
    # TODO: fix water buffer to avoid unnecessary checks
    if vertex_r >= 2 and brd_state["built_map"][vertex_r - 2] & (1 << vertex_c):
        return True
    if vertex_r <= 10 and brd_state["built_map"][vertex_r + 2] & (1 << vertex_c):
        return True
    if vertex_c >= 2 and brd_state["built_map"][vertex_r] & (1 << (vertex_c - 2)):
        return True
    return brd_state["built_map"][vertex_r] & (1 << (vertex_c + 2))


def assign_longest_road(brd_state):
    """
    Assigns the longest road bonus to the player with the longest road.
    Tie breaks by precedence; previous holder keeps it if ties are present
    Preconditions:
    - Assumes valid state. That is, only one player, or the bank, holds the longest road card at one point.
        Additionally, all player's recorded longest road lengths are accurate.
    :param brd_state: Board state.
    """
    longest_road = 4
    longest_road_pidx = -1
    # Find current holder of longest road card, if not in bank
    for pidx in range(brd_state["num_players"]):
        if brd_state["hands"][pidx * HAND_OFFSET + HIdx.LNGST_ROAD.value] == 1:
            longest_road = brd_state["hands"][pidx * HAND_OFFSET + HIdx.LEN_LNGST_ROAD.value]
            longest_road_pidx = pidx
    old_holder = longest_road_pidx

    # Find current longest road length & corresponding player
    for pidx in range(brd_state["num_players"]):
        if pidx != old_holder:
            if brd_state["hands"][pidx * HAND_OFFSET + HIdx.LEN_LNGST_ROAD.value] > longest_road:
                longest_road = brd_state["hands"][pidx * HAND_OFFSET + HIdx.LEN_LNGST_ROAD.value]
                longest_road_pidx = pidx

    # Update records if longest_road player has changed
    if old_holder != longest_road_pidx:
        brd_state["hands"][longest_road_pidx * HAND_OFFSET + HIdx.LNGST_ROAD.value] = 1
        brd_state["hands"][longest_road_pidx * HAND_OFFSET + HIdx.TRUE_VP.value] += 2
        if old_holder != -1:  # Previously, different player had longest road card
            brd_state["hands"][old_holder * HAND_OFFSET + HIdx.LNGST_ROAD.value] = 0
            brd_state["hands"][old_holder * HAND_OFFSET + HIdx.TRUE_VP.value] -= 2
        else:  # Previously, longest road card was in the bank
            brd_state["bank"][HIdx.LNGST_ROAD.value] = 0


def assign_largest_army(brd_state):
    """
    Assigns the largest army bonus to the player with the largest army.
    Tie breaks by precedence; previous holder keeps it if ties are present
    Preconditions:
    - Assumes valid state. That is, only one player, or the bank, holds the largest army card at one point.
    :param brd_state: Board state.
    """
    largest_army = 2
    largest_army_pidx = -1
    # Find current holder of largest army card, if not in bank
    for pidx in range(brd_state["num_players"]):
        if brd_state["hands"][pidx * HAND_OFFSET + HIdx.LRGST_ARMY.value] == 1:
            largest_army = brd_state["hands"][pidx * HAND_OFFSET + HIdx.PLAYED_KNIGHTS.value]
            largest_army_pidx = pidx
    old_holder = largest_army_pidx

    # Find player with current largest army
    for pidx in range(brd_state["num_players"]):
        if pidx != old_holder:
            if brd_state["hands"][pidx * HAND_OFFSET + HIdx.PLAYED_KNIGHTS.value] > largest_army:
                largest_army = brd_state["hands"][pidx * HAND_OFFSET + HIdx.PLAYED_KNIGHTS.value]
                largest_army_pidx = pidx

    # Update records if largest_army player has changed
    if old_holder != largest_army_pidx:
        brd_state["hands"][largest_army_pidx * HAND_OFFSET + HIdx.LRGST_ARMY.value] = 1
        brd_state["hands"][largest_army_pidx * HAND_OFFSET + HIdx.TRUE_VP.value] += 2
        if old_holder != -1:  # Previously, different player had largest army card
            brd_state["hands"][old_holder * HAND_OFFSET + HIdx.LRGST_ARMY.value] = 0
            brd_state["hands"][old_holder * HAND_OFFSET + HIdx.TRUE_VP.value] -= 2
        else:  # Previously, largest army card was in the bank
            brd_state["bank"][HIdx.LRGST_ARMY.value] = 0


def find_len_longest_road(brd_state, player_idx):
    """
    Finds the length of the longest road for a player on the board.
    Performs a grid search for roads, and uses DFS to find longest connected road system.
    :param brd_state: Board state.
    :param player_idx: Index of the player for whom to check longest road.
    :return: Length of the longest road for the player.
    """
    # Obtain map of just player's roads
    rdmap = [brd_state["rbmap" + str(player_idx)][i] & RMAP[i] for i in range(13)]
    # # TODO: account for blocking houses
    # # Obtain map of just enemy buildings
    # bmap = [(brd_state["built_map"][i] & BMAP[i]) & (~brd_state["rbmap" + str(player_idx)][i]) for i in range(13)]

    def is_road(r, c):
        """Check road location for player"""
        return rdmap[r] & (1 << c)

    def dfs(r, c, visited):
        """Run dfs to find longest road from given road edge"""
        if (r, c) in visited:
            return 0
        visited.add((r, c))

        path_length = 1
        # Directions: NE, SE, SW, NW
        directions = [(1, -1), (-1, -1), (-1, 1), (1, 1)]
        if r % 2 != 0:  # with odd rows, E & W are adjacent edges
            # Directions: NE, SE, SW, NW, W
            directions = [(1, -1), (-1, -1), (-1, 1), (1, 1), (0, 2)]
            if c > 1:  # E; have to check to avoid out of bounds exception
                directions.append((0, -2))
        for dr, dc in directions:
            newRow, newCol = r + dr, c + dc
            if is_road(newRow, newCol):
                path_length = max(path_length, 1 + dfs(newRow, newCol, visited))

        visited.remove((r, c))
        return path_length

    max_len = 0
    # Iterate over all hex edges
    for row in range(1, len(rdmap)-1):  # 13 rows, skip water buffers
        for col in range(1, 22):  # 23 cols including water buffers
            if rdmap[row] & (1 << col):  # if player has road at this edge
                # NOTE: could improve efficiency: currently finds longest road from each road edge, but could
                # potentially improve by caching longest road from visited edges
                max_len = max(max_len, dfs(row, col, set()))
    return max_len


def find_buildable_roads(brd_state, player_idx) -> tuple:
    """
    Finds all buildable road locations for a player on the board.
    Useful note: All roads must be adjacent to another road; buildings need not be considered. Any building we may be
    building from must have had at least one connected road already
    TODO: doesn't consider blocking by enemy buildings
    :param brd_state: Board state.
    :param player_idx: Index of the player for whom to find buildable roads.
    :return: A tuple of tuples, each representing a buildable road location.
    """
    if brd_state["hands"][player_idx * HAND_OFFSET + HIdx.RDS_BUILT.value] >= MAX_ROADS:
        return ()
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
                    if RMAP[row_idx + 1] & (1 << (col - 1)) and brd_state["built_map"][row_idx + 1] & (
                            1 << (col - 1)) == 0:
                        buildable_roads.append((row_idx+1, col - 1))
                    # Check SE
                    if RMAP[row_idx - 1] & (1 << (col - 1)) and brd_state["built_map"][row_idx - 1] & (
                            1 << (col - 1)) == 0:
                        buildable_roads.append((row_idx-1, col - 1))
                    # Check SW
                    if RMAP[row_idx - 1] & (1 << (col + 1)) and brd_state["built_map"][row_idx - 1] & (
                            1 << (col + 1)) == 0:
                        buildable_roads.append((row_idx-1, col + 1))
                    # Check NW
                    if RMAP[row_idx + 1] & (1 << (col + 1)) and brd_state["built_map"][row_idx + 1] & (
                            1 << (col + 1)) == 0:
                        buildable_roads.append((row_idx+1, col + 1))
                    if row % 2 != 0:  # with odd rows, E & W are adjacent edges
                        # Check E
                        if RMAP[row_idx] & (1 << (col - 2)) and brd_state["built_map"][row_idx] & (1 << (col - 2)) == 0:
                            buildable_roads.append((row_idx, col - 2))
                        # Check W
                        if RMAP[row_idx] & (1 << (col + 2)) and brd_state["built_map"][row_idx] & (1 << (col + 2)) == 0:
                            buildable_roads.append((row_idx, col + 2))
    return tuple(buildable_roads)


def place_settlement(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a settlement for a player at a vertex on the board.
    :param brd_state: Board state.
    :param player_idx: Index of the player placing the settlement.
    :param row: Settlement location row.
    :param col: Settlement location column.
    :param consume_res: Whether or not to consume resources.
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
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.B.value] >= 0
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.G.value] >= 0
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.L.value] >= 0
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.W.value] >= 0
        brd_state["bank"][HIdx.B.value] += 1
        brd_state["bank"][HIdx.G.value] += 1
        brd_state["bank"][HIdx.L.value] += 1
        brd_state["bank"][HIdx.W.value] += 1
    # increment player's victory points
    brd_state["hands"][player_idx * HAND_OFFSET + HIdx.TRUE_VP.value] += 1
    # increment played settlements
    brd_state["hands"][player_idx * HAND_OFFSET + HIdx.SMENTS_BUILT.value] += 1


def find_buildable_settlements(brd_state, player_idx) -> tuple:
    """
    Finds all buildable settlement locations for a player on the board.
    :param brd_state: Board state.
    :param player_idx: Index of player to check for possible settlement locations.
    :return: A tuple of tuples, each representing a buildable settlement location.
    """
    player_hand = "rbmap" + str(player_idx)
    buildable_settlements = []
    # All valid building locations that are connected to player's road
    # curr_roads = [player_map_val & RMAP[idx] for idx, player_map_val in enumerate(brd_state[player_hand])]
    # TODO: make this method more efficient
    for row_idx, row in enumerate(brd_state[player_hand]):
        for col in range(1, 22):
            # Check if valid vertex, and empty, and not adjacent to other building
            if BMAP[row_idx] & (1 << col) and brd_state["built_map"][row_idx] & (1 << col) == 0 and \
                    not is_adjacent_to_building(brd_state, row_idx, col):
                # Check W, E, S, N for adj road
                if (row & (1 << col + 1) or row & (1 << col - 1) or brd_state[player_hand][row_idx + 1] & (1 << col) or
                        brd_state[player_hand][row_idx - 1] & (1 << col)):
                    buildable_settlements.append((row_idx, col))
    return tuple(buildable_settlements)


def find_buildable_cities(brd_state, player_idx) -> tuple:
    """
    Finds all buildable city locations for a player on the board.
    :param brd_state: Board state.
    :param player_idx: Index of player to check for possible city locations.
    :return: A tuple of tuples, each representing a buildable city location.
    """
    # Simply return all settlement locations of the player's color
    player_hand = "rbmap" + str(player_idx)
    buildable_cities = []
    for row in range(1, 12):  # 13 rows including water buffers
        if brd_state[player_hand][row] != 0:
            for col in range(1, 22):  # 23 cols including water buffers
                # Valid vertex, and has player's settlement
                if BMAP[row] & (1 << col) and brd_state[player_hand][row] & (1 << col) and \
                        brd_state["btypemap"][row] & (1 << col) == 0:
                    buildable_cities.append((row, col))
    return tuple(buildable_cities)


def place_city(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a city for a player at a vertex on the board.
    Preconditions:
    - The vertex is valid, and has no adjacent buildings.
    - The vertex has a settlement of the player's color.
    - The player has sufficient resources.
    :param brd_state: Board state.
    :param player_idx: Index of the player placing the city.
    :param row: City location row.
    :param col: City location column.
    :param consume_res: Whether or not to consume resources.
    """
    hand = "rbmap" + str(player_idx)
    brd_state[hand][row] |= (1 << col)
    # NOTE: no need to set built_map here, since it is already set for settlements (unchecked precondition)
    # indicate city by setting bit in building type map
    brd_state["btypemap"][row] |= (1 << col)
    if consume_res:
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.G.value] -= 2
        brd_state["hands"][player_idx * HAND_OFFSET + HIdx.O.value] -= 3
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.G.value] >= 0
        assert brd_state["hands"][player_idx * HAND_OFFSET + HIdx.O.value] >= 0
        brd_state["bank"][HIdx.G.value] += 2
        brd_state["bank"][HIdx.O.value] += 3
    # increment player's victory points
    brd_state["hands"][player_idx * HAND_OFFSET + HIdx.TRUE_VP.value] += 1
    # increment played cities
    brd_state["hands"][player_idx * HAND_OFFSET + HIdx.CITIES_BUILT.value] += 1
    # decrement settlements; converted one
    brd_state["hands"][player_idx * HAND_OFFSET + HIdx.SMENTS_BUILT.value] -= 1


def place_road(brd_state, player_idx, row, col, consume_res=True):
    """
    Places a road for a player at an edge on the board.
    Preconditions:
    - The edge is valid, and has is connected to a building/road of the player's color.
    - The edge is empty.
    - The player has sufficient resources.
    :param brd_state: Board state.
    :param player_idx: Index of the player placing the road.
    :param row: Road location row.
    :param col: Road location column.
    :param consume_res: Whether or not to consume resources.
    """
    offset = player_idx * HAND_OFFSET
    hand = "rbmap" + str(player_idx)
    assert RMAP[row] & (1 << col)
    assert brd_state["built_map"][row] & (1 << col) == 0
    brd_state[hand][row] |= (1 << col)
    brd_state["built_map"][row] |= (1 << col)
    if consume_res:
        brd_state["hands"][offset + HIdx.B.value] -= 1
        assert brd_state["hands"][offset + HIdx.B.value] >= 0
        brd_state["hands"][offset + HIdx.L.value] -= 1
        assert brd_state["hands"][offset + HIdx.L.value] >= 0
        brd_state["bank"][HIdx.B.value] += 1
        brd_state["bank"][HIdx.L.value] += 1
    brd_state["hands"][offset + HIdx.RDS_BUILT.value] += 1
    assert brd_state["hands"][offset + HIdx.RDS_BUILT.value] <= MAX_ROADS


def game_over(brd_state):
    """Check if game is won."""
    return any([brd_state["hands"][player_idx * HAND_OFFSET + HIdx.TRUE_VP.value] >= WINNING_VPS
                for player_idx in range(brd_state["num_players"])])


def get_winner(brd_state):
    """Returns the index of the winning player, or -1 if no winner."""
    for pidx in range(brd_state["num_players"]):
        if brd_state["hands"][pidx * HAND_OFFSET + HIdx.TRUE_VP.value] >= WINNING_VPS:
            return pidx
    return -1


def restore_board_state_from_json(brd_state):
    """Restores fields of board state that don't convert to json."""
    brd_state["vresmap"] = gen_vertex_resource_map(brd_state["hex_state"], brd_state["tkn_state"],
                                                   brd_state["port_orients"],
                                                   brd_state["port_type_state"])
    brd_state["dv_to_hex_map"] = gen_dv_to_hex_map(brd_state["hex_state"], brd_state["tkn_state"])


def filter_dict(board_state):
    """Filters out keys that can't convert to json."""
    excluded = ["vresmap", "dv_to_hex_map"]  # keys for objects that don't convert to json
    filtered_dict = {key: value for key, value in board_state.items() if key not in excluded}
    return filtered_dict


# Methods for saving/loading board state from file
def save_state_to_json(brd_state_object, fn=""):
    """
    Save the game state to a JSON file.
    :param brd_state_object: The game state to be saved.
    :param fn: Name of the JSON file.
    :return: Path to the created file.
    """
    if fn == "":
        fn = "board_state_" + str(int(time.time())) + ".json"
    if not os.path.exists(BOARD_STATES_DIR):
        os.makedirs(BOARD_STATES_DIR)
    with open(make_unique_fn(BOARD_STATES_DIR + fn), 'w') as json_file:
        json.dump(filter_dict(brd_state_object), json_file, indent=4)
    return BOARD_STATES_DIR + fn


def make_unique_fn(fp):
    """
    Checks if a file exists at the given path, and if so, appends a number to the end of the filename to make it
    unique.
    Preconditions:
    - Assumes parent directory exists.
    :param fp: Filepath to try.
    :return: Unique filepath, based on given proposed filepath.
    """
    base, ext = os.path.splitext(fp)
    count = 1
    new_filename = fp
    while os.path.exists(new_filename):
        if global_verbose:
            print("File already exists: ", base, "; making variation")
        new_filename = f"{base}{count}{ext}"
        count += 1

    return new_filename


def save_stats_to_csv(fp: str, stats: list):
    write_header = False
    if not os.path.exists(fp):
        write_header = True
    with open(fp, "a") as file:
        if write_header:
            file.write(STAT_HEADER_STR)
        for stat_line in stats:
            file.write(",".join([str(stat) for stat in stat_line]) + "\n")


def save_game_to_json(game_state, moves, fn=""):
    """
    Save a full game history to a JSON file.
    Involves 1 large JSON object with 2 keys: "game_state" and "moves"
    "moves" is essentially an array of arrays, where the arrays are each move taken sequentially in the game
    :param game_state: Game state to be saved.
    :param moves: Moves taken in the game.
    :param fn: Name of the JSON file.
    :return: Path to the created file.
    """
    saveable_moves = []
    for move in moves:
        if len(move) > 1:
            saveable_moves.append([move[0].value] + list(move[1:]))
        else:
            saveable_moves.append([move[0].value])
    if fn == "":
        fn = "game_" + str(int(time.time())) + "_.json"
    if not os.path.exists(GAME_STATES_DIR):
        os.makedirs(GAME_STATES_DIR)
    with open(make_unique_fn(GAME_STATES_DIR + fn), 'w') as json_file:
        json.dump({"game_state": filter_dict(game_state), "moves": saveable_moves}, json_file, indent=4)
    return GAME_STATES_DIR + fn


def load_game_from_json(fp):
    """Load a full game history from a JSON file."""
    with open(fp, 'r') as json_file:
        game_state = json.load(json_file)
    restore_board_state_from_json(game_state["game_state"])
    game_state["moves"] = [[Act(move[0])] + move[1:] for move in game_state["moves"]]
    return game_state["game_state"], game_state["moves"]


def load_state_from_json(fn, just_layout=False):
    """Load the game state from file."""
    with open(BOARD_STATES_DIR + fn, 'r') as json_file:
        game_state = json.load(json_file)
    if just_layout:
        hands = ["rbmap" + str(i) for i in range(game_state["num_players"])]
        for hand in hands:
            game_state[hand] = [0 for _ in range(13)]  # TODO: fix water buffers
        for i in range(game_state["num_players"]):
            game_state["hands"] = [0 for _ in range(HAND_OFFSET * game_state["num_players"])]
        game_state["built_map"] = [0 for _ in range(13)]
        game_state["btypemap"] = [0 for _ in range(13)]
        game_state["robber_loc"] = game_state["hex_state"].index("D")
        # Restore bank to initial state
        game_state["bank"] = [19, 19, 19, 19, 19, 14, 5, 2, 2, 2, 1, 1, ]
        restore_board_state_from_json(game_state)
    return game_state
