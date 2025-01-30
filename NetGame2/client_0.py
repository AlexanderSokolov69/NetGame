#!/usr/bin/env python3
# coding:utf-8
import socket
import sys
import time
import json
from random import choice
import pygame


# HOST = "172.16.1.42"  # The server's hostname or IP address
HOST = "localhost"  # The server's hostname or IP address
PORT = 5058  # The port used by the server
DATA_WIND = 8192
SIZE_MUL = 2

pygame.init()
size = width, height = 1400, 800
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
fps = 10
color = choice(['white', 'red', 'blue', 'green', 'yellow'])
rnd = ['left', 'right', 'up', 'down']
buff = ''

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((HOST, PORT))
            print(s.getpeername())
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                keys = pygame.key.get_pressed()
                cmd = {'key': []}
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
                        cmd['d_rad'] = 20
                # if len(cmd['key']) < 1:
                #     cmd['key'].append(choice(rnd))
                st = json.dumps(cmd)
                try:
                    s.send(st.encode())
                except Exception as err:
                    print('Error of send:', err)

                try:
                    buff += s.recv(DATA_WIND).decode()
                    # print(buff)
                except Exception as err:
                    print('Error of receive:', err)

                while buff.find('%%%%%') >= 0:
                    pos = buff.find('%%%%%')
                    data = buff[5:pos]
                    buff = buff[pos + 5:]
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        print('JSON convert error.', data)
                        continue
                    except Exception as err:
                        print('==> ', err)
                        continue
                screen.fill('lightgreen')
                #
                for key, player in data.get('players', []).items():
                    body = player['body']
                    figure = player['figure']
                    len_body = len(body)
                    hero_length = player['length']
                    hero_life = player['life']
                    radius = player['radius'] + len_body // SIZE_MUL
                    color_r, color_g, color_b = player['color']
                    dr_color = (255 - color_r) // len_body
                    dg_color = (255 - color_g) // len_body
                    db_color = (255 - color_b) // len_body
                    txt_pos = [0, 0]
                    for i, pos in enumerate(body):
                        _radius = radius
                        if i == 0:
                            txt_pos = pos
                            color = (color_r // 2, color_g // 2, color_b // 2)
                            radius -= player['radius']
                        else:
                            color = (color_r + dr_color * i,
                                     color_g + dg_color * i,
                                     color_b + db_color * i)
                            radius = max(3, radius / 1.05)
                        if figure == 0:
                            pygame.draw.circle(screen, color, pos, _radius)
                        elif figure == 1:
                            rect = pygame.Rect(pos[0] - _radius // 2, pos[1] - _radius // 2,
                                               _radius, _radius)
                            pygame.draw.rect(screen, color, rect)
                    font = pygame.font.Font(size=25)
                    surf_1 = font.render(f"{hero_length}", False, 'lightblue', 'black')
                    surf_0 = font.render(f"{hero_life}", False, 'pink', 'black')
                    screen.blit(surf_0, (txt_pos[0], txt_pos[1] - 20))
                    screen.blit(surf_1, txt_pos)
                pygame.display.flip()
                # clock.tick(fps)
    except ConnectionResetError:
        print('Try reconnect')
        continue
    except Exception as err:
        print('All errors: ', err)
