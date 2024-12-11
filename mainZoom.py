import math
import random
from enum import Enum
from typing import List, Tuple

import pygame

import slider
from pattern_library import patterns
from supabasePatterns import getPatterns

pygame.init()
myfont = pygame.font.SysFont("monospace", 20)

RLE_PATTERNS = getPatterns()

# Enum for cell states
class CellState(Enum):
    ALIVE = 1
    DEAD = 0

# Class for each cell in the grid
class Cell:
    def __init__(self, x: int, y: int, state: CellState = CellState.DEAD, freezed: bool = False) -> None:
        self.x = x
        self.y = y
        self.state = state
        self.next_state = state  # Speichert nächsten Stand nachdem Regeln angewendet wurden
        self.time_not_changed = 0
        self.freezed = freezed

    def determine_next_state(self, neighbors: List['Cell']):
        """Determine the cell's next state based on Game of Life rules"""
        alive_neighbors = sum(1 for neighbor in neighbors if neighbor.state == CellState.ALIVE)

        if self.state == CellState.ALIVE:
            self.next_state = CellState.ALIVE if alive_neighbors in [2, 3] else CellState.DEAD
        else:
            self.next_state = CellState.ALIVE if alive_neighbors == 3 else CellState.DEAD

        '''Count, that a cell did not change'''
        if self.state == self.next_state:
            if not self.freezed:
                self.time_not_changed += 1
        else:
            self.time_not_changed = 0

    def update_state(self):
        """Update cell's state to its next state"""
        self.state = self.next_state


