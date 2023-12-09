import argparse
import asyncio
import copy

import websockets

import util
from Agents import RandomAgent, HumanAgent, ExpectiminimaxAgent, GreedyRandomAgent, GreedyVPAgent
from GameBoard import *
from util import *
from constants import global_verbose  # TODO: fix usage of global_verbose


global_verbose = False

def main():
    global global_verbose
    parser = argparse.ArgumentParser(description="Conquerors of Catan")

    # Optional arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    parser.add_argument('-n', '--nogui', action='store_true', help='Number of players', default=False)
    parser.add_argument('-p', '--players', type=str, help='N character string for N players', default="HGGG")
    parser.add_argument('-g', '--num-games', type=int, help='Number of games to run', default=1)
    # random seed option for reproducibility
    parser.add_argument('-s', '--seed', type=int, help='Random seed', default=0)
    parser.add_argument('-m', '--maxturns', type=int, help='Max turns per game', default=2000)

    # Saving & loading game files
    parser.add_argument('-l', '--loadstate', type=str, help='Load game state from file')
    parser.add_argument('-j', '--justlayout', type=str, help='Save game state to file')
    parser.add_argument('-w', '--writerecord', action='store_true', help='Record game state to file', default=False)
    parser.add_argument('-r', '--readrecord', type=str, help='Game file to replay')
    parser.add_argument('-a', '--autosteps', action='store_true', help='Automatically step through replay',
                        default=False)
    # parser.add_argument('-b', '--beginnerboard', action='store_true', help='Use beginner board layout', default=False)

    args = parser.parse_args()
    random.seed(args.seed)
    if len(args.players) < 2 or len(args.players) > 4:
        parser.exit(1, "Invalid number of players")
    if args.verbose:
        global_verbose = True
    if args.nogui:
        # TODO: implement non-gui loadstate
        # Run games with no GUI, therefore no human players
        run_games(args)
        return
    # Otherwise, run with GUI
    # if args.beginnerboard:
    #     global_verbose = True
    #     # game_board = generate_beginner_board(len(args.players))
    #     game_board = generate_new_board(len(args.players))
    if args.loadstate:
        # ex file: board_state_1701364167.json
        if global_verbose:
            print("Loading game state from file")
        try:
            game_board = load_state_from_json(args.loadstate)
        except Exception as e:
            print("Error loading file")
            print(e)
            return
    elif args.justlayout:
        # load json file, but only use tokens and hex layout; reinitialize everything else
        if global_verbose:
            print("Loading game state from file")
        try:
            game_board = load_state_from_json(args.justlayout, just_layout=True)
            # TODO: reconcile players string with board loaded from file
        except Exception as e:
            print("Error loading file")
            print(e)
            return
    else:
        if global_verbose:
            print("Generating new game state")
        game_board = generate_new_board(len(args.players))

    if args.readrecord:
        # Replay game from file
        print("Waiting for frontend to connect...")
        start_server = websockets.serve(lambda ws, path: replay_game(ws, path, args.readrecord, args.autosteps), "localhost", 8080)
        if global_verbose:
            print("server started")
        asyncio.get_event_loop().run_until_complete(start_server)
        if global_verbose:
            print("server running")
        asyncio.get_event_loop().run_forever()
        return

    # Normal case with GUI
    # args.num_games = 100
    # run_games(args)
    start_server = websockets.serve(lambda ws, path: websocket_server(ws, path, game_board, args.players), "localhost",
                                    8080)
    if global_verbose:
        print("server started")
    asyncio.get_event_loop().run_until_complete(start_server)
    if global_verbose:
        print("server running")
    asyncio.get_event_loop().run_forever()


async def send_update_to_frontend(websocket, board_state: dict):
    """Send message to frontend to update the board state"""
    # Send the current game state to the frontend via websockets
    brd_s = filter_dict(board_state)
    brd_s["type"] = "board_update"  # doesn't matter if we change just "type" or "message" field
    msg = json.dumps(brd_s)
    await websocket.send(msg)


