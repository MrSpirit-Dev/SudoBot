from dokusan import generators, solvers
from renderer import sudoku_to_grid


DIFFICULTIES = {
    "Easy": 75,
    "Medium": 150,
    "Hard": 300,
}


class SudokuGame:
    def __init__(
        self,
        puzzle,
        solution,
        difficulty,
        board,
        solution_board,
        started_by
    ):
        self.puzzle = puzzle
        self.solution = solution

        self.difficulty = difficulty
        self.started_by = started_by

        self.board = board
        self.solution_board = solution_board

        self.original_board = [
            row.copy()
            for row in board
        ]

    def to_dict(self):
        return {
            "difficulty": self.difficulty,
            "started_by": self.started_by,
            "board": self.board,
            "solution_board": self.solution_board,
            "original_board": self.original_board
        }

    @classmethod
    def from_dict(cls, data):

        game = cls.__new__(cls)

        game.puzzle = None
        game.solution = None

        game.difficulty = data["difficulty"]
        game.started_by = data["started_by"]

        game.board = data["board"]
        game.solution_board = data["solution_board"]
        game.original_board = data["original_board"]

        return game


def create_sudoku(
    avg_rank: int,
    difficulty: str,
    started_by: str
):

    puzzle = generators.random_sudoku(avg_rank)
    solution = solvers.backtrack(puzzle)

    board = sudoku_to_grid(puzzle)
    solution_board = sudoku_to_grid(solution)

    return SudokuGame(
        puzzle,
        solution,
        difficulty,
        board,
        solution_board,
        started_by
    )