# Class for the grid of cells
class Grid:
    def __init__(self, width: int, height: int, cell_size: int) -> None:
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cells = [[Cell(x, y) for y in range(height)] for x in range(width)]
        self.stats = [0, 0, 0, 0]  # Alive, Dead, New Alive, New Dead


    def apply_rle_pattern(self, rle: str):
        """Wendet ein RLE-Pattern auf das Grid an."""
        rle_grid = Grid.parse_rle(rle, width=None, height=None)

        # Größe des RLE-Musters bestimmen
        pattern_width = len(rle_grid[0])
        pattern_height = len(rle_grid)
        #print(pattern_width, pattern_height)

        # Berechnung der Offsets für die Zentrierung
        offset_x = (self.width - pattern_width) // 2
        offset_y = (self.height - pattern_height) // 2
        
        # Zustände auf das Grid anwenden
        for x, row in enumerate(rle_grid):
            for y, value in enumerate(row):
                if 0 <= x + offset_x < self.width and 0 <= y + offset_y < self.height:
                    self.cells[x + offset_x][y + offset_y].state = (
                        CellState.ALIVE if value == 1 else CellState.DEAD
                    )
                    self.cells[x + offset_x][y + offset_y].time_not_changed = 0

    @staticmethod
    def parse_rle(rle, width=None, height=None):
        """Parst ein RLE-Pattern in ein 2D-Grid."""
        lines = rle.splitlines()
        header = [line for line in lines if line.startswith('#')]
        pattern = [line for line in lines if not line.startswith('#')]
        pattern = ''.join(pattern).replace('\n', '')

        # RLE dekodieren
        rows = []
        current_row = []
        count = ''
        for char in pattern:
            if char.isdigit():
                count += char  # Baue Ziffern zusammen
            elif char in 'bo':
                current_row.extend([1 if char == 'o' else 0] * (int(count) if count else 1))
                count = ''
            elif char == '$':
                rows.append(current_row)
                current_row = []
        rows.append(current_row)  # Letzte Zeile hinzufügen

        # Normalisieren: Sicherstellen, dass alle Zeilen gleich lang sind
        max_length = max(len(row) for row in rows)
        grid = [row + [0] * (max_length - len(row)) for row in rows]

        # Optional: Größe anpassen
        if width or height:
            target_width = width if width else len(grid[0])
            target_height = height if height else len(grid)
            padded_grid = [[0] * target_width for _ in range(target_height)]

            for i in range(min(target_height, len(grid))):
                for j in range(min(target_width, len(grid[i]))):
                    padded_grid[i][j] = grid[i][j]
            grid = padded_grid

        return grid

    def initialize_random(self):
        """Randomly initialize the grid with alive and dead cells."""
        for row in self.cells:
            for cell in row:
                cell.state = CellState.ALIVE if random.random() > 0.7 else CellState.DEAD # mehr DEAD Zellen (größere Wahrscheinlichkeit)
                cell.time_not_changed = 0
    
    def change_cell_state(self, x, y):
        cell = self.cells[x][y]
        if cell.state == CellState.ALIVE:
            cell.state = CellState.DEAD
        else:
            cell.state = CellState.ALIVE
    
    def initialize_manually(self):
        for row in self.cells:
            for cell in row:
                cell.state = CellState.DEAD

    def reset_field(self):
        for row in self.cells:
            for cell in row:
                cell.next_state = CellState.DEAD
                cell.time_not_changed = 0
                cell.update_state()

    def get_neighbors(self, cell: Cell) -> List[Cell]:
        """Return a list of neighboring cells for a given cell."""
        neighbors = []
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            nx, ny = cell.x + dx, cell.y + dy
            try:
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append(self.cells[nx][ny])
            except IndexError as e:
                pass

        return neighbors


    def update(self):
        """Apply Game of Life rules to each cell in the grid."""
        # Determine next state for each cell
        for row in self.cells:
            for cell in row:
                neighbors = self.get_neighbors(cell)
                cell.determine_next_state(neighbors)
        
        # Update state to the next state
        for row in self.cells:
            for cell in row:
                if not cell.freezed:
                    cell.update_state()

 

    def apply_lightning(self, pos_x: int, pos_y: int):
        for i, row in enumerate(self.cells):
            if math.sqrt(pow(i - pos_x, 2)) <= 10:
                for j, cell in enumerate(row):
                    if math.sqrt(pow(i - pos_x, 2) + pow(j - pos_y, 2)) <= 10:
                        cell.next_state = CellState.ALIVE if cell.state == CellState.DEAD else CellState.DEAD
                        cell.time_not_changed = 0
                        cell.update_state()
    
    def apply_freeze(self, pos_x: int, pos_y: int):
        for i, row in enumerate(self.cells):
            if math.sqrt(pow(i - pos_x, 2)) <= 10:
                for j, cell in enumerate(row):
                    if math.sqrt(pow(i - pos_x, 2) + pow(j - pos_y, 2)) <= 10:
                        cell.freezed = True

    def apply_unfreeze(self):
        for i, row in enumerate(self.cells):
            for j, cell in enumerate(row):
                cell.freezed = False
    
    def apply_earthquake(self):
        for row in self.cells:
            for cell in row:
                cell.next_state = CellState.ALIVE if cell.state == CellState.DEAD else CellState.DEAD
                cell.time_not_changed = 0
                cell.update_state()

    def get_stats(self):
        self.stats = [0, 0, 0, 0]
        for row in self.cells:
            for cell in row:
                if cell.state == CellState.ALIVE:
                    self.stats[0] += 1
                    if cell.time_not_changed == 0:
                        self.stats[2] += 1
                else:
                    self.stats[1] += 1
                    if cell.time_not_changed == 0:
                        self.stats[3] += 1

    def draw(self, screen):
        """Draw the grid of cells to the screen."""
        self.adjust_grid()
        self.stats = [0, 0, 0, 0]
        for row in self.cells:
            for cell in row:
                #1 color
                #color = (0, 255, 0) if cell.state == CellState.ALIVE else (0, 0, 0)
                #changing colors and calculating stats
                if cell.state == CellState.ALIVE:
                    if not cell.freezed:
                        r = max(255 - 2*cell.time_not_changed, 0)
                        g = min(cell.time_not_changed, 255)
                        b = max(255 - 0.5*cell.time_not_changed, 0)
                        color = (r, g, b)
                    elif cell.freezed:
                        r = int(max(255 - 2*cell.time_not_changed, 0)*0.8)
                        g = int(min(cell.time_not_changed, 255)*0.9)
                        b = int(max(255 - 0.5*cell.time_not_changed, 0) + (255 - max(255 - 0.5*cell.time_not_changed, 0))*0.2)
                        color = (r, g, b)
                    self.stats[0] += 1
                    if cell.time_not_changed == 0:
                        self.stats[2] += 1
                else:
                    if not cell.freezed:
                        r, g, b = max(255 - cell.time_not_changed, 0), max(255 - cell.time_not_changed, 0), max(255 - cell.time_not_changed, 0)
                        color = (r, g, b)
                    elif cell.freezed:
                        r = int(max(255 - cell.time_not_changed, 0)*0.8)
                        g = int(max(255 - cell.time_not_changed, 0)*0.9)
                        b = int(max(255 - cell.time_not_changed, 0) + (255 - max(255 - cell.time_not_changed, 0))*0.2)
                        color = (r, g, b)
                    self.stats[1] += 1
                    if cell.time_not_changed == 0:
                        self.stats[3] += 1
                pygame.draw.rect(screen, color, pygame.Rect(
                    cell.x * self.cell_size, cell.y * self.cell_size, self.cell_size, self.cell_size))
    
    def adjust_grid(self):
        old_num = len(self.cells)
        new_num = int(self.width)

        difference = new_num - old_num

        if difference < 0:
            diff_top = difference // 2
            diff_bottom = difference - diff_top

            diff_left = diff_top
            diff_right = diff_bottom

            new_cells = [[Cell(x, y) for y in range(new_num)] for x in range(new_num)]

            for row_index, row in enumerate(new_cells):
                for col_index, cell in enumerate(row):
                    if (diff_top-1 < row_index) and (row_index < new_num-diff_bottom-1) and (diff_left - 1 < col_index) and (col_index < new_num - diff_right-1):
                        # retrieve the cell of self.cells
                        old_cell = self.cells[row_index-diff_top][col_index-diff_left]
                        new_cells[row_index][col_index].state, new_cells[row_index][col_index].next_state, new_cells[row_index][col_index].freezed, new_cells[row_index][col_index].time_not_changed = old_cell.state, old_cell.next_state, old_cell.freezed, old_cell.time_not_changed

            self.cells = []
            self.cells.extend(new_cells)

        elif difference > 0:
            diff_top = difference // 2
            diff_bottom = difference - diff_top

            diff_left = diff_top
            diff_right = diff_bottom

            new_cells = [[Cell(x, y) for y in range(new_num)] for x in range(new_num)]

            for row_index, row in enumerate(self.cells):
                for col_index, cell in enumerate(row):
                    if (diff_top-1 < row_index) and (row_index < new_num-diff_bottom-1) and (diff_left - 1 < col_index) and (col_index < new_num - diff_right-1):
                        # retrieve the cell of self.cells
                        old_cell = self.cells[row_index-diff_top][col_index-diff_left]
                        new_cells[row_index][col_index].state, new_cells[row_index][col_index].next_state, new_cells[row_index][col_index].freezed, new_cells[row_index][col_index].time_not_changed = old_cell.state, old_cell.next_state, old_cell.freezed, old_cell.time_not_changed

            self.cells = []
            self.cells.extend(new_cells)