async def send_init_board_to_frontend(websocket, board_state: dict):
    """Send message to frontend to initialize the board state for new game"""
    # Send the current game state to the frontend via websockets
    brd_s = filter_dict(board_state)
    brd_s["type"] = "new_board"  # doesn't matter if we change just "type" or "message" field
    msg = json.dumps(brd_s)
    await websocket.send(msg)


async def wait_for_human_player(websocket, gb):
    """Wait for the human player to make a move via websocket; parse response"""
    # Wait for the human player to make a move via websockets
    # You can use the websockets library to receive messages from the frontend
    await websocket.send(
        json.dumps({"type": "notif", "message": "human_turn", "game_cycle_status": gb["game_cycle_status"]}))

    loop = True
    while loop:
        loop = False
        # Wait for the response
        msg = await websocket.recv()
        msg_obj = json.loads(msg)
        if msg_obj["type"] == "action":
            print("received action from player", msg_obj)
            if msg_obj["action"] == "road_btn":
                return Act.ROAD, msg_obj["r"], msg_obj["c"]
            elif msg_obj["action"] == "settlement_btn":
                return Act.SETTLEMENT, msg_obj["r"], msg_obj["c"]
            elif msg_obj["action"] == "city_btn":
                return Act.CITY, msg_obj["r"], msg_obj["c"]
            elif msg_obj["action"] == "save_game_btn":
                # Saving game state to file
                saved_file = save_state_to_json(gb)
                await websocket.send(json.dumps({"type": "notif", "message": "saved_game", "filename": saved_file}))
                loop = True
            elif msg_obj["action"] == "robber_btn":
                # TODO: implement stealing from player at vertex "c" in given hex
                return Act.PLACE_ROBBER, msg_obj["r"], msg_obj["c"]
            elif msg_obj["action"] == "dev_card_btn":
                return (Act.DEV_CARD,)
            elif msg_obj["action"] == "reset_game_btn":
                # Resetting game state
                return (Act.RESET,)

            else:
                return (Act.END_TURN,)
    return (Act.END_TURN,)


def parse_players(players_str, human_interface=True):
    """Parse the players string into a list of agent class instances"""
    # Parse agents string
    agents = []
    for pidx, char in enumerate(players_str):
        if char == "H" and human_interface:
            agents.append(HumanAgent(pidx))
        elif char == "R":
            agents.append(RandomAgent(pidx))
        elif char == "G":
            agents.append(GreedyRandomAgent(pidx))
        elif char == "V":
            agents.append(GreedyVPAgent(pidx))
        elif char == "E":
            agents.append(ExpectiminimaxAgent(pidx))
        else:
            print("invalid player string")
            return []
    print(f"Agents: {agents}")
    return agents


