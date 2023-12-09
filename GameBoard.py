import random
from copy import deepcopy
from constants import HAND_OFFSET, Act, HIdx
from util import *


# TODO: consider in AI heuristics when robber is on a hex


def generate_successor(gb: dict, action: tuple):
    """Generate an independent successor game board state, independent of the old state object"""
    # create a copy of the board state, completely independent from old board state
    new_gb = deepcopy(gb)
    take_move(new_gb, action)
    return new_gb


def generate_successor_dice_separate(gb: dict, action: tuple):
    """Generate an independent successor game board state, independent of the old state object"""
    # create a copy of the board state, completely independent from old board state
    new_gb = deepcopy(gb)
    if action[0] == Act.END_TURN:
        pidx = new_gb["curr_turn"]
        offset = HAND_OFFSET * pidx
        new_gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] = 0
        # Check for playable dev cards
        for i in range(5):
            if i == 0 or i == 2:  # Knight or Road Builder
                if new_gb["hands"][offset + i + HIdx.KNIGHT.value] > 0:
                    # NOTE: we don't check here if the player has maxed out their road building
                    new_gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] |= 1 << i
        # TODO: implement other three dev cards
        new_gb["hands"][offset + HIdx.PLAYED_DEV.value] = 0
        new_gb["curr_turn"] = (new_gb["curr_turn"] + 1) % new_gb["num_players"]
    elif action[0] == Act.DICE_ROLL:
        roll_dice(new_gb, action[1], action[2], False)
    else:
        take_move(new_gb, action)
    return new_gb


def take_move(gb: dict, action: tuple):
    """
    Take a move on the game board
    :param gb: Read "GameBoard"; current game state
    :param action: tuple; action to take; format: (move_type, *args)
    For roads, cities, and settlements, tuple is (move_type, row, col)
    For dev cards (purchase) tuple is just (move_type, )
    For bank trades, tuple is (move_type, resource_idx, num_to_trade, requested_resource_idx)
    For playing dev cards, tuple is (move_type, dev_card_id)
    """
    # for idx, val in enumerate(gb["hands"]):
    #     if val < 0:
    #         print(f"NEGATIVE HAND VALUE, {idx} : {HIdx(idx % HAND_OFFSET)}: {val}")
    #         raise ValueError("Negative hand value")


    pidx = gb["curr_turn"]
    offset = HAND_OFFSET * pidx
    if action[0] == Act.END_TURN:
        # Reset player's playable dev cards & played dev card status
        gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] = 0
        # Check for playable dev cards
        for i in range(5):
            if i == 0 or i == 2:  # Knight or Road Builder
                if gb["hands"][offset + i + HIdx.KNIGHT.value] > 0:
                    # NOTE: we don't check here if the player has maxed out their road building
                    gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] |= 1 << i
        # if gb["hands"][offset + HIdx.KNIGHT.value] > 0:
        #     gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] |= 1
        # if gb["hands"][offset + HIdx.RD_BLDR.value] > 0:
        #     gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] |= 1 << 2  # 3rd bit, skip unplayable VP card bit
        gb["hands"][offset + HIdx.PLAYED_DEV.value] = 0

        gb["curr_turn"] = (pidx + 1) % gb["num_players"]
        if len(action) > 1:  # For game replay
            roll_dice(gb, action[1], action[2])
        else:
            roll_dice(gb)

    elif action[0] == Act.ROAD:
        if gb["game_cycle_status"] == 2 or gb["game_cycle_status"] == 3:  # Placing road from road builder dev card
            assert gb["hands"][offset + HIdx.RDS_BUILT.value] < MAX_ROADS
            place_road(gb, pidx, action[1], action[2], False)
            # Update game cycle status; no second road if we have run out of roads
            gb["game_cycle_status"] = 3 if (
                        gb["game_cycle_status"] == 2 and gb["hands"][offset + HIdx.RDS_BUILT.value] < MAX_ROADS) else 0
        else:
            place_road(gb, pidx, action[1], action[2], True)
        # Run longest road update in case it was just achieved
        new_longest_len_road = find_len_longest_road(gb, pidx)
        if new_longest_len_road > gb["hands"][offset + HIdx.LEN_LNGST_ROAD.value]:
            gb["hands"][offset + HIdx.LEN_LNGST_ROAD.value] = new_longest_len_road
            # Check if this player now holds the longest road
            if gb["hands"][offset + HIdx.LEN_LNGST_ROAD.value] >= 5:
                assign_longest_road(gb)
    elif action[0] == Act.SETTLEMENT:
        place_settlement(gb, pidx, action[1], action[2], True)
    elif action[0] == Act.CITY:
        place_city(gb, pidx, action[1], action[2], True)
    elif action[0] == Act.DEV_CARD:
        buy_dev_card(gb, pidx)
    elif action[0] == Act.PLAY_DEV:
        play_dev_card(gb, action[1])
        if action[1] == HIdx.KNIGHT.value:  # Played knight
            if gb["hands"][offset + HIdx.PLAYED_KNIGHTS.value] >= 3:
                # Run largest army update in case it was just achieved
                assign_largest_army(gb)
    elif action[0] == Act.BANK_TRADE:
        trade_with_bank(gb, pidx, action[1], action[2], action[3])
    elif action[0] == Act.PLACE_ROBBER:
        place_robber(gb, action[1], action[2])
        gb["game_cycle_status"] = 0
    else:
        raise ValueError("Invalid action type")


