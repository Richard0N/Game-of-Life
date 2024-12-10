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
        # Draw the slider line
        pygame.draw.line(screen, self.GRAY, (self.x, self.y), (self.x + self.width, self.y), self.height)
        # Draw the circle at the slider's value position
        pygame.draw.circle(screen, self.BLUE, (self.circle_x, self.circle_y), self.circle_radius)

    def update(self, mouse_pos, mouse_pressed):
        if mouse_pressed and self.is_hovering(mouse_pos):
            self.is_dragging = True
        if not mouse_pressed:
            self.is_dragging = False

        if self.is_dragging:
            # Update the circle position based on the mouse
            new_x = mouse_pos[0]
            if new_x < self.x:
                new_x = self.x
            if new_x > self.x + self.width:
                new_x = self.x + self.width
            self.circle_x = new_x
            # Calculate the value based on the circle position
            self.value = self.min_value + (self.circle_x - self.x) / self.width * (self.max_value - self.min_value)
            self.circle_y = self.y  # Keep the circle aligned vertically with the slider

    def is_hovering(self, mouse_pos):
        # Check if the mouse is hovering over the slider
        return self.x <= mouse_pos[0] <= self.x + self.width and self.y - self.height <= mouse_pos[1] <= self.y + self.height

    def get_value(self):
        return self.value
