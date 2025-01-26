#!/usr/bin/env python3
# coding:utf-8
import socket
import sys
import time
import json
from random import choice
import pygame


HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 5056  # The port used by the server

pygame.init()
size = width, height = 800, 600
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
fps = 1
color = choice(['white', 'red', 'blue', 'green', 'yellow'])
rnd = ['left', 'right', 'up', 'down']

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((HOST, PORT))
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                keys = pygame.key.get_pressed()
                cmd = {'key': [], 'step': 2}
                if any(keys):
                    if keys[pygame.K_LEFT]:
                        cmd['key'].append("left")
                    if keys[pygame.K_RIGHT]:
                        cmd['key'].append("right")
                    if keys[pygame.K_UP]:
                        cmd['key'].append("up")
                    if keys[pygame.K_DOWN]:
                        cmd['key'].append("down")
                    if keys[pygame.K_SPACE]:
                        cmd['d_rad'] = 1
                    if keys[pygame.K_BACKSPACE]:
                        cmd['d_rad'] = -1
                if len(cmd['key']) < 1:
                    cmd['key'].append(choice(rnd))
                st = json.dumps(cmd)
                try:
                    s.sendall(st.encode())
                    data = s.recv(1024).decode()
                    data = json.loads(data)
                    # print(data)
                except json.JSONDecodeError:
                    print('Data send error.', 'json.JSONDecodeError')
                    break
                except Exception as err:
                    print('==> ', err)
                    break
                screen.fill('black')
                #
                for key, player in data.get('players', []).items():
                    pos = player['pos']
                    radius = player['radius']
                    pygame.draw.circle(screen, color, pos, radius)
                #
                pygame.display.flip()
                # clock.tick(fps)
    except ConnectionResetError:
        print('Try reconnect')
        continue
    except Exception as err:
        print('All errors: ', err)
