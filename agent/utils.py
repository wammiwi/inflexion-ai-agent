# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part A: Single Player Infexion
from queue import PriorityQueue
import random

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir


def apply_ansi(str, bold=True, color=None):
    """
    Wraps a string with ANSI control codes to enable basic terminal-based
    formatting on that string. Note: Not all terminals will be compatible!

    Arguments:

    str -- String to apply ANSI control codes to
    bold -- True if you want the text to be rendered bold
    color -- Colour of the text. Currently only red/"r" and blue/"b" are
        supported, but this can easily be extended if desired...

    """
    bold_code = "\033[1m" if bold else ""
    color_code = ""
    if color == "r":
        color_code = "\033[31m"
    if color == "b":
        color_code = "\033[34m"
    return f"{bold_code}{color_code}{str}\033[0m"


def render_board(board: dict[tuple, tuple], ansi=False) -> str:
    """
    Visualise the Infexion hex board via a multiline ASCII string.
    The layout corresponds to the axial coordinate system as described in the
    game specification document.

    Example:

        >>> board = {
        ...     (5, 6): ("r", 2),
        ...     (1, 0): ("b", 2),
        ...     (1, 1): ("b", 1),
        ...     (3, 2): ("b", 1),
        ...     (1, 3): ("b", 3),
        ... }
        >>> print_board(board, ansi=False)

                                ..
                            ..      ..
                        ..      ..      ..
                    ..      ..      ..      ..
                ..      ..      ..      ..      ..
            b2      ..      b1      ..      ..      ..
        ..      b1      ..      ..      ..      ..      ..
            ..      ..      ..      ..      ..      r2
                ..      b3      ..      ..      ..
                    ..      ..      ..      ..
                        ..      ..      ..
                            ..      ..
                                ..
    """
    dim = 7
    output = ""
    for row in range(dim * 2 - 1):
        output += "    " * abs((dim - 1) - row)
        for col in range(dim - abs(row - (dim - 1))):
            # Map row, col to r, q
            r = max((dim - 1) - row, 0) + col
            q = max(row - (dim - 1), 0) + col
            if (r, q) in board:
                color, power = board[(r, q)]
                text = f"{color}{power}".center(4)
                if ansi:
                    output += apply_ansi(text, color=color, bold=False)
                else:
                    output += text
            else:
                output += " .. "
            output += "    "
        output += "\n"
    return output

    """
    generate a list containing neighboring (firendly) cells
    """


def get_neighbors(coord: tuple):
    directions = [(0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)]
    neighbors = list()
    for direction in directions:
        neighbors.append((determine_next_cell(coord, direction)))
    return neighbors

    """
    spawn a cell adjacent to neighboring (friendly) cells
    """


def spawn(board: dict[tuple, tuple], coord: tuple, player: str, enemy, game_state):
    if coord in board:
        all_neighbors = list()
        all_cells = coord_list(board, coord)

        for cell in all_cells:
            neighbors = (get_neighbors(cell))
            all_neighbors.extend(neighbors)

        neighbors = list(set(all_neighbors))

        enemy_cood_list = coord_list(board, enemy)
        enemy_cood_list.append(coord)
        for neighbor in neighbors:
            if (neighbor in board) and \
                    (board[neighbor][0] != player) and \
                    (neighbor not in enemy_cood_list):
                coord = neighbor
                break
        else:
            while coord in board:
                coord = (random.randint(0, 6), random.randint(0, 6))
    board[coord] = (player, 1)
    return SpawnAction(HexPos(coord[0], coord[1]))

    """
    decide which move egenerate the best eval value and playu it
    """