# Main Game of Life class to control the game flow
class GameOfLife:
    def __init__(self, width: int, height: int, cell_size: int):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = Grid(width, height, cell_size)
        self.generation = 0

    def initialize(self):
        """Initialize the grid with a random setup of alive and dead cells."""
        #self.grid.initialize_random()
        self.grid.initialize_manually()
    
    def initialize_automatically(self):
        """Initialize the grid with a random setup of alive and dead cells."""
        self.grid.initialize_random()

    def next_generation(self):
        """Advance the grid to the next generation."""
        self.grid.update()

    def apply_spell(self, key: int, pos_x: int = None, pos_y: int = None):
        if key == 0:
            self.grid.apply_lightning(pos_x, pos_y)
        elif key == 1:
            self.grid.apply_earthquake()
        elif key == 2:
            self.grid.apply_freeze(pos_x, pos_y)
        elif key == 3:
            self.grid.apply_unfreeze()


# Images
play_image = pygame.image.load('play.png') 
play_image = pygame.transform.scale(play_image, (140, 60)) 

reset_image = pygame.image.load("reset.png")
reset_image = pygame.transform.scale(reset_image, (130, 45))

random_image = pygame.image.load("random.png")
random_image = pygame.transform.scale(random_image, (130, 105))

#Buttons
red_button = pygame.Surface((140, 60))  # play button
red_button.blit(play_image, (0, -5))

blue_button = pygame.Surface((130, 105)) # random button
blue_button.blit(random_image, (0, -30))

