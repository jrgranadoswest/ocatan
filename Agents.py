import copy
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


class HumanAgent(Agent):
    """
    Human agent for Catan; player input used to choose moves
    """
    def __init__(self, pidx=0):
        super().__init__(pidx)

    async def choose_move(self, gb, avail_moves):
        """Chooses action by waiting for human player input"""
        pass


class RandomAgent(Agent):
    """Random agent for Catan; chooses moves uniformly at random"""
    def __init__(self, pidx=0):
        super().__init__(pidx)

    def choose_move(self, gb, avail_moves):
        """Chooses action based on agent's policy"""
        return random.choice(avail_moves)


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


class GreedyVPAgent(Agent):
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


# class ExpectiminimaxAgent(Agent):
#     """
#     Expectiminimax agent for adversarial search of Catan game tree
#     """
# 
#     def __init__(self, pidx=0, depth=2):
#         super().__init__(pidx)
#         self.depth = depth
#         self.dice_vals = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6)]
# 
#     def evaluation(self, gb: dict, player_idx: int):
#         """
#         Evaluates the board state for the player.
#         Maximizes for self (higher score is better, lower is better for opponents.
#         """
#         if game_over(gb):
#             if get_winner(gb) == self.pidx:  # Win
#                 return float("inf")
#             else:  # Loss
#                 return -float("inf")
#         score = 0
#         offset = self.pidx * HAND_OFFSET
#         score += gb["hands"][offset + HIdx.TRUE_VP.value]
#         for i in range(gb["num_players"]):
#             if i != self.pidx:
#                 score -= gb["hands"][i * HAND_OFFSET + HIdx.TRUE_VP.value]
#         return score

