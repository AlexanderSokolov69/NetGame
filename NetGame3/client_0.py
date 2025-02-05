#!/usr/bin/env python3
# coding:utf-8
import os
import socket
import sys
import time
import json
import zlib
from random import choice
import pygame

from const import Const

DATA_WIND = Const.data['DATA_WIND']
SIZE_MUL = 2
l_text, h_text, step_text = 200, 100, 100


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class MainMenu:
    def __init__(self):
        self.image = pygame.transform.scale(load_image('fon.png'), size)
        font = pygame.font.Font(size=50)
        self.text_game = [font.render('Начать игру', True, 'darkred'),
                          font.render('Выход', True, 'darkred')]
        self.text_rect = []
        for surface in self.text_game:
            rect = surface.get_rect()
            rect = (rect[0] + l_text, rect[1] + h_text, rect[2], rect[3])
            self.text_rect.append(rect)
        # print(self.text_rect)

    def exec(self, scr: pygame.Surface):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    return True
            scr.fill('black')
            scr.blit(self.image, (0, 0))
            for i, surface in enumerate(self.text_game):
                scr.blit(surface, (l_text, h_text + i * step_text))
            pygame.display.flip()


pygame.init()
size = width, height = 1400, 800
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
# fps = 4
color = choice(['white', 'red', 'blue', 'green', 'yellow'])
rnd = ['left', 'right', 'up', 'down']
buff = ''
my_addr = '-.-.-.-'
sound_brake = pygame.mixer.Sound('data/break1.ogg')
sound_eat = pygame.mixer.Sound('data/eat.ogg')
sound_ataka = pygame.mixer.Sound('data/brake.ogg')


def play_sound(sound: str, addr=''):
    if addr != my_addr:
        return
    if 'break' in sound:
        sound_brake.play()
    elif 'eat' in sound:
        sound_eat.play()
    elif 'ataka' in sound:
        sound_ataka.play()


play_sound('eat')
game = True
menu = MainMenu()
convert_error = True
while game:
    game = menu.exec(screen)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.connect((Const.data['HOST'], Const.data['PORT']))
            my_addr = s.getsockname()[0]
            print(' ADDR:', my_addr)
            flag = game
            while flag:
                cmd = {'key': []}
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        flag = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        cmd['pos'] = event.pos
                keys = pygame.key.get_pressed()
                if any(keys):
                    if keys[pygame.K_LEFT]:
                        cmd['key'].append("left")
                    if keys[pygame.K_RIGHT]:
                        cmd['key'].append("right")
                    if keys[pygame.K_UP]:
                        cmd['key'].append("up")
                    if keys[pygame.K_DOWN]:
                        cmd['key'].append("down")
                st = json.dumps(cmd)
                try:
                    s.send(st.encode())
                except Exception as err:
                    print('Error of send:', err)

                try:
                    buff += zlib.decompress(s.recv(DATA_WIND)).decode()
                    # print(buff)
                except Exception as err:
                    print('Error of receive:', err)

                data = dict()
                while buff.find('%%%%%') >= 0:
                    pos = buff.find('%%%%%')
                    data = buff[5:pos]
                    buff = buff[pos + 5:]
                    convert_error = True
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        print('JSON convert error.', data)
                        convert_error = False
                        continue
                    except Exception as err:
                        print('==> ', err)
                        continue

                if convert_error:
                    winner = data.get('WINNER', '')
                    if winner:
                        print('Победитель:', winner)
                    pygame.display.set_caption(f"До конца раунда осталось: {data['TIMER']} секунд...")
                    screen.fill(pygame.Color((0, 50, 0)))
                    #
                    for addr, player in data.get('players', []).items():
                        # print(player)
                        sound = player.get('sound', '')
                        if sound:
                            play_sound(sound, addr)
                        body = player['body']
                        figure = player['figure']
                        len_body = len(body)
                        hero_length = player['length']
                        hero_life = player['life']
                        radius = player['radius']
                        # print(radius)
                        color_r, color_g, color_b = player['color']
                        dr_color = (255 - color_r) // len_body
                        dg_color = (255 - color_g) // len_body
                        db_color = (255 - color_b) // len_body
                        txt_pos = [0, 0]
                        contour = 0
                        for i, pos in enumerate(body):
                            _radius = radius
                            if i == 0:
                                txt_pos = pos
                                div = min(2, len(body))
                                color = (color_r // div, color_g // div, color_b // div)
                                radius -= 4
                            else:
                                color = (color_r + dr_color * i,
                                         color_g + dg_color * i,
                                         color_b + db_color * i)
                                radius = max(3, radius / 1.1)
                            if figure == 0:
                                pygame.draw.circle(screen, color, pos, _radius, contour)
                                contour = 2
                            elif figure == 1:
                                rect = pygame.Rect(pos[0] - _radius // 2, pos[1] - _radius // 2,
                                                   _radius, _radius)
                                pygame.draw.rect(screen, color, rect)
                        font = pygame.font.Font(size=25)
                        surf_1 = font.render(f"{hero_length}", False, 'lightblue')
                        surf_0 = font.render(f"{hero_life}", False, 'pink')
                        screen.blit(surf_0, (txt_pos[0], txt_pos[1] - 20))
                        screen.blit(surf_1, txt_pos)
                    pygame.display.flip()
                    # clock.tick(fps)
    except ConnectionResetError:
        print('Try reconnect')
        continue
    # except Exception as err:
    #     print('All errors: ', err)
pygame.quit()
sys.exit()
