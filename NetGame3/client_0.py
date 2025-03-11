#!/usr/bin/env python3
# coding:utf-8
import gc
import math
import os
# import random
import socket
import sys
# import time
import json
import zlib
from random import choice

import msgpack
import pygame

from cl_color import Color, load_image
from const import Const


with open('config.json') as f:
    data = json.load(f)
    print(data)
    s_port = data.get('PORT')
    s_host = data.get('HOST')
    if s_port:
        Const.data['PORT'] = int(s_port)
    if s_host:
        Const.data['HOST'] = s_host
    FULLSCREEN = data.get("FULLSCREEN", 0)
    width = data.get("WIDTH", 1600)
    height = data.get("HEIGHT", 900)

DATA_WIND = Const.data['DATA_WIND']
SIZE_MUL = 2
l_text, h_text, step_text = 200, 200, 70
background = (0, 50, 0)
time_color = (10, 80, 10)
pygame.init()
size = width, height

if FULLSCREEN:
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
else:
    screen = pygame.display.set_mode(size, pygame.HWSURFACE | pygame.DOUBLEBUF)
clock = pygame.time.Clock()
pygame.display.set_caption(f'ЗМЕИНЫЕ ГОНКИ. {Const.VERSION} (клиент)')


class MainMenu:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)
        self.user_name = self.local_ip
        self.sound = pygame.mixer.Sound('data/menu_click.ogg')
        self.image = pygame.transform.scale(load_image('fon.png'), size)
        self.image_cobra = pygame.transform.scale(load_image('cobra.png'), (600, 500))
        self.font = pygame.font.Font(size=50)
        self.font_title = pygame.font.Font('data/Capsmall.ttf', size=70)
        self.title = self.font_title.render('ЗМЕИНЫЕ ГОНКИ', True, 'yellow')
        self.text_game = [(self.font.render('Начать игру', True, 'darkred'),
                           self.font.render('Начать игру', True, 'orange')),
                          (self.font.render('Выход', True, 'darkred'),
                           self.font.render('Выход', True, 'orange'))]
        self.text_rect = []
        for i, surface in enumerate(self.text_game):
            rect = surface[0].get_rect()
            rect = rect.move(l_text, h_text + i * step_text)
            self.text_rect.append(rect)
        # print(self.text_rect)
        self.snake = [[width // 2, height // 2 + 70] for _ in range(60)]
        self.radius = 20
        self.step = 6
        self.pos = [self.step, 0]
        self.color = Color().color

    def check_user_name(self):
        if not self.user_name:
            self.user_name = self.local_ip

    def exec(self, scr: pygame.Surface):
        mouse_pos = 0, 0
        click = False
        m_clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click = True
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_name = self.user_name[:-1]
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.pos = [-self.step, 0]
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.pos = [self.step, 0]
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.pos = [0, -self.step]
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.pos = [0, self.step]
                    if event.key == pygame.K_SPACE:
                        self.color = Color().color
                    if event.key == pygame.K_RETURN:
                        return True
                    else:
                        try:
                            sym = chr(event.key)
                            if 'a' <= sym <= 'z' or sym in '1234567890-=/.':
                                self.user_name = f"{self.user_name}{sym}"[:20].capitalize()
                        except:
                            pass

            scr.fill('black')
            scr.blit(self.image, (0, 0))
            self.draw_snake(scr)
            scr.blit(self.image_cobra, (width - 650, height - 600))
            lx = width // 2 - self.title.get_rect().width // 2
            scr.blit(self.title, (lx, 50))
            for i, (surface, rect) in enumerate(zip(self.text_game, self.text_rect)):
                if rect.collidepoint(mouse_pos):
                    k = 1
                    if click:
                        self.sound.play()
                        return i == 0
                else:
                    k = 0
                scr.blit(surface[k], rect)
            click = False
            text = self.font.render(f"Компьютер: {self.hostname} | IP адрес: {self.local_ip}",
                                    True, 'gray')
            scr.blit(text, (width // 2 - text.get_rect().width // 2, height - 50))
            surf_user_name = self.font.render(f"NikName: {self.user_name}", True, 'black')
            scr.blit(surf_user_name, (610, 150))
            pygame.display.flip()
            m_clock.tick(60)

    def draw_snake(self, scr: pygame.Surface):
        segment = (self.snake[0][0] + self.pos[0]) % width, (self.snake[0][1] + self.pos[1]) % height
        radius = self.radius
        color = self.color
        cont = 0
        for i in range(len(self.snake)):
            if i % 3 == 0:
                pygame.draw.circle(scr, color, self.snake[i], radius, cont)
            if i == 0:
                pygame.draw.circle(scr, 'lightgreen', self.snake[i], radius - 10, cont)
            radius = max(8, radius // 1.04)
            color = (min(255, color[0] + 4),
                     min(255, color[1] + 4),
                     min(255, color[2] + 4))
            self.snake[i], segment = segment, self.snake[i]
            cont = 4


class Camera:
    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._center_x = width // 2
        self._center_y = height // 2
        self._queue = []
        self.q_len = 30
        self._window = 0

    def move(self, new_x, new_y):
        if self._x - new_x > self._window:
            self._x = new_x + self._window
        elif new_x - self._x > self._window:
            self._x = new_x - self._window
        if self._y - new_y > self._window:
            self._y = new_y + self._window
        elif new_y - self._y > self._window:
            self._y = new_y - self._window
        # self._queue.append((new_x, new_y))
        # if len(self._queue) < self.q_len:
        #     self._x, self._y = self._queue[0]
        # else:
        #     self._x, self._y = self._queue.pop(0)

    def pos(self):
        return self._x, self._y

    def shift(self, pos):
        x = pos[0] - self._x + self._center_x
        if x > width:
            x -= Const.WIDTH
        elif x < 0:
            x += Const.WIDTH
        y = pos[1] - self._y + self._center_y
        if y > height:
            y -= Const.HEIGHT
        elif y < 0:
            y += Const.HEIGHT
        return x, y


class ScrSprite(pygame.sprite.Sprite):
    def __init__(self, surf: pygame.Surface, pos: tuple[int, int], *args):
        super().__init__(*args)
        self.image = surf
        rect = self.image.get_rect()
        self.rect = rect.move(*pos)


# color = choice(['white', 'red', 'blue', 'green', 'yellow', 'black'])
# rnd = ['left', 'right', 'up', 'down']
buff = b''
my_addr = '-.-.-.-'
sound_brake = pygame.mixer.Sound('data/break1.ogg')
sound_eat = pygame.mixer.Sound('data/eat.ogg')
sound_ataka = pygame.mixer.Sound('data/brake.ogg')

font_win = pygame.font.Font('data/Capsmall.ttf', 50)
font_time = pygame.font.Font('data/Capsmall.ttf', 80)
img_list = [load_image('snake.png'), load_image('snake2.png'),
            load_image('snake3.png'), load_image('snake4.png'),
            load_image('snake5.png')]
font = pygame.font.Font('data/Capsmall.ttf', size=20)


class SnakeHead:
    def __init__(self):
        self._history = dict()
        self._cache = dict()
        snake_head = img_list[3]
        snake_head2 = pygame.transform.flip(snake_head, True, False)
        snake_head_2 = img_list[4]
        snake_head2_2 = pygame.transform.flip(snake_head_2, True, False)
        self._img = {'right': snake_head,
                     'left': snake_head2,
                     'down': pygame.transform.rotate(snake_head2, -90),
                     'up': pygame.transform.rotate(snake_head2, 90),
                     'stop': img_list[0]}
        self._img2 = {'right': snake_head_2,
                     'left': snake_head2_2,
                     'down': pygame.transform.rotate(snake_head2_2, -90),
                     'up': pygame.transform.rotate(snake_head2_2, 90),
                     'stop': img_list[0]}

    def get_head(self, body, pos, radius, addr):
        # radius = min(100, radius)
        if len(body) <= 1:
            _state = 'stop'
        else:
            dx = body[0][0] - body[1][0]
            dy = body[0][1] - body[1][1]
            if dx > 0:
                _state = 'right'
            elif dx < 0:
                _state = 'left'
            elif dy > 0:
                _state = 'up'
            else:
                _state = 'down'
        a_state, a_count = self._history.get(addr, ['right', 0])
        if a_state == _state:
            self._history[addr] = (a_state, 0)
        else:
            self._history[addr] = (a_state, a_count + 1)
        if a_count + 1 > 10:
            self._history[addr] = (_state, 0)
            a_state = _state
        _shift_x, _shift_y = -(radius // 2), radius
        if a_state == 'left':
            _shift_x = radius * 2
        elif a_state == 'down':
            _shift_y = radius
            _shift_x = radius * 2
        elif a_state == 'up':
            _shift_y = 0
            _shift_x = -(radius // 2)
        _img = self.cache_img(a_state, radius)
        _rect = _img.get_rect().move(pos[0] - radius, pos[1] - radius)
        return _img, _rect, _shift_x, _shift_y

    def cache_img(self, a_state, radius):
        img = self._cache.get((a_state, radius))
        if img:
            return img
        else:
            if radius < 80:
                img = pygame.transform.scale(self._img[a_state], (radius * 2, radius * 2)).convert_alpha()
            else:
                img = pygame.transform.scale(self._img2[a_state], (radius * 2, radius * 2)).convert_alpha()
            self._cache[(a_state, radius)] = img
        return img


class Head(pygame.sprite.Sprite):
    def __init__(self, image, rect, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = image
        self.rect = rect


def play_sound(sound: str, addr=''):
    if addr != my_addr:
        return
    try:
        if 'break' in sound:
            sound_brake.play()
        elif 'eat' in sound:
            sound_eat.play()
        elif 'ataka' in sound:
            sound_ataka.play()
    except:
        pass


def delta_pos(pos0: list[int, int], pos1: list[int, int]):
    return max(abs(pos0[0] - pos1[0]), abs(pos0[1] - pos1[1]))


class Circle:
    def __init__(self):
        pass
        # self.data = dict()

    def get(self, radius, color, contour):
        # img = self.data.get((radius, color, contour))
        # if img:
        #     return img
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color,
                           (radius, radius), radius, contour)
        # self.data[(radius, color, contour)] = surf
        # print(len(self.data))
        return surf

    def circle_to_head(self, radius, color, pos, grp=None, contour=3):
        surf = self.get(radius, color, contour)
        Head(surf, pos, grp)


play_sound('eat')
game = True
menu = MainMenu()
s_head = SnakeHead()
circle = Circle()
convert_error = True
packet_number = 0
tm_winner = ''
scr_grp = pygame.sprite.Group()
heads_group = pygame.sprite.Group()
main_head_grp = pygame.sprite.Group()

surf_radar = pygame.Surface((800, 800), pygame.SRCALPHA)
pygame.draw.circle(surf_radar, time_color, (400, 400), 400, 1)
pygame.draw.circle(surf_radar, time_color, (400, 400), 350, 1)
pygame.draw.circle(surf_radar, time_color, (400, 400), 300, 1)
pygame.draw.circle(surf_radar, time_color, (400, 400), 250, 1)
for i in range(2):
    pygame.draw.line(surf_radar, time_color, (100, 100 + i * 600), (700, 700 - i * 600), 1)
    pygame.draw.line(surf_radar, time_color, (i * 400, 400 - i * 400), (800 - i * 400, 400 + i * 400), 1)
    # pygame.draw.line(surf, background, (i * 4, 0), (i * 4, 800), 1)
pygame.draw.circle(surf_radar, background, (400, 400), 220)

while game:
    camera = Camera(0, 0)
    my_pos = [0, 0]
    game = menu.exec(screen)
    menu.check_user_name()
    gamers = dict()
    scr_dx = screen.get_width() // 2
    scr_dy = screen.get_height() // 2
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Подключение к серверу: {Const.data['HOST']}:{Const.data['PORT']}")
            s.connect((Const.data['HOST'], Const.data['PORT']))
            my_addr = s.getsockname()[0]
            print(' ADDR:', my_addr)
            flag = game
            end_clr = [255, 255, 255]
            len_body = 0
            old_data = dict()
            gamers.clear()
            while flag:
                scr_grp.empty()
                heads_group.empty()
                main_head_grp.empty()
                cmd = {'key': [], 'name': menu.user_name}
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        flag = False
                    if event.type == (pygame.USEREVENT + 1000):
                        tm_winner = ''
                        break
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # cmd['pos'] = event.pos
                        if event.button == 3:
                            cmd['key'] = ["stop"]

                keys = pygame.key.get_pressed()
                if any(keys):
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        cmd['key'].append("left")
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        cmd['key'].append("right")
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        cmd['key'].append("up")
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        cmd['key'].append("down")
                    if keys[pygame.K_SPACE]:
                        cmd['key'] = ["stop"]
                    if keys[pygame.K_TAB]:
                        cmd['key'] = ["freeze"]
                    if keys[pygame.K_ESCAPE]:
                        flag = False
                # st = json.dumps(cmd)
                try:
                    s.send(zlib.compress(msgpack.packb(cmd)) + b'0%%0%0%%0')
                except Exception as err:
                    print('Error of send:', err)
                try:
                    buff += s.recv(DATA_WIND)
                    # buff += s.recv(DATA_WIND)
                    # buff += s.recv(DATA_WIND)
                    # print(buff)
                except Exception as err:
                    print('Error of receive:', err, 'BUF:', len(buff))
                data = dict()
                while (pos := buff.find(b'0%%0%0%%0')) >= 0:
                    i_data = buff[:pos]
                    buff = buff[pos + 9:]
                    try:
                        data: dict[tuple[list, int, int, int, int]] = msgpack.unpackb(zlib.decompress(i_data))
                        convert_error = True
                        Const.WIDTH, Const.HEIGHT = data.get('AREA_SIZE', [Const.WIDTH, Const.HEIGHT])
                    except json.JSONDecodeError:
                        print('JSON convert error.', data)
                        convert_error = False
                        # continue
                    except Exception as err:
                        print('UNPACK Error ==> ', err)
                        convert_error = False
                        # continue
                try:
                    my_pos = data['players'][my_addr][0][0]
                    old_data = data
                    gud_packets = True
                except Exception as e:
                    gud_packets = False
                    print('MY POS ==>', e)
                    if old_data.get('players', None):
                        data = old_data
                        my_pos = data['players'][my_addr][0][0]
                        convert_error = True
                if convert_error:
                    winner = data.get('WINNER', '')
                    if winner:
                        # print('Победитель:', winner)
                        if not tm_winner:
                            pygame.time.set_timer(pygame.USEREVENT + 1000, 5000, 1)
                            print('Победитель:', winner)
                            tm_winner = f"Победитель: {winner}"
                    tm = data.get('TIMER', 999)
                    if tm < 2:
                        screen.fill(end_clr)
                        end_clr = max(0, end_clr[0] - 6), max(0, end_clr[1] - 4), max(0, end_clr[2] - 6)
                    else:
                        end_clr = [250, 255, 250]
                        screen.fill(background)
                    ScrSprite(surf_radar, (scr_dx - 400, scr_dy - 400), scr_grp)

                    surf = font_time.render(f"ТАЙМЕР: {tm}", False, time_color)
                    ScrSprite(surf, (60, 20), scr_grp)
                    if tm_winner:
                        surf = font_time.render(tm_winner, False, time_color)
                        ScrSprite(surf, (width // 2 - surf.get_rect().width // 2, height - 100), scr_grp)
                    surf = font_time.render(menu.user_name, False, time_color)
                    ScrSprite(surf, (width - surf.get_rect().width - 50, 20), scr_grp)
                    camera.move(*my_pos)
                    for eat in data.get('eats', []):
                        # pos, radius, color
                        l_pos = camera.shift(eat[0][0])
                        surf = pygame.Surface((eat[1] * 2, eat[1] * 2))
                        surf.fill(eat[2])
                        ScrSprite(surf, (l_pos[0] - eat[1], l_pos[1] - eat[1]), scr_grp)
                    for addr, player in data.get('players', dict()).items():
                        # body, radius, color, life, breake, sound, real_len
                        body, radius, color, hero_life, breake, sound, len_body = player
                        if sound:
                            play_sound(sound, addr)
                        figure = 0
                        my_head = addr == my_addr
                        if my_head:
                            gamers['me'] = body[0], len_body
                            surf = font_time.render(f"ДЛИНА: {len_body}", False, time_color)
                            ScrSprite(surf, (width - surf.get_rect().width - 50, 120), scr_grp)
                            color_r, color_g, color_b = menu.color
                        else:
                            if gamers.get('me'):
                                me_body = gamers['me'][0]
                                b_body = body[0]
                                if me_body[0] < b_body[0]:
                                    x1, x2 = b_body[0] - me_body[0], b_body[0] - Const.WIDTH - me_body[0]
                                else:
                                    x1, x2 = b_body[0] - me_body[0], b_body[0] + Const.WIDTH - me_body[0]
                                if me_body[1] < b_body[1]:
                                    y1, y2 = b_body[1] - me_body[1], b_body[1] - Const.HEIGHT - me_body[1]
                                else:
                                    y1, y2 = b_body[1] - me_body[1], b_body[1] + Const.HEIGHT - me_body[1]
                                dx = x1 if abs(x1) < abs(x2) else x2
                                dy = y1 if abs(y1) < abs(y2) else y2

                                if len_body > 30 and (abs(dx) > scr_dx or abs(dy) > scr_dy):
                                    rad = math.sqrt(dx * dx + dy * dy)
                                    if rad < 2000:
                                        koef = 250 / rad
                                    elif rad > 3000:
                                        koef = 400 / rad
                                    elif rad > 2500:
                                        koef = 350 / rad
                                    else:
                                        koef = 300 / rad

                                    _x = scr_dx + (dx * koef)
                                    _y = scr_dy + (dy * koef)
                                    dist = font.render(str(len_body), False, time_color)
                                    ScrSprite(dist, (_x, _y), scr_grp)
                                    # c_color = color if gamers['me'][1] > 100 else time_color
                                    rds = min(100, len_body // 2)
                                    circle.circle_to_head(rds, time_color, (_x - rds, _y - rds),
                                                   grp=scr_grp, contour=max(1, len_body // 50))
                            color_r, color_g, color_b = color
                        dr_color = (255 - color_r) // len_body
                        dg_color = (255 - color_g) // len_body
                        db_color = (255 - color_b) // len_body
                        txt_pos = [0, 0]
                        contour = 0
                        img, rect, *shift = s_head.get_head(body,
                                                            camera.shift(body[0]), radius, addr)
                        if img:
                            Head(img, rect, main_head_grp)
                            surf_0 = font.render(f"{hero_life}", False,
                                                 'pink', background)
                            Head(surf_0, (rect[0] + shift[0], rect[1] + shift[1]), main_head_grp)

                        pre_pos = camera.shift(body[0])
                        if breake > 0:
                            c_pos = camera.shift(body[0])
                            r_pos = c_pos[0] - radius, c_pos[1] - radius
                            b_color = (min(255, breake * 20), min(255, breake * 4), min(255, breake * 4))
                            circle.circle_to_head(radius + 4, b_color, (r_pos[0] - 4, r_pos[1] - 4),
                                           grp=heads_group, contour=4)
                        for i, pos in enumerate(body[len_body // 300:]):
                            c_pos = camera.shift(pos)
                            _radius = radius
                            r_pos = c_pos[0] - _radius, c_pos[1] - _radius
                            if i == 0:
                                txt_pos = r_pos
                                div = min(2, len(body))
                                color = (color_r // div, color_g // div, color_b // div)
                                radius -= 4
                                if len(body) == 1 or not img:
                                    circle.circle_to_head(_radius, color, r_pos, grp=heads_group)
                            else:
                                color = (color_r + dr_color * i,
                                         color_g + dg_color * i,
                                         color_b + db_color * i)
#                                if delta_pos(pre_pos, c_pos) <= 20:
                                radius = max(5, radius / 1.2)
                                circle.circle_to_head(_radius, color, r_pos,
                                               grp=heads_group, contour=max(3, len_body // 60))
                            pre_pos = c_pos
                else:
                    screen.fill(background)
                if gud_packets:
                    color = 'green'
                else:
                    color = 'red'
                circle.circle_to_head(10, color, (10, 10), grp=scr_grp, contour=3)
                surf = font.render(f"{int(clock.get_fps())}FPS", False, color)
                ScrSprite(surf, (40, 8), scr_grp)

                scr_grp.draw(screen)
                heads_group.draw(screen)
                main_head_grp.draw(screen)
                if gc.isenabled():
                    gc.collect()
                pygame.display.update()
                clock.tick(100)
    except ConnectionResetError:
        print('Try reconnect')
        # continue
    # except Exception as err:
    #     print('All errors: ', err)
pygame.quit()
sys.exit()