green_button = pygame.Surface((130, 65)) # reset button
green_button.blit(reset_image, (0, 0))

stat_button = pygame.Surface((75, 50)) 
stat_button.fill((50, 50, 50))

stat_surface = pygame.Surface((400, 200)) 
stat_surface.fill((100, 100, 100))

legende_button_color = (50, 50, 50) 
legende_button_rect = pygame.Rect(1100, 0, 100, 50) 
legende_button_caption = myfont.render("Legende", 1, (255, 255, 255))

legende_surface_color = (100, 100, 100) 
legende_surface_rect = pygame.Rect(800, 0, 400, 560) 

# Setup der GUI
class GUI:
    def __init__(self): 
        FPS = 60
        cell_size = 12
        grid_width, grid_height = 100, 100  # Defines the grid size in terms of cells
        #grid_width, grid_height = 1200//cell_size, 1200//cell_size
        red_button_offset = (grid_width * cell_size/2-150, grid_height * cell_size+10)
        blue_button_offset = (grid_width * cell_size/2, grid_height * cell_size+10)
        green_button_offset = (grid_width * cell_size/2+150, grid_height * cell_size+10)
        label_count_offset = (grid_width * cell_size-200, grid_height * cell_size+10)
        label_fps_offset = (grid_width * cell_size-200, grid_height * cell_size+30)
        stat_label_1_offset = (70, 50)
        stat_label_2_offset = (70, 80)
        zoom_Slider_pos = (300, 1235)
        velocity_Slider_pos = (80, 1235)
        #stat_label_3_offset = (70, 110)
        #stat_label_4_offset = (70, 140)
        #screen = pygame.display.set_mode((grid_width * cell_size, grid_height * cell_size+100))
        screen = pygame.display.set_mode((1200,1300))
        pygame.display.set_caption("Conway's Game of Life")
        #manager = pygame_gui.UIManager((800, 600))
        clock = pygame.time.Clock()

        # Sliders (zoom and velocity)
        zoom_Slider = slider.Slider(zoom_Slider_pos[0], zoom_Slider_pos[1], 100, 5, min_value= 5, max_value=20, startValue=12)
        velocity_Slider = slider.Slider(velocity_Slider_pos[0], velocity_Slider_pos[1], 100, 5, min_value= 1, max_value=100, startValue=60)

        # Initialize game
        game = GameOfLife(grid_width, grid_height, cell_size)
        game.initialize()

        running = True
        started = False
        selected_pattern = None
        stats_opened = False
        legende_opened = False
        count = 0
        while running:
            screen.fill((0, 0, 0))

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                pos = pygame.mouse.get_pos()

                #Update Sliders
                mouse_pressed = pygame.mouse.get_pressed()[0]
                zoom_Slider.update(pos, mouse_pressed)
                velocity_Slider.update(pos, mouse_pressed)
                
                #Update velocity (FPS)
                FPS = int(velocity_Slider.get_value())
                cell_size = int(zoom_Slider.get_value())
                game.grid.cell_size = cell_size
                grid_width, grid_height = 1200//cell_size, 1200//cell_size
                game.grid.width, game.grid.height = grid_width, grid_height

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if red_button.get_rect(topleft=red_button_offset).collidepoint(pos):
                        started = not started
                    if not started and 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size):
                        pos_cell = [pos[0]//cell_size, pos[1]//cell_size]
                        cell = game.grid.cells[pos_cell[0]][pos_cell[1]]
                        if cell.state == CellState.ALIVE: cell.state = CellState.DEAD 
                        else: cell.state = CellState.ALIVE
                    if not started and blue_button.get_rect(topleft=blue_button_offset).collidepoint(pos):
                        game.initialize_automatically()
                        count = 0
                    if green_button.get_rect(topleft=green_button_offset).collidepoint(pos):
                        game.grid.reset_field()
                        count = 0
                        started = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        if 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size):
                            game.apply_spell(0, pos[0]/cell_size, pos[1]/cell_size)
                    if event.key == pygame.K_f:
                        if 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size):
                            game.apply_spell(2, pos[0]/cell_size, pos[1]/cell_size)
                    elif event.key == pygame.K_e:
                        game.apply_spell(1)
                    elif event.key == pygame.K_c:
                        game.grid.reset_field()
                        count = 0
                        started = False
                    elif event.key == pygame.K_u:
                        game.apply_spell(3)
                    elif event.key == pygame.K_UP:
                        if FPS < 95:
                            FPS += 5
                            velocity_Slider.change_value(FPS)
                    elif event.key == pygame.K_DOWN:
                        if FPS > 5:
                            FPS -= 5
                            velocity_Slider.change_value(FPS)
                    elif event.key == pygame.K_1:
                        selected_pattern = RLE_PATTERNS["glider"]
                    elif event.key == pygame.K_2:
                        selected_pattern = RLE_PATTERNS["blinker"]
                    elif event.key == pygame.K_3:
                        selected_pattern = RLE_PATTERNS["toad"]
                    elif event.key == pygame.K_4:
                        selected_pattern = RLE_PATTERNS["rats"]
                    elif event.key == pygame.K_5:
                        selected_pattern = RLE_PATTERNS["acorn"]
                    elif event.key == pygame.K_6:
                        selected_pattern = RLE_PATTERNS["gosper_glider_gun"]
                    elif event.key == pygame.K_7:
                        selected_pattern = RLE_PATTERNS["queen_bee_shuttle"]
                    elif event.key == pygame.K_8:
                        selected_pattern = RLE_PATTERNS["pulsar"]
                    elif event.key == pygame.K_9:
                        selected_pattern = RLE_PATTERNS["diehard"]
                    elif event.key == pygame.K_a:
                        selected_pattern = RLE_PATTERNS["r_pentomino"]
                    elif event.key == pygame.K_b:
                        selected_pattern = RLE_PATTERNS["ants"]

            # Update and draw
            if started:
                game.next_generation()
                count += 1

            if selected_pattern:
                game.grid.apply_rle_pattern(selected_pattern)
                selected_pattern = None

            game.grid.draw(screen) 
            zoom_Slider.draw(screen)
            velocity_Slider.draw(screen)

            stat_label_1 = myfont.render(f'Cells alive: {game.grid.stats[0]}', 1, (255,255,0))
            stat_label_2 = myfont.render(f'Cells dead: {game.grid.stats[1]}', 1, (255,255,0))
            stat_button_caption = myfont.render(f'Stats', 1, (255,255,255))

            legende_button_caption = myfont.render(f'Legende', 1, (255,255,255))

            random_button_caption = myfont.render(f'Random', 1, (255,255,255))
            zoom_slider_caption = myfont.render(f'Zoom:', 1, (255,255,255))
            velocity_Slider_caption = myfont.render(f'V:',1, (255,255,255))
            velocity_Slider_value = myfont.render(f'{FPS}', 1, (255,255,255))
            zoom_Slider_value = myfont.render(f'{cell_size}',1, (255,255,255))

            # Legende properties
            increase_fps_caption = myfont.render(f'Erhöhe V: Key Up', 1, (255, 255, 255))
            decrease_fps_caption = myfont.render(f'Vermindere V: Key Down', 1, (255, 255, 255))
            glider_pattern_caption = myfont.render(f'Glider: Key 1', 1, (255, 255, 255))
            blinker_pattern_caption = myfont.render(f'Blinker: Key 2', 1, (255, 255, 255))
            toad_pattern_caption = myfont.render(f'Toad: Key 3', 1, (255, 255, 255))
            rats_pattern_caption = myfont.render(f'Rats: Key 4', 1, (255, 255, 255))
            acorn_pattern_caption = myfont.render(f'Acorn: Key 5', 1, (255, 255, 255))
            gosper_glider_gun_caption = myfont.render(f'Gosper Glider Gun: Key 6', 1, (255, 255, 255))
            queen_bee_shuttle_caption = myfont.render(f'Queen Bee Shuttle: Key 7', 1, (255, 255, 255))
            pulsar_pattern_caption = myfont.render(f'Pulsar: Key 8', 1, (255, 255, 255))
            diehard_pattern_caption = myfont.render(f'Diehard: Key 9', 1, (255, 255, 255))
            pentomino_pattern_caption = myfont.render(f'Pentomino: Key a', 1, (255, 255, 255))
            ants_pattern_caption = myfont.render(f'Pentomino: Key b', 1, (255, 255, 255))
            reset_field_caption = myfont.render(f'Leeren: Key C', 1, (255, 255, 255))
            apply_spell_0_caption = myfont.render(f'Zauber 0: Key L', 1, (255, 255, 255))
            apply_spell_2_caption = myfont.render(f'Zauber 2: Key F', 1, (255, 255, 255))
            apply_spell_1_caption = myfont.render(f'Zauber 1: Key E', 1, (255, 255, 255))
            apply_spell_3_caption = myfont.render(f'Zauber 3: Key U', 1, (255, 255, 255)) 


            if (stat_button.get_rect().collidepoint(pos) and stats_opened == False) or (stat_surface.get_rect().collidepoint(pos) and stats_opened == True):
                stats_opened = True
                screen.blit(stat_surface, (0, 0))
                screen.blit(stat_label_1, stat_label_1_offset)
                screen.blit(stat_label_2, stat_label_2_offset)
                #screen.blit(stat_label_3, stat_label_3_offset)
                #screen.blit(stat_label_4, stat_label_4_offset)
            else: stats_opened = False

            if legende_button_rect.collidepoint(pos) and not legende_opened or legende_surface_rect.collidepoint(pos) and legende_opened == True:
                legende_opened = True
                pygame.draw.rect(screen, legende_surface_color, legende_surface_rect)
                screen.blit(increase_fps_caption, (810, 20))
                screen.blit(decrease_fps_caption, (810, 50))
                screen.blit(glider_pattern_caption, (810, 80))
                screen.blit(blinker_pattern_caption, (810, 110))
                screen.blit(toad_pattern_caption, (810, 140))
                screen.blit(rats_pattern_caption, (810, 170))
                screen.blit(acorn_pattern_caption, (810, 200))
                screen.blit(gosper_glider_gun_caption, (810, 230))
                screen.blit(queen_bee_shuttle_caption, (810, 260))
                screen.blit(pulsar_pattern_caption, (810, 290))
                screen.blit(diehard_pattern_caption, (810, 320))
                screen.blit(pentomino_pattern_caption, (810, 350))
                screen.blit(ants_pattern_caption, (810, 380))
                screen.blit(reset_field_caption, (810, 410))
                screen.blit(apply_spell_0_caption, (810, 440))
                screen.blit(apply_spell_2_caption, (810, 470))
                screen.blit(apply_spell_1_caption, (810, 500))
                screen.blit(apply_spell_3_caption, (810, 530))
            else:
                legende_opened = False


            # Buttons anzeigen
            for i, (name, rle) in enumerate(RLE_PATTERNS.items()):
                label = myfont.render(f"{i+1}: {name}", 1, (255, 255, 255))
                screen.blit(label, (grid_width * cell_size + 10, 30 * i + 10))
            
            screen.blit(red_button, red_button_offset) 
            screen.blit(blue_button, blue_button_offset) 
            screen.blit(green_button, green_button_offset)
            screen.blit(stat_button, (0, 0))
            screen.blit(stat_button_caption, (5,15))
            screen.blit(random_button_caption, (blue_button_offset[0]+23, blue_button_offset[1]+12))
            screen.blit(zoom_slider_caption, (zoom_Slider_pos[0]-65, zoom_Slider_pos[1]-10))
            screen.blit(velocity_Slider_caption, (velocity_Slider_pos[0]-40, velocity_Slider_pos[1]-10))
            screen.blit(velocity_Slider_value, (velocity_Slider_pos[0]+(velocity_Slider.width/2), velocity_Slider_pos[1]+20))
            screen.blit(zoom_Slider_value, (zoom_Slider_pos[0]+ (zoom_Slider.width/2), zoom_Slider_pos[1]+20))
            pygame.draw.rect(screen, legende_button_color, legende_button_rect)
            screen.blit(legende_button_caption, (1105, 15))


            label_count = myfont.render(f'Count: {count}', 1, (255,255,0))
            screen.blit(label_count, label_count_offset)
            label_fps = myfont.render(f'FPS: {FPS}', 1, (255,255,0))
            screen.blit(label_fps, label_fps_offset)
            pygame.display.update()
            #pygame.display.flip()
            clock.tick(FPS) 

        pygame.quit()

def main():
    gui = GUI()

# Run the game
if __name__ == "__main__":
    main()
