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
                        b = int(max(255 - 0.5*cell.time_not_changed, 0) + (255 - max(255 - 0.5*cell.time_not_changed, 0))*0.2) # time_not changed ändert sich nicht, daher auch keine Änderung der Farben bei Freeze
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
        FPS = 60 # Variable, die die Geschwindigkeit speichert (gemessen in FPS)
        cell_size = 12 # speichert die Größe der quadratischen Zelle
        grid_width, grid_height = 100, 100  # bestimmt Anzahl der Zeilen und Spalten im Feld
        
        red_button_offset = (grid_width * cell_size/2-150, grid_height * cell_size+10) # offset vom play Button
        blue_button_offset = (grid_width * cell_size/2, grid_height * cell_size+10) # offset vom random Button
        green_button_offset = (grid_width * cell_size/2+150, grid_height * cell_size+10) # offset vom reset Button
        label_count_offset = (grid_width * cell_size-200, grid_height * cell_size+10) # offset für count Label unten rechts
        label_fps_offset = (grid_width * cell_size-200, grid_height * cell_size+30) # offset für FPS Label unten rechts
        stat_label_1_offset = (70, 50) # offset Stat Label 1 oben links
        stat_label_2_offset = (70, 80) # offset Stat Label 2 oben links
        zoom_Slider_pos = (300, 1235) # Position des Zoom Sliders
        velocity_Slider_pos = (80, 1235) # Position des Geschwindigkeitssliders
        
        screen = pygame.display.set_mode((1200,1300)) # Screen wird initialisiert
        pygame.display.set_caption("Conway's Game of Life") # Titel für den Screen
        
        clock = pygame.time.Clock() # Initialisierung der clock

        # Sliders 
        zoom_Slider = slider.Slider(zoom_Slider_pos[0], zoom_Slider_pos[1], 100, 5, min_value= 5, max_value=20, startValue=12) # Initialisierung des ZoomSliders
        velocity_Slider = slider.Slider(velocity_Slider_pos[0], velocity_Slider_pos[1], 100, 5, min_value= 1, max_value=100, startValue=60) #Initialisierung des Geschwindigkeitssliders

        game = GameOfLife(grid_width, grid_height, cell_size) # Initialisierung des Spiels (durch Objekt der GameOfLife Klasse)
        game.initialize() # Spielfeld initialisieren durch Aufruf der initialize Funktion der GameOfLife Klasse

        running = True # ob das Programm läuft oder nicht
        started = False # ob der Ablauf der Zellen gestarted wurde (durch den Play Button)
        selected_pattern = None # speichert ausgewähltes Muster
        stats_opened = False # gibt an, ob der Nutzer das Stats-Fenster oben in der linken Ecke geöffnet hat
        legende_opened = False # gibt an, ob der Nutzer das Legende-Fenster oben in der rechten Ecke geöffnet hat
        count = 0 # Anzahl der durchlaufenen Frames
        while running: #läuft nur solange running auf True ist, das Programm laufen soll
            screen.fill((0, 0, 0)) # Hintergrund (schwarz)

            # Events
            for event in pygame.event.get(): # iteriert durch alle Events, die derzeit in der Event-Liste sind
                if event.type == pygame.QUIT:
                    running = False # Falls das Programm geschlossen wird, soll es nicht mehr weiterlaufen

                pos = pygame.mouse.get_pos() # speichert die aktuelle Position der Maus

                #Slider aktualisieren
                mouse_pressed = pygame.mouse.get_pressed()[0] # 0 steht für linke Maustaste, gibt True oder False für gedrückt zurück
                zoom_Slider.update(pos, mouse_pressed) # zoom Slider aktualisieren
                velocity_Slider.update(pos, mouse_pressed) # Geschwindigkeitsslider aktualisieren
                
                # Geschwindigkeit und Zoom implementieren/ändern
                FPS = int(velocity_Slider.value) # FPS Wert vom Slider nehmen

                cell_size = int(zoom_Slider.value) # Größe der Zelle vom Slider nehmen (Slider gibt Größe der Zelle an)
                game.grid.cell_size = cell_size # die Zellengröße im Grid verändern
                grid_width, grid_height = 1200//cell_size, 1200//cell_size # die Anzahl an Spalten und Zeilen neu berechnen
                game.grid.width, game.grid.height = grid_width, grid_height # Die Anzahl an Spalten und Zeilen den Attributen

                if event.type == pygame.MOUSEBUTTONDOWN: # Wenn Maus geklickt wird
                    if red_button.get_rect(topleft=red_button_offset).collidepoint(pos): # Play button 
                        started = not started # bestimmt, ob gestartet wird
                    if not started and 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size): # schaut, ob auf ein Kästchen geklickt wird
                        pos_cell = [pos[0]//cell_size, pos[1]//cell_size] # Zelle herausfinden
                        cell = game.grid.cells[pos_cell[0]][pos_cell[1]] # Zelle aus Grid holen
                        if cell.state == CellState.ALIVE: cell.state = CellState.DEAD # Zellenstatus verändern
                        else: cell.state = CellState.ALIVE
                    if not started and blue_button.get_rect(topleft=blue_button_offset).collidepoint(pos): # schauen, ob random button gedrück wird
                        game.initialize_automatically() # zufälliges grid initialisieren
                        count = 0 # count zurückgesetzt
                    if green_button.get_rect(topleft=green_button_offset).collidepoint(pos): # schauen, ob reset gedrück wird
                        game.grid.reset_field() # Feld zurücksetzen
                        count = 0 # count zurücksetzen
                        started = False # Generationsfortsetzung/Ablauf stoppen
                if event.type == pygame.KEYDOWN: # Wenn eine Taste gedrückt wird
                    if event.key == pygame.K_l: # l wird gedrückt, Lightning Zauber aktiviert
                        if 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size): # schaut, ob Maus im gegebenen Fenser liegt
                            game.apply_spell(0, pos[0]/cell_size, pos[1]/cell_size) # gibt berechnet Spalte und Zeile zum Zauber
                    if event.key == pygame.K_f: # f wird gedrückt (freeze)
                        if 0<=pos[0]<=(grid_width * cell_size) and 0<=pos[1]<=(grid_height * cell_size):
                            game.apply_spell(2, pos[0]/cell_size, pos[1]/cell_size)
                    elif event.key == pygame.K_e: # wenn e gedrückt wird (earthquake)
                        game.apply_spell(1)
                    elif event.key == pygame.K_c: # wenn c gedrückt wird 
                        game.grid.reset_field() # Feld zurücksetzen
                        count = 0
                        started = False
                    elif event.key == pygame.K_u: # wenn u gedrückt wird, unfreeze
                        game.apply_spell(3) # unfreeze Spell über apply_spell in Game Of Life aufgerufen
                    elif event.key == pygame.K_UP: # Pfeiltaste nach oben gedrückt
                        if FPS < 95: # Begrenzung
                            FPS += 5 # FPS um 5 erhöht
                            velocity_Slider.change_value(FPS) # Wert auf dem Slider ändern
                    elif event.key == pygame.K_DOWN: # Wenn Pfeiltaste nach unten gedrückt wird
                        if FPS > 5: # Begrenzung
                            FPS -= 5 # FPS verringern
                            velocity_Slider.change_value(FPS) # Slider ändern
                    elif event.key == pygame.K_1: # Wenn Zahl gedrückt wird (hier: 1)
                        selected_pattern = RLE_PATTERNS["glider"] # Vorgefertigtes Pattern in Variable speichern
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

            
            if started:
                game.next_generation() # Wenn Ablauf gestartet wurde, nächste Generation starten
                count += 1 # nächsten Frame addieren

            if selected_pattern:
                game.grid.apply_rle_pattern(selected_pattern) # wenn das ausgewählte Muster existiert, das RLE Pattern anwenden
                selected_pattern = None # pattern zurücksetzen

            game.grid.draw(screen)  # Grid auf den Screen packen
            zoom_Slider.draw(screen) # zoom slider auf den Screen
            velocity_Slider.draw(screen) # Geschwindigkeitsslider auf den Screen

            stat_label_1 = myfont.render(f'Cells alive: {game.grid.stats[0]}', 1, (255,255,0)) # stat labels Initialisierung
            stat_label_2 = myfont.render(f'Cells dead: {game.grid.stats[1]}', 1, (255,255,0)) 
            stat_button_caption = myfont.render(f'Stats', 1, (255,255,255)) # Stat button caption

            legende_button_caption = myfont.render(f'Legende', 1, (255,255,255)) #Legende button caption

            random_button_caption = myfont.render(f'Random', 1, (255,255,255)) # random button caption
            zoom_slider_caption = myfont.render(f'Zoom:', 1, (255,255,255)) # zoom slider captino
            velocity_Slider_caption = myfont.render(f'V:',1, (255,255,255)) # Geschwindigkeitsslider caption
            velocity_Slider_value = myfont.render(f'{FPS}', 1, (255,255,255)) # Geschwinidigkeitsslider Wert Label
            zoom_Slider_value = myfont.render(f'{cell_size}',1, (255,255,255)) # Geschwindigkeitsslider Wert Label

            # Legende Attribute (alles Labels mit Position und antialias = 1 --> glattere Kanten)
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
            ants_pattern_caption = myfont.render(f'Ants: Key b', 1, (255, 255, 255))
            reset_field_caption = myfont.render(f'Leeren: Key C', 1, (255, 255, 255))
            apply_spell_0_caption = myfont.render(f'Lightning: Key L', 1, (255, 255, 255))
            apply_spell_2_caption = myfont.render(f'Freeze: Key F', 1, (255, 255, 255))
            apply_spell_1_caption = myfont.render(f'Earthquake: Key E', 1, (255, 255, 255))
            apply_spell_3_caption = myfont.render(f'Unfreeze: Key U', 1, (255, 255, 255)) 

            # Wenn die Maus über den Stat Button geht
            if (stat_button.get_rect().collidepoint(pos) and stats_opened == False) or (stat_surface.get_rect().collidepoint(pos) and stats_opened == True):
                stats_opened = True
                # Die Stat Label auf den Screen bringen
                screen.blit(stat_surface, (0, 0))
                screen.blit(stat_label_1, stat_label_1_offset)
                screen.blit(stat_label_2, stat_label_2_offset)
            else: stats_opened = False

            if legende_button_rect.collidepoint(pos) and not legende_opened or legende_surface_rect.collidepoint(pos) and legende_opened == True:
                legende_opened = True
                pygame.draw.rect(screen, legende_surface_color, legende_surface_rect) # Das Rechteck der expandierten Legende auf den Screen bringen
                # Legenden Labels auf den Screen bringen, solange die Legende expandiert ist
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
            
            # Die variablen-unabhängigen Elemente auf den Screen bringen (Buttons, Captions, sliders, legende etc.)
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


            label_count = myfont.render(f'Count: {count}', 1, (255,255,0)) # Label unten rechts (count)
            screen.blit(label_count, label_count_offset) # Count Label auf den Screen bringen

            label_fps = myfont.render(f'FPS: {FPS}', 1, (255,255,0)) # FPS Label unten rechts
            screen.blit(label_fps, label_fps_offset) # FPS Label auf den Screen bringen

            pygame.display.update() # den Screen aktualisieren, sodass alle Änderungen angezeigt werden
            
            clock.tick(FPS) # Pro Sekunde laufen FPS Frames ab

        pygame.quit() # Programm stoppen, wenn es durch den Nutzer beendet wurde

def main():
    gui = GUI() # Objekt von der GUI Klasse initialisieren

# Run the game
if __name__ == "__main__":
    main()
