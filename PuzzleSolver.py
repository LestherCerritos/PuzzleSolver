import sys
import pygame
import random
from queue import PriorityQueue
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog

# Constants
WIDTH, HEIGHT = 600, 600  # Dimensions of the game window
GRID_SIZE = 3             # Size of the puzzle grid (3x3)
TILE_SIZE = WIDTH // GRID_SIZE  # Size of each tile
WHITE = (255, 255, 255)   # Color for the blank tile
BLACK = (0, 0, 0)         # Background color
BLANK_TILE = -1           # Placeholder for the blank tile


# GUI Class for the Puzzle Game
class PuzzleGameGUI(QWidget):
    """GUI for uploading an image and starting the puzzle game."""
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.init_ui()

    def init_ui(self):
        """Initialize the GUI layout."""
        self.setWindowTitle("8-Puzzle Game")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        # Instructions label
        self.label = QLabel("Select an image to start the puzzle game.")
        layout.addWidget(self.label)

        # Button to upload an image
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)

        # Button to start the game (enabled after image upload)
        self.start_button = QPushButton("Start Game")
        self.start_button.clicked.connect(self.start_game)
        self.start_button.setEnabled(False)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def upload_image(self):
        """Open a file dialog to upload an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select an Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.image_path = file_path
            self.label.setText(f"Selected Image: {file_path.split('/')[-1]}")
            self.start_button.setEnabled(True)
        else:
            self.label.setText("No image selected. Please upload an image.")

    def start_game(self):
        """Start the puzzle game if an image is uploaded."""
        if self.image_path:
            self.close()
            run_puzzle_game(self.image_path)


# Puzzle Logic
def split_image(image_path):
    """
    Split the uploaded image into tiles for the puzzle.
    :param image_path: Path to the uploaded image.
    :return: A list of image tiles and a numbered representation.
    """
    image = pygame.image.load(image_path)
    image = pygame.transform.scale(image, (WIDTH, HEIGHT))
    tiles = [
        image.subsurface(pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)).copy()
        for i in range(GRID_SIZE)
        for j in range(GRID_SIZE)
    ]
    tiles[-1] = None  # The last tile is blank
    numbered_tiles = list(range(1, GRID_SIZE * GRID_SIZE)) + [BLANK_TILE]
    return tiles, numbered_tiles


def is_solvable(tiles):
    """
    Check if the puzzle is solvable.
    :param tiles: The numbered tile representation.
    :return: True if the puzzle is solvable, False otherwise.
    """
    indices = [tile for tile in tiles if tile != BLANK_TILE]
    inversions = sum(
        1 for i in range(len(indices)) for j in range(i + 1, len(indices)) if indices[i] > indices[j]
    )
    return inversions % 2 == 0


def shuffle_tiles(numbered_tiles):
    """
    Shuffle the tiles until the puzzle is solvable.
    :param numbered_tiles: The numbered tile representation.
    """
    while True:
        random.shuffle(numbered_tiles)
        if is_solvable(numbered_tiles):
            break


def draw_tiles(screen, image_tiles, numbered_tiles):
    """
    Draw the tiles on the game window.
    :param screen: The Pygame screen surface.
    :param image_tiles: List of image tiles.
    :param numbered_tiles: The numbered tile representation.
    """
    for i, number in enumerate(numbered_tiles):
        x, y = (i % GRID_SIZE) * TILE_SIZE, (i // GRID_SIZE) * TILE_SIZE
        if number != BLANK_TILE:
            screen.blit(image_tiles[number - 1], (x, y))
        else:
            pygame.draw.rect(screen, WHITE, pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))


# A* Solver
def manhattan_distance(state, goal):
    """
    Calculate the Manhattan distance as the heuristic for A*.
    :param state: Current puzzle state.
    :param goal: Goal puzzle state.
    :return: The total Manhattan distance.
    """
    return sum(
        abs(goal.index(tile) % GRID_SIZE - i % GRID_SIZE) +
        abs(goal.index(tile) // GRID_SIZE - i // GRID_SIZE)
        for i, tile in enumerate(state) if tile != BLANK_TILE
    )


def a_star_solver(initial, goal):
    """
    Solve the 8-puzzle using the A* algorithm.
    :param initial: The initial puzzle state.
    :param goal: The goal puzzle state.
    :return: A list of states representing the solution path.
    """
    open_set = PriorityQueue()
    open_set.put((0, tuple(initial)))
    came_from = {}
    g_score = {tuple(initial): 0}
    f_score = {tuple(initial): manhattan_distance(initial, goal)}

    while not open_set.empty():
        _, current = open_set.get()
        if list(current) == goal:
            # Reconstruct the path from goal to start
            path = []
            while current in came_from:
                path.append(list(current))
                current = came_from[current]
            return path[::-1]

        blank_idx = current.index(BLANK_TILE)
        row, col = divmod(blank_idx, GRID_SIZE)

        # Generate valid neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                neighbor = list(current)
                swap_idx = nr * GRID_SIZE + nc
                neighbor[blank_idx], neighbor[swap_idx] = neighbor[swap_idx], neighbor[blank_idx]
                neighbor_tuple = tuple(neighbor)

                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor_tuple, float('inf')):
                    came_from[neighbor_tuple] = current
                    g_score[neighbor_tuple] = tentative_g_score
                    f_score[neighbor_tuple] = tentative_g_score + manhattan_distance(neighbor, goal)
                    open_set.put((f_score[neighbor_tuple], neighbor_tuple))
    return []


# Main Game Logic
def run_puzzle_game(image_path):
    """
    Run the puzzle game.
    :param image_path: Path to the uploaded image.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("8-Puzzle Game")
    clock = pygame.time.Clock()

    # Initialize the puzzle
    image_tiles, numbered_tiles = split_image(image_path)
    goal = numbered_tiles[:]
    shuffle_tiles(numbered_tiles)

    # Solve the puzzle
    solution = a_star_solver(numbered_tiles, goal)
    step = 0

    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Animate the solution step by step
        if step < len(solution):
            numbered_tiles = solution[step]
            step += 1

        screen.fill(BLACK)
        draw_tiles(screen, image_tiles, numbered_tiles)
        pygame.display.flip()
        clock.tick(1)  # Adjust speed of animation

    pygame.quit()


# Main Entry Point
def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    gui = PuzzleGameGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