def run_games(args):
    """
    Runs a number of games with the given arguments, and no GUI or human players.
    Outputs statistics and other information to stdout.
    :param args: command line arguments from argparse module
    """
    agents = parse_players(args.players, human_interface=False)
    agent_wins = [0] * (len(agents) + 1)
    num_turns = [0] * args.num_games
    num_actions = [0] * args.num_games
    opponent_losing_vps = [0] * (len(agents) + 1)
    total_player_vps = [0] * (len(agents) + 1)
    if len(agents) == 0:
        return
    for i in range(args.num_games):
        if args.loadstate:
            gb = load_state_from_json(args.loadstate)
        else:
            gb = generate_new_board(len(agents))
        if args.writerecord:
            # Make independent copy of gb
            gb_init = copy.deepcopy(gb)
            moves_history = []
        while not util.game_over(gb):
            available_moves = find_moves(gb, gb["curr_turn"])
            assert len(available_moves) > 0, "Empty avail moves list"
            act = agents[gb["curr_turn"]].choose_move(gb, available_moves)
            if global_verbose:
                print(f"P{gb['curr_turn']} turn (AI) taking action {act}")
            if act[0] == Act.END_TURN:
                num_turns[i] += 1
                if num_turns[i] > args.maxturns:
                    print(f"Game {i} turn {num_turns[i]} action {num_actions[i]}")
                    # DNF: Stalemate probably reached; too many turns without win
                    agent_wins[-1] += 1
                    for pidx in range(len(agents)):  # NOTE: /TODO: DNFs will inevitably lower average VPs
                        total_player_vps[pidx] += gb["hands"][pidx * HAND_OFFSET + HIdx.TRUE_VP.value]
                    opponent_losing_vps[-1] += sum([gb["hands"][pidx * HAND_OFFSET + HIdx.TRUE_VP.value] for pidx in range(len(agents))])
                    break
            num_actions[i] += 1
            take_move(gb, act)
            if args.writerecord:
                if act[0] == Act.END_TURN:
                    # Record dice roll associated with end of turn
                    moves_history.append((Act.END_TURN, gb["dv1"], gb["dv2"]))
                else:
                    moves_history.append(act)
        if args.writerecord:
            fp = save_game_to_json(gb_init, moves_history)
            if global_verbose:
                print(f"Game saved to file {fp}")
        win_pidx = get_winner(gb)
        agent_wins[win_pidx] += 1
        opponent_losing_vps[win_pidx] += sum([gb["hands"][pidx * HAND_OFFSET + HIdx.TRUE_VP.value] for pidx in range(len(agents)) if pidx != win_pidx])
        for pidx in range(len(agents)):
            total_player_vps[pidx] += gb["hands"][pidx * HAND_OFFSET + HIdx.TRUE_VP.value]
        print(
            f"Game {i} over; P{win_pidx} wins with {gb['hands'][win_pidx * HAND_OFFSET + HIdx.TRUE_VP.value]} VPs in {num_turns[i]} turns, {num_actions[i]} actions")
        if global_verbose:
            for pidx in range(len(agents)):
                if pidx != win_pidx:
                    print(f"P{pidx} VPs: {gb['hands'][pidx * HAND_OFFSET + HIdx.TRUE_VP.value]}")
    print(f"Ran {args.num_games} games")
    print("Game statistics:")
    print("Agent type\tPIdx\tWins\tWin %\tAvg. VPs\tAvg. Opp. VPs from Wins")
    for pidx in range(len(agents)):
        if args.players[pidx] == "H":
            agent_type = "Human"
        elif args.players[pidx] == "R":
            agent_type = "Random"
        elif args.players[pidx] == "G":
            agent_type = "GreedyRandom"
        elif args.players[pidx] == "E":
            agent_type = "Expectiminimax"
        elif args.players[pidx] == "V":
            agent_type = "GreedyVP"
        else:
            agent_type = "Unknown"
        agent_tabbing = "\t" if len(agent_type) > 7 else "\t\t"
        avg_opp_vps_on_wins = opponent_losing_vps[pidx] / agent_wins[pidx] if agent_wins[pidx] > 0 else 0
        print(f"{agent_type}{agent_tabbing}{pidx}\t{agent_wins[pidx]}\t{agent_wins[pidx] / args.num_games * 100:.1f}%\t{total_player_vps[pidx] / args.num_games:.2f}\t\t{avg_opp_vps_on_wins:.2f}")
    avg_vps_on_DNF_games = opponent_losing_vps[-1] / agent_wins[-1] if agent_wins[-1] > 0 else 0
    print(f"DNF \t\t-\t{agent_wins[-1]}\t{agent_wins[-1] / args.num_games * 100:.2f}%\t-\t\t{avg_vps_on_DNF_games}")
    print(f"Average turns per game: {sum(num_turns) / len(num_turns)}")
    print(f"Average actions per game: {sum(num_actions) / len(num_actions)}")
    print(f"Average actions per turn: {sum(num_actions) / sum(num_turns)}")
    print(f"Average turns per player: {sum(num_turns) / len(num_turns) / len(agents)}")

    # TODO: save statistics for each game


