import socket
import pygame
import random
import time


class PlayerNode:
    def __init__(self, address, port):
        self.leader_address = address
        self.leader_port = port

        self.WINDOW_WIDTH = 400
        self.WINDOW_HEIGHT = 400
        self.BLOCK_SIZE = 50
        self.x = self.WINDOW_WIDTH // 2 - self.BLOCK_SIZE // 2
        self.y = self.WINDOW_HEIGHT // 2 - self.BLOCK_SIZE // 2

        self.speed = 5
        self.socket = None

    def reset_state(self):
        self.x = 0
        self.y = 0

    def draw(self, window):
        pygame.draw.rect(window, (0, 0, 255), self.block)

    def move(self, movement):
        self.x += movement[0] * self.speed
        self.y += movement[1] * self.speed

    def run_game(self):
        pygame.init()
        window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Movable Square Block with Bouncing Circle")
        clock = pygame.time.Clock()
        self.draw(window)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_state()

            movement = [0, 0]
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                movement[0] -= 1
            if keys[pygame.K_RIGHT]:
                movement[0] += 1
            if keys[pygame.K_UP]:
                movement[1] -= 1
            if keys[pygame.K_DOWN]:
                movement[1] += 1

            window.fill((255, 255, 255))
            self.move(movement)
            self.draw(window)
            pygame.display.flip()
            clock.tick(60)


class NPCNode:
    def __init__(self, leader_address, leader_port):
        self.leader_address = leader_address
        self.leader_port = leader_port
        self.x = 0
        self.y = 0
        self.WINDOW_WIDTH = 400
        self.WINDOW_HEIGHT = 400
        self.BLOCK_SIZE = 50
        self.x = self.WINDOW_WIDTH // 2 - self.BLOCK_SIZE // 2
        self.y = self.WINDOW_HEIGHT // 2 - self.BLOCK_SIZE // 2

        self.speed = 5
        self.npc_speed = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.socket = None
        # self.block = pygame.Rect(self.x, self.y, self.BLOCK_SIZE, self.BLOCK_SIZE)

    def share_state(self):

        self.send_message(f'{{"type":"state","x":{self.x},"y":{self.y}}}')

    def reset_state(self):
        self.x = 0
        self.y = 0

    def update_block(self):
        self.x += self.npc_speed[0]
        self.y += self.npc_speed[1]

        if self.x <= 0 or self.x >= self.WINDOW_WIDTH - self.BLOCK_SIZE:
            self.npc_speed[0] = -self.npc_speed[0]

        if self.y <= 0 or self.y >= self.WINDOW_HEIGHT - self.BLOCK_SIZE:
            self.npc_speed[1] = -self.npc_speed[1]

    def move_in_square(self):
        running = True
        while running:
            self.update_block()
            time.sleep(0.5)
