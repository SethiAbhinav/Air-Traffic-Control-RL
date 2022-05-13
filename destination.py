import pygame
import random
import conf
from waypoint import *

class Destination(Waypoint):

    COLOR_DEST = (192, 192, 192)

    def __init__(self, location, text):
        self.location = location
        self.text = text
        font = pygame.font.Font(None, 20)
        self.font_img = font.render(text, True, Destination.COLOR_DEST)

    def draw(self, surface):
        pygame.draw.circle(surface, Destination.COLOR_DEST, self.location, 5, 0)
        surface.blit(self.font_img, (self.location[0] + 8, self.location[1] + 8))

    def clickedOn(self, clickpos):
        return False
		
    @staticmethod
    def generateGameDestinations(screen_w, screen_h):
        ret = []
        for x in range(0, conf.get()['game']['n_destinations']):
            randx = random.randint( 20, screen_w - 20 )
            randy = random.randint( 20, screen_h - 20 )
            dest = Destination((randx, randy), "D" + str(x))
            ret.append(dest)
        return ret