def trade_with_bank(gb: dict, pidx: int, resource_idx: int, num_to_trade: int, requested_resource_idx: int):
    """
    Trade with the bank
    Preconditions:
    - player has enough resources
    - proposed trade is valid
    :param gb: Read "GameBoard"; current game state
    :param pidx: int [0, <num players>)
    :param resource_idx: int [0, 4]; index of resource to trade
    :param num_to_trade: int [1, 4]; number of resources to trade
    :param requested_resource_idx: int [0, 4]; index of resource to receive
    """
    offset = HAND_OFFSET * pidx
    # Consume resources
    gb["hands"][offset + resource_idx] -= num_to_trade
    assert gb["hands"][offset + resource_idx] >= 0
    gb["bank"][resource_idx] += num_to_trade
    # Give requested resource
    gb["hands"][offset + requested_resource_idx] += 1
    gb["bank"][requested_resource_idx] -= 1
    assert gb["bank"][requested_resource_idx] >= 0


def act_invalid(brd_state: dict, act_tuple):
    """Checks if an action is valid; used for human players"""
    possible_moves = find_moves(brd_state, brd_state["curr_turn"])
    # Get unique action types
    act_types = set([act[0] for act in possible_moves])
    # Check if the player can perform the general type of action
    if act_tuple[0] not in act_types:
        return True
    # TODO: complete validity checking of actions
    return False


def buy_dev_card(gb: dict, pidx: int):
    """
    Buy a development card
    Preconditions:
    - player has enough resources
    - Assumes board state holds dev cards contiguously; doesn't 100% rely on HIdx
    - Assumes sufficient dev cards in bank hand
    :param gb: Read "GameBoard"; current game state
    :param pidx: int [0, <num players>) Player index buying card
    """
    offset = HAND_OFFSET * pidx
    # Consume resources
    gb["hands"][offset + HIdx.O.value] -= 1
    gb["hands"][offset + HIdx.G.value] -= 1
    gb["hands"][offset + HIdx.W.value] -= 1
    assert gb["hands"][offset + HIdx.O.value] >= 0
    assert gb["hands"][offset + HIdx.G.value] >= 0
    assert gb["hands"][offset + HIdx.W.value] >= 0
    gb["bank"][HIdx.O.value] += 1
    gb["bank"][HIdx.G.value] += 1
    gb["bank"][HIdx.W.value] += 1
    # Select randomly from deck
    dev_cards = [HIdx.KNIGHT.value, HIdx.VP_CRD.value, HIdx.RD_BLDR.value, HIdx.MONO.value, HIdx.YOP.value]
    dev_card_id = random.choices(dev_cards, weights=gb["bank"][HIdx.KNIGHT.value:HIdx.YOP.value + 1])[0]
    # Take from bank, add to hand
    gb["hands"][offset + dev_card_id] += 1
    gb["bank"][dev_card_id] -= 1
    assert gb["bank"][dev_card_id] >= 0
    # Update VP count as appropriate
    if dev_card_id == HIdx.VP_CRD.value:
        gb["hands"][offset + HIdx.TRUE_VP.value] += 1


def play_dev_card(gb: dict, dev_card_id: int):
    """
    Play a development card
    :param gb: Read "GameBoard"; current game state
    :param dev_card_id: int corresponding to HIdx val of dev card
    """
    offset = HAND_OFFSET * gb["curr_turn"]
    if dev_card_id == HIdx.KNIGHT.value:
        gb["game_cycle_status"] = 1  # Set game cycle status to 1 to indicate robber placement
        gb["hands"][offset + HIdx.PLAYED_KNIGHTS.value] += 1  # update stats for largest army
    elif dev_card_id == HIdx.RD_BLDR.value:
        gb["game_cycle_status"] = 2  # Set game cycle status to 2 to indicate road placement
        gb["hands"][offset + HIdx.PLAYED_RD.value] += 1  # update stats (not needed for in-game use)
    elif dev_card_id == HIdx.MONO.value:
        return
    elif dev_card_id == HIdx.YOP.value:
        return
    else:
        return
    # Return card to bank
    gb["hands"][offset + dev_card_id] -= 1
    assert gb["hands"][offset + dev_card_id] >= 0
    gb["bank"][dev_card_id] += 1
    # Mark that player has played a dev card this turn; can't play another
    gb["hands"][offset + HIdx.PLAYED_DEV.value] = 1


