import copy
import math
import sys
from GameBoard import *
from constants import global_verbose


class Agent:
    """
    Base class for Catan agents
    """

    def __init__(self, pidx=0):
        self.pidx = pidx

    def choose_move(self, state, avail_moves):
        print("Agent.choose_move() not implemented")
        sys.exit(1)

    def __str__(self):
        return "Agent"


class HumanAgent(Agent):
    """
    Human agent for Catan; player input used to choose moves
    """
    def __init__(self, pidx=0):
        super().__init__(pidx)

    async def choose_move(self, gb, avail_moves):
        """Chooses action by waiting for human player input"""
        pass

    def __str__(self):
        return "Human"

class RandomAgent(Agent):
    """Random agent for Catan; chooses moves uniformly at random"""
    def __init__(self, pidx=0):
        super().__init__(pidx)

    def choose_move(self, gb, avail_moves):
        """Chooses action based on agent's policy"""
        return random.choice(avail_moves)

    def __str__(self):
        return "RandomAgent"

class GreedyRandomAgent(Agent):
    """
    Greedy random agent for Catan; chooses moves uniformly at random, but prefers moves that build cities/settlements
    """
    def __init__(self, pidx=0):
        super().__init__(pidx)

    def choose_move(self, gb, avail_moves):
        """Chooses action based on agent's policy"""
        # Find all possible moves that build a city
        city_moves = [move for move in avail_moves if move[0] == Act.CITY]
        settlement_moves = [move for move in avail_moves if move[0] == Act.SETTLEMENT]
        if len(city_moves) > 0:
            return random.choice(city_moves)
        elif len(settlement_moves) > 0:
            return random.choice(settlement_moves)
        return random.choice(avail_moves)
        # More arbitrary than random greedy, but works better in practice against random:
        # for move_idx, move in enumerate(avail_moves):
        #     if move[0] == Act.CITY:
        #         return move
        #     elif move[0] == Act.SETTLEMENT:
        #         return move
        # return random.choice(avail_moves)

    def __str__(self):
        return "GreedyRandomAgent"

class VPGreedyAgent(Agent):
    """
    Greedily chooses moves that maximize victory points
    """
    def __init__(self, pidx=0):
        super().__init__(pidx)

    def choose_move(self, gb, avail_moves):
        """Chooses action based on agent's policy"""
        max_vps = 0
        best_moves = []
        for move in avail_moves:
            next_state = generate_successor(gb, move)
            new_vps = next_state["hands"][self.pidx * HAND_OFFSET + HIdx.TRUE_VP.value]
            if new_vps > max_vps:
                max_vps, best_moves = new_vps, [move]
            elif new_vps == max_vps:
                best_moves.append(move)

        assert len(best_moves) > 0
        # Randomly choose between moves of equal VP value
        return random.choice(best_moves)

    def __str__(self):
        return "VPGreedyAgent"


class ExpectiminimaxAgent(Agent):
    """
    Expectiminimax agent for adversarial search of Catan game tree
    """

    def __init__(self, pidx=0, depth=2):
        super().__init__(pidx)
        self.depth = depth
        self.dice_vals = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6)]

    def evaluation(self, gb: dict, player_idx: int):
        """
        Evaluates the board state for the player.
        Maximizes for self (higher score is better, lower is better for opponents.
        """
        if game_over(gb):
            if get_winner(gb) == self.pidx:  # Win
                return 100000
            else:  # Loss
                return -100000
        score = 0
        offset = self.pidx * HAND_OFFSET
        score += gb["hands"][offset + HIdx.TRUE_VP.value]
        for i in range(gb["num_players"]):
            if i != self.pidx:
                score -= gb["hands"][i * HAND_OFFSET + HIdx.TRUE_VP.value]
        return score

    def choose_move(self, gb: dict, avail_moves):
        """Chooses action based on agent's policy"""
        assert not game_over(gb)
        choice_score, move_choice = self.expectimax(gb, 4, self.pidx)
        if global_verbose:
            print(f"EXPECTIMAX CHOICE SCORE: {choice_score} MOVE CHOICE: {move_choice}")
        return move_choice


    def expectimax(self, gb: dict, depth: int, player: int, chance: bool=False):
        """
        Runs version of minimax on the game state.
        All opponents minimize score and player maximizes score.
        :return: (score, move)  Internal calls only care about score, top level call cares about move
        """
        if depth == 0 or game_over(gb):
            return self.evaluation(gb, player), None

        assert player == gb["curr_turn"]
        # Player idx of -1 indicates chance node
        if chance:
            expected_score = 0
            for dice_sum in range(2, 12):
                # Manually generate next state
                next_state = copy.deepcopy(gb)
                # curr player is already set to next player at this point
                next_state["dice_sum"] = dice_sum
                next_state["dv1"], next_state["dv2"] = self.dice_vals[dice_sum - 2]
                roll_dice(next_state, self.dice_vals[dice_sum - 2][0], self.dice_vals[dice_sum - 2][1], False)
                eval, _ = self.expectimax(next_state, depth - 1, player, False)  # chance node always followed by non-chance
                expected_score += eval * DICE_SUM_PROBS[dice_sum]
            return expected_score, None
        if self.pidx == player:  # Our move; maximize
            best_score = -float("inf")
            best_move = None
            for move in find_moves(gb, player):
                next_state = generate_successor_dice_separate(gb, move)
                # Next state is chance node if we finished our turn (next turn is not ours)
                score, _ = self.expectimax(next_state, depth - 1, next_state["curr_turn"], next_state["curr_turn"] != player)
                if score > best_score:
                    best_score, best_move = score, move
            return best_score, best_move
        else:  # opponent move; minimize
            best_score = float("inf")
            best_move = None
            for move in find_moves(gb, player):
                next_state = generate_successor_dice_separate(gb, move)
                # Next state is chance node if they finished their turn (next turn is not theirs)
                score, _ = self.expectimax(next_state, depth - 1, next_state["curr_turn"], next_state["curr_turn"] != player)
                if score < best_score:
                    best_score, best_move = score, move
            return best_score, best_move

    def __str__(self):
        return "ExpectimaxAgent"