async def websocket_server(websocket, path, gb, players_str):
    """
    Main websocket server function; handles main game loop & communication with GUI.
    Allows for human players with GUI, or GUI display with no human players.
    :param websocket: websocket object
    :param path: unused path for websocket
    :param gb: initial game board state
    :param players_str: string representation of player types
    """
    agents = parse_players(players_str)
    if len(agents) == 0:
        return
    await send_init_board_to_frontend(websocket, gb)
    while not util.game_over(gb):
        # Perform game logic for the current turn
        if agents[gb["curr_turn"]].__class__.__name__ == "HumanAgent":
            print(f"P{gb['curr_turn']} turn (human)")
            act = await wait_for_human_player(websocket, gb)
            print(f"Human took action: {act}")
            if act[0] == Act.RESET:
                gb = generate_new_board()
                await send_init_board_to_frontend(websocket, gb)
                continue
            elif act_invalid(gb, act):
                print(f"Invalid action {act} by player {gb['curr_turn']}")
                await websocket.send(
                    json.dumps({"type": "notif", "message": "invalid_action", "pidx": gb["curr_turn"]}))
                continue
            # print("waiting for human player")
            # act = await agents[mgs["curr_turn"]].choose_move(mgs)
        else:
            print(f"P{gb['curr_turn']} turn (AI)")
            available_moves = find_moves(gb, gb["curr_turn"])
            act = agents[gb["curr_turn"]].choose_move(gb, available_moves)
            await asyncio.sleep(0.01)
            print(f"AI took action: {act}")
            # DEBUG
            all_res = 0
            for pidx in range(len(agents)):
                all_res += sum(gb["hands"][pidx * HAND_OFFSET: pidx * HAND_OFFSET + 5])
            assert all_res + sum(gb["bank"][0:5]) == 95
        take_move(gb, act)

        await send_update_to_frontend(websocket, gb)

    # Game over
    await websocket.send(json.dumps({"type": "notif", "message": "game_over", "pidx": gb["curr_turn"]}))
    print(f"Game over; P{get_winner(gb)} wins")


async def replay_game(websocket, path, fname, auto_steps=True):
    """
    Replay a game from file, using the GUI to display the game.
    :param websocket: websocket object
    :param path: unused path for websocket
    :param fname: filename of game state to replay
    :param auto_steps: whether to automatically replay game, or use human interface to step through
    """
    print("Starting game replay")
    gb, moves_history = load_game_from_json(fname)
    await send_init_board_to_frontend(websocket, gb)
    act_num = 0
    while len(moves_history) > 0:
        # Player steps game forward by hitting "End Turn" every time
        await websocket.send(json.dumps({"type": "notif", "message": "step_game_replay"}))

        while not auto_steps:
            # Wait for the response
            msg = await websocket.recv()
            msg_obj = json.loads(msg)
            if msg_obj["type"] == "action" and msg_obj["action"] == "end_turn_btn":
                break
            else:
                print("Invalid action during game replay")
                await websocket.send(
                    json.dumps({"type": "notif", "message": "invalid_act_during_replay", "pidx": gb["curr_turn"]}))
        if auto_steps:
            await asyncio.sleep(0.5)  # simply wait half a second between actions

        curr_move = moves_history.pop(0)
        if global_verbose:
            print("Current hands:")
            for pidx in range(gb["num_players"]):
                for i in range(5):
                    offset = pidx * HAND_OFFSET + i * 5
                    print(f"P{pidx} Hand {i}: {gb['hands'][offset: offset + 5]}")
            print(f"Next move options: {find_moves(gb, gb['curr_turn'])}")
            print(f"NEXT: Act{act_num} P{gb['curr_turn']} turn (replay): {curr_move}")
        take_move(gb, curr_move)
        act_num += 1
        await send_update_to_frontend(websocket, gb)

    # Game over
    await websocket.send(json.dumps({"type": "notif", "message": "game_over", "pidx": gb["curr_turn"]}))


if __name__ == "__main__":
    main()
