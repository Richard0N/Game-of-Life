import pygame
import sys

class Slider:

    GRAY = (169, 169, 169)
    BLUE = (51, 153, 255)

    def __init__(self, x, y, width, height, min_value=0, max_value=100, startValue=50):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.value = startValue
        self.circle_radius = 10
        self.circle_x = x + ((startValue-min_value)/(max_value-min_value)) * width
        self.circle_y = y
        self.is_dragging = False

    def draw(self, screen):
        pygame.draw.line(screen, self.GRAY, (self.x, self.y), (self.x + self.width, self.y), self.height) # Slider zeichnen
        pygame.draw.circle(screen, self.BLUE, (self.circle_x, self.circle_y), self.circle_radius) # Kreis für den Slider auf die Benutzeroberfläche legen (auf die Linie)

    def update(self, mouse_pos, mouse_pressed):
        if mouse_pressed and self.is_hovering(mouse_pos):
            self.is_dragging = True # wenn die Maus auf dem Slider ist und gleichzeitig drückt
        if not mouse_pressed:
            self.is_dragging = False

        if self.is_dragging:
            new_x = mouse_pos[0] # Position der Maus
            if new_x < self.x:
                new_x = self.x
            if new_x > self.x + self.width:
                new_x = self.x + self.width
            self.circle_x = new_x
            
            self.value = self.min_value + (self.circle_x - self.x) / self.width * (self.max_value - self.min_value) # Wert basierend auf Mausposition berechnen
            self.circle_y = self.y  # Kreis behält y Koordinatee

    def is_hovering(self, mouse_pos):
        # gibt zurück, ob die Maus gerade auf dem Slider ist (muss zwischen x bzw. y und der drauf addierten Höhe bzw. Breite liegen)
        return self.x <= mouse_pos[0] <= self.x + self.width and self.y - self.height <= mouse_pos[1] <= self.y + self.height

    def get_value(self):
        return self.value # gibt Wert zurück
    
    def change_value(self, new_value):
        self.value = new_value # ändert Wert
        self.circle_x = self.x + ((self.value-self.min_value)/(self.max_value-self.min_value)) * self.width # Berechnet Position des Kreises auf dem Slider, sodass er verschoben wird
        # Die Funktion ist wichtig, da die Geschwindigkeit auch mit den Pfeiltasten gesteuert werden kann, sodass Update hierfür nicht aufgerufen wird, da die Mouse Position nicht zwingend auf dem Slider liegt