def find_moves(gb: dict, turn: int) -> list:
    """
    For current player, find all possible moves
    :param gb: Read "GameBoard"; current game state
    :param turn: int [0, <num players>) Player index making move
    """
    # TODO: to what extent should flexible recipes be supported?
    if gb["game_cycle_status"] == 1:  # Currently placing robber
        return [(Act.PLACE_ROBBER, hex_idx, 0) for hex_idx in range(19) if hex_idx != gb["robber_loc"]]
    offset = HAND_OFFSET * turn
    if gb["game_cycle_status"] == 2 or gb["game_cycle_status"] == 3:  # Currently placing road
        e_moves_roads = [(Act.ROAD, rd[0], rd[1]) for rd in find_buildable_roads(gb, turn)]
        if len(e_moves_roads) > 0:
            return e_moves_roads
        else:  # maxed out on roads or just can't build any, cancel road builder play
            gb["game_cycle_status"] = 0

    e_moves = [
        (Act.END_TURN,), ]  # exact moves: each move is a tuple, with the first item being the general move type id

    if gb["hands"][offset + HIdx.B.value] >= 1 and gb["hands"][offset + HIdx.L.value] >= 1:
        if gb["hands"][offset + HIdx.RDS_BUILT.value] < MAX_ROADS:
            e_moves.extend([(Act.ROAD, rd[0], rd[1]) for rd in find_buildable_roads(gb, turn)])
        if gb["hands"][offset + HIdx.G.value] >= 1 and gb["hands"][offset + HIdx.W.value] >= 1 and gb["hands"][
            offset + HIdx.SMENTS_BUILT.value] < MAX_SETTLEMENTS:
            e_moves.extend([(Act.SETTLEMENT, st[0], st[1]) for st in find_buildable_settlements(gb, turn)])
    if gb["hands"][offset + HIdx.O.value] >= 3 and gb["hands"][offset + HIdx.G.value] >= 2 and gb["hands"][
        offset + HIdx.CITIES_BUILT.value] < MAX_CITIES:
        e_moves.extend([(Act.CITY, ct[0], ct[1]) for ct in find_buildable_cities(gb, turn)])
    if gb["hands"][offset + HIdx.O.value] >= 1 and gb["hands"][offset + HIdx.G.value] >= 1 and gb["hands"][
        offset + HIdx.W.value] >= 1:
        e_moves.append((Act.DEV_CARD,))

    # Check for playable dev cards
    if gb["hands"][offset + HIdx.PLAYED_DEV.value] == 0:  # haven't played a dev yet this turn
        # Check for dev cards not bought on this turn
        for i in range(5):
            if gb["hands"][offset + HIdx.PLAYABLE_DEV_MAP.value] & (1 << i):
                # road builder is only playable if player has not maxed out their roads
                if i != 2 or gb["hands"][offset + HIdx.RDS_BUILT.value] < MAX_ROADS:
                    e_moves.append((Act.PLAY_DEV, i + HIdx.KNIGHT.value))

    # Check ports and cards to determine bank trades:
    # port types: 0: brick, 1: grain, 2: lumber, 3: ore, 4: wool, 5: 3:1, 6: 4:1
    gen_trade_type = 5 if (gb["hands"][offset + HIdx.PORTS.value] & (1 << 5)) else 6  # See if player has 3:1 port
    for i in range(5):
        if gb["hands"][offset + i] >= (3 if gen_trade_type == 5 else 4):
            for j in range(5):
                if j != i and gb["bank"][j] >= 1:
                    # 4:1 or 3:1 trade possible (currently just 4:1)
                    # TODO: implement as multi-stage action, like dev cards
                    e_moves.append((Act.BANK_TRADE, i, (3 if gen_trade_type == 5 else 4), j))

    # TODO: HIdx.PORTS.value needs to be properly implemented & maintained elsewhere in code for this to be implemented
    # trade_types = []
    # gen_trade_possible = False
    # # Check all 2:1 ports
    # for i in range(5):
    #     if gb["hands"][offset + HIdx.PORTS.value] & (1 << i):  # Check for player's access to port
    #         if gb["hands"][offset + i] >= 2:
    #             trade_types.append(i)
    #     if gb["hands"][offset + i] >= (3 if gen_trade_type == 5 else 4):
    #         gen_trade_possible = True
    # if gen_trade_possible:
    #     trade_types.append(gen_trade_type)
    # if trade_types:
    #     gen_moves.append(Act.BANK_TRADE)

    return e_moves