def make_move(board: dict[tuple, tuple], player: str, enemy, game_state):
    total_power = count_power(board)

    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('-inf')

    moves = generate_moves(board, player)

    for move in moves:
        if (total_power >= 47):
            if (move[0] == "SPAWN"):
                continue
        temp_board = make_board(board, move, player).copy()
        value = mini_max(temp_board, 3, True, player, enemy, game_state, alpha, beta)

        if (value > best_value):
            best_value = value
            best_move = move
        alpha = max(alpha, best_value)

    if best_move[0] == "SPAWN":
        return spawn(board, best_move[1], player, enemy, game_state)

    elif best_move[0] == "SPREAD":
        return simple_spread(board, (best_move[1][0], best_move[1][1]), HexDir((best_move[1][2], best_move[1][3])))

    """
    simple helper function for spreading into the board
    """


def simple_spread(board: dict[tuple, tuple], playerCell, direction):
    return SpreadAction(HexPos(playerCell[0], playerCell[1]), HexDir(direction))

    """
    generate a list of (firendly) cells
    """


def coord_list(board, player):
    result_list = list()

    for cell in board.keys():
        if board[cell][0] == player:
            result_list.append(cell)
    return result_list

    """
    generate a list of (firendly) cells
    """


def determine_next_cell(current_cell: tuple, direction: tuple):
    # hex directions: (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)

    current_x = current_cell[0]
    current_y = current_cell[1]

    next_x = current_x + direction[0]
    next_y = current_y + direction[1]

    # check if the coordinates wrap around the board
    if next_x > 6:
        next_x -= 7
    elif next_x < 0:
        next_x += 7
    if next_y > 6:
        next_y -= 7
    elif next_y < 0:
        next_y += 7

    return (next_x, next_y)

    """
    make a spread move
    """


def spread(board: dict[tuple, tuple], action: tuple, colour):
    cell = (action[0], action[1])
    direction = (action[2], action[3])
    if cell in board:
        power = board[cell][1]
        current_cell = cell

        # iterate through the cells that are to be covered, and check for blue cells
        for i in range(power):
            next_cell = determine_next_cell(current_cell, direction)
            if next_cell in board:
                next_power = board[next_cell][1]
                # if cell to spread to has power of 6, empty cell
                if next_power == 6:
                    board.pop(next_cell)
                # if blue cell -> capture, if red cell -> update cells to reflect board state
                else:
                    board[next_cell] = (colour, next_power + 1)
            else:
                board[next_cell] = (colour, 1)
            current_cell = next_cell
        # update cell -> empty it
        board.pop(cell)
    return board

    """
    count total power on the board
    """


def count_power(board: dict[tuple, tuple]):
    total_power = 0
    values = list(board.values())
    for index, tuple in enumerate(values):
        total_power += values[index][1]
    return total_power

    """
    count total power on the board (cell)
    """


def count_color_power(board: dict[tuple, tuple], color):
    total_power = 0
    values = list(board.values())
    for index, tuple in enumerate(values):
        if values[index][0] == color:
            total_power += values[index][1]
    return total_power

    """
    minimax implementation with alpha-beta pruning
    """


def mini_max(board: dict[tuple, tuple], depth, max_player, player, enemy, game_state, alpha, beta):
    # base case (game over)
    if (depth == 0) or (game_over(player, enemy, game_state)):
        return evaluate_state(board, player, enemy)

    # current player is to be maximised
    if max_player == True:
        max_eval = float('-inf')

        # general moves to make on the board
        # two types, Spawn or spread (they need to be identified)
        # actions can be a list of tuples, where spawn and spread moves are distinguished
        moves = generate_moves(board, player)

        # get best three moves
        for move in moves:
            temp_board = make_board(board, move, player).copy()
            max_eval = max(max_eval, mini_max(temp_board, depth - 1, True, player, enemy, game_state, alpha, beta))
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break

        return max_eval

    else:
        min_eval = float('inf')
        moves = generate_moves(board, enemy)

        for move in moves:
            temp_board = make_board(board, move, enemy).copy()
            min_eval = min(min_eval, mini_max(temp_board, depth - 1, False, player, enemy, game_state, alpha, beta))
            beta = min(beta, min_eval)
            if beta <= alpha:
                break

        return min_eval

    """
    generate a tempory board
    """


def make_board(board, move, player):
    temp_board = board.copy()
    if move[0] == "SPAWN":
        temp_board[move[1]] = (player, 1)
    elif move[0] == "SPREAD":
        temp_board = spread(temp_board, move[1], player)
    return temp_board

    """
    determin of the end game state has been reached
    """


def game_over(player, enemy, game_state):
    if (game_state._round >= 343) or \
            (count_color_power(game_state.board, player) == 0) or \
            (count_color_power(game_state.board, enemy) == 0):
        return True
    else:
        return False

    """
    generate a value to the given state
    """


def evaluate_state(board: dict[tuple, tuple], player: str, enemy: str) -> int:
    # The below Evaluation function is completely made up!!!!!!

    # Weights for evaluation components
    power_weight = 0.5
    cell_dominance_weight = 0.5
    Mobility_weight = 1
    vulnerability_weight = -1

    # calculate some board metrics

    # Power Eval
    player_power = count_color_power(board, player)
    enemy_power = count_color_power(board, enemy)
    power_eval = power_weight * (player_power - enemy_power)

    # Board Dominance Eval
    player_cells = len(coord_list(board, player))
    enemy_cells = len(coord_list(board, enemy))
    empty_cells = len(get_spawn_options(board))

    player_dom = (player_cells / (player_cells + enemy_cells + empty_cells))
    enemy_dom = (enemy_cells / (player_cells + enemy_cells + empty_cells))
    dominance_eval = (cell_dominance_weight * (player_dom + enemy_dom)) * 10

    # Mobility Eval
    mobility_eval = (Mobility_weight * (calculate_spread_enemy_cells(board, player, enemy)))
    vulnerability_eval = (vulnerability_weight * (calculate_spread_enemy_cells(board, enemy, player)))

    # calculate score / give an evaluation
    evaluation = (power_eval + dominance_eval + mobility_eval + vulnerability_eval)
    return evaluation

    """
    generate a count of enemy cells which can be spread upon
    """
def calculate_spread_enemy_cells(board: dict[tuple, tuple], player: str, enemy: str) -> dict[tuple, int]:
    directions = [(0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)]
    enemy_count = 0
    # iterate over each player cell on the board
    for player_cell in board:
        if board[player_cell][0] == player:
            # check each direction for potential spread to enemy cells
            for d in directions:
                current_cell = player_cell
                power = board[current_cell][1]
                distance = 0
                spread = True

                # keep spreading until you find your own cell (distance is incorporated)
                while spread:
                    adjacent_cell = determine_next_cell(current_cell, d)
                    if adjacent_cell in board:
                        if board[adjacent_cell][0] == enemy:
                            if distance <= power:
                                enemy_count += 1
                            spread = False
                        elif board[adjacent_cell][0] == player:
                            # stop spreading if a player cell is met
                            spread = False
                        else:
                            distance += 1
                            if distance > power:
                                spread = False
                    else:
                        spread = False
                    current_cell = adjacent_cell
    return enemy_count

    """
    generate a list of possible moves to make on the board
    """


def generate_moves(board: dict[tuple, tuple], player: str) -> list:
    moves = list()
    # generate moves for spawning a new piece
    # get a list of empty cells which can be spawned on
    empty_cells = get_spawn_options(board)
    for cell in empty_cells:
        moves.append(("SPAWN", (cell[0], cell[1])))

    # generate moves for spreading existing pieces
    player_cells = coord_list(board, player)
    for cell in player_cells:
        directions = [(0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)]
        for direction in directions:
            moves.append(("SPREAD", (cell[0], cell[1], direction[0], direction[1])))
    return moves

    """
    generate a list of possible places to spawn on
    """


def get_spawn_options(board: dict[tuple, tuple]) -> list:
    # get a list of all empty cells which can be spawned on
    empty_cells = list()
    occupied_cells = set(board.keys())
    for row in range(7):
        for col in range(7):
            cell = (row, col)
            if cell not in occupied_cells:
                empty_cells.append(cell)
    return empty_cells