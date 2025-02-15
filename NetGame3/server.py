#!/usr/bin/env python3
# coding:utf-8
import math
from pprint import pprint
import datetime
import colorsys
import random
import socket
import sys
import time
import json
import zlib
import sqlite3
from random import randint

import pygame

from const import Const


def load_config():
    global S_FPS, EAT_COUNT, EAT_LIFE
    with open('srv_config.json') as f:
        data = json.load(f)
        print(data)
        s_port = data.get('PORT')
        s_host = data.get('HOST')
        if s_port:
            Const.data['PORT'] = int(s_port)
        if s_host:
            Const.data['HOST'] = s_host
        Const.data['GAME_TIMER'] = int(data.get('GAME_TIMER', Const.data['GAME_TIMER']))
        Const.data['BOTS_COUNTER'] = int(data.get('BOTS_COUNTER', Const.data['BOTS_COUNTER']))
        Const.data['STEP_WAIT'] = int(data.get('STEP_WAIT', Const.data['STEP_WAIT']))
        Const.data['DATA_WIND'] = int(data.get('DATA_WIND', Const.data['DATA_WIND']))
        Const.data['CHAOS'] = int(data.get('CHAOS', Const.data['CHAOS']))
        S_FPS = int(data.get('S_FPS', 100))
        EAT_COUNT = int(data.get('EAT_COUNT', 10))
        EAT_LIFE = int(data.get('EAT_LIFE', 300))
        Const.MIN_SAFE_LENGTH = int(data.get('MIN_SAFE_LENGTH', 30))
        Const.START_LIFE = int(data.get('START_LIFE', 10))
        Const.WIDTH = int(data.get('WIDTH', 3000))
        Const.HEIGHT = int(data.get('HEIGHT', 3000))


pygame.init()
S_SIZE = S_WIDTH, S_HEIGHT = 850, 550
screen = pygame.display.set_mode(S_SIZE)
s_clock = pygame.time.Clock()
S_FPS = 0
EAT_COUNT = 0
EAT_LIFE = 0

load_config()

ALIAS = False
# font = pygame.font.Font('data/Pressdarling.ttf', size=20)
font = pygame.font.Font('data/Capsmall.ttf', size=20)
font2 = pygame.font.Font('data/Capsmall.ttf', size=25)
ten_sound = pygame.mixer.Sound('data/ten_second.ogg')

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
packet_size = 0
DATA_WIND = Const.data['DATA_WIND']  # размер пакета данных
WIDTH, HEIGHT = Const.WIDTH, Const.HEIGHT
STEP = Const.STEP
RADIUS = Const.RADIUS
COUNT = Const.COUNT
SIZE_MUL = Const.SIZE_MUL
MIN_SAFE_LENGTH = Const.MIN_SAFE_LENGTH

coords = set()
rnd = ['left', 'right', 'up', 'down']

con = sqlite3.connect('data/results.db')
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, addr VARCHAR(40), wins INTEGER, name VARCHAR(60));
                """)
if Const.restart:
    cur.execute("""DELETE FROM users""")
    con.commit()

win_stat = dict()


def get_sql_stat():
    global win_stat
    sql_stat = cur.execute("SELECT * FROM users").fetchall()
    win_stat = dict()
    for rec in sql_stat:
        win_stat[rec[1]] = rec[2], rec[3]


all_sprites = pygame.sprite.Group()
eat_sprites = pygame.sprite.Group()


def random_coord():
    x = 5 * STEP * (randint(1, WIDTH // STEP // 5 - 1))
    y = 5 * STEP * (randint(1, HEIGHT // STEP // 5 - 1))
    return [x, y]


class MySprite(pygame.sprite.Sprite):
    def __init__(self, pos=(0, 0), radius=10, color='white', *args):
        super().__init__(*args)
        self._radius = radius
        self.image, self.rect = self.new_radius(radius, color)
        self.move_point(pos)

    def move_point(self, pos):
        self.rect.x = pos[0] - self._radius
        self.rect.y = pos[1] - self._radius

    def new_radius(self, radius, color):
        a = radius * 2
        image = pygame.Surface((a, a))
        pygame.draw.circle(image, color, (radius, radius), radius)
        self._radius = radius
        return image, image.get_rect()

    def get_radius(self):
        return self._radius


class Color:
    data = [0.1, 0.95, 0.2, 0, 85, 0.3, 0.75, 0.4, 0.65, 0.5,
            0.55, 0.6, 0.45, 0.7, 0.35, 0.8, 0.25, 0.9, 0.15]
    random.shuffle(data)
    count = 0

    def __init__(self):
        h, s, l = Color.data[Color.count], 0.9, 0.4 + random.random() / 5.0
        r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
        self.color = (r, g, b)
        Color.count = (Color.count + 1) % len(Color.data)


class Eat(MySprite):
    def __init__(self):
        self._pos = [0, 0]
        self._body = [random_coord()]
        self._radius = 8
        self._figure = 0
        self._color = (50, 255, 50)
        self._life = 0
        super().__init__(self._body[0], self._radius, self._color, eat_sprites)
        self._count = EAT_LIFE

    def get_data(self):
        return {'body': self._body, 'radius': self._radius, 'color': self._color,
                'figure': self._figure, 'length': '', 'life': ''}

    def get_head(self):
        return self._body[0]

    def update(self):
        self._count -= 1
        r, g, b = self._color
        r = min(200, r + 1)
        g = max(10, g - 1)
        b = max(0, b - 1)
        self._color = (r, g, b)
        if self._count < 0:
            eat_sprites.remove(self)
        return self._count < 0


class Player(MySprite):
    def __init__(self, pos=None, radius=RADIUS):
        if pos is None:
            pos = random_coord()
        self._pos = [0, 0]
        self._body = [pos]
        self._color = Color().color
        super().__init__(self._body[0], radius, self._color, all_sprites)
        self._inc = 0
        self._data = dict()
        self._data_out = dict()
        self._step = STEP
        self._iter = 0
        self._wait = Const.data['STEP_WAIT']
        self._figure = 0
        self._break = 0
        self._life = Const.START_LIFE
        self.user_name = ''
        self.set_data({'key': rnd[random.randint(0, 3)]})
        self.super_speed = 1
        self.segment = MySprite()

    def is_break(self):
        return self._break > 0

    def get_pos(self):
        return self._pos

    def set_pos(self, pos):
        old_pos, self._pos = self._pos, pos
        return old_pos

    def update(self):
        if self._break <= 0:
            self._pos[0] = 0 if self._pos[0] == 0 else math.copysign(self._step, self._pos[0])
            self._pos[1] = 0 if self._pos[1] == 0 else math.copysign(self._step, self._pos[1])
            cmd = self._data.get('key', [])
            if cmd:
                if 'left' in cmd:
                    self._pos[0] = -self._step
                    self._pos[1] = 0
                if 'right' in cmd:
                    self._pos[0] = self._step
                    self._pos[1] = 0
                if 'down' in cmd:
                    self._pos[1] = self._step
                    self._pos[0] = 0
                if 'up' in cmd:
                    self._pos[1] = -self._step
                    self._pos[0] = 0
                if 'stop' in cmd and self.super_speed == 1:
                    self._pos[1] *= 2
                    self._pos[0] *= 2
                    self.super_speed = 0
                    self.breake()
            if Network.num % 4 == 0:
                sprites = all_sprites.copy()
                sprites.remove(self)
                if self.eat_in_head():
                    self.add_segment()
                self.is_head_to_head(sprites)
                self.is_body_atak(sprites)
        else:
            self._break -= 1
        self._data['key'] = None
        self._iter += 1
        if self._iter > self._wait:
            self._iter = 0
            self.move()

    def is_body_atak(self, sprites):
        if self.is_break():
            return False
        start_segment = 4
        coll = 0
        step = max([1, (self.get_length() - start_segment) // 10])
        for i in range(start_segment, self.get_length(), step):
            self.segment.move_point(self._body[i])
            player = pygame.sprite.spritecollideany(self.segment, sprites)
            if player:
                coll = i
                break
            if i >= MIN_SAFE_LENGTH:
                sprites.add(self)
        else:
            return
        cut = self.get_length() - coll
        if self == player:
            self.del_segment(cut)
            self._data_out['sound'] = 'ataka'
        else:
            if cut <= player.get_length():
                self.del_segment(cut)
                self._data_out['sound'] = 'ataka'
                player.add_segment(cut, 1)
                player.add_data({'sound': 'ataka'})
            else:
                player.reverse()

    def is_head_to_head(self, sprites):
        if self.is_break():
            return False
        player = pygame.sprite.spritecollideany(self, sprites)
        if player:
            self._pos = player.set_pos(self._pos)
            if self.get_life() == 0 and self.get_length() > 10:
                self.del_segment(5)
            if player.get_life() == 0 and player.get_length() > 10:
                player.del_segment(5)
            self.set_life(-1)
            player.set_life(-1)
            player.breake()
            self.breake()

    def move(self):
        segment = self._body[0].copy()
        for i in range(self.get_length()):
            if i == 0:
                self._body[i] = [(self._body[i][0] + self._pos[0]) % WIDTH,
                                 (self._body[i][1] + self._pos[1]) % HEIGHT]
                self.move_point(self._body[0])
            else:
                segment, self._body[i] = self._body[i], segment
        self.add_segment(count=self._inc)
        self._inc = 0

    def add_segment(self, count=1, life=0):
        self.set_life(life)
        segment = self._body[-1]
        for _ in range(count):
            self._body.append(segment)
        self.image, self.rect = self.new_radius(self.calc_radius(),
                                                self._color)
        self.move_point(self._body[0])

    def calc_radius(self):
        return max(RADIUS, RADIUS + len(self._body) // SIZE_MUL)

    def del_segment(self, count=1):
        for _ in range(min(count, len(self._body) - 1)):
            self._body.pop()
        self.image, self.rect = self.new_radius(self.calc_radius(),
                                                self._color)
        if self.get_life() > 0:
            self.set_life(-1)

    def set_data(self, data):
        self._data = data
        self.user_name = self._data.get('name', '')

    def get_data(self):
        self._data_out['body'] = self._body
        self._data_out['radius'] = self._radius
        self._data_out['color'] = self._color
        self._data_out['figure'] = self._figure
        self._data_out['length'] = self.get_length()
        self._data_out['life'] = self._life
        to_send = self._data_out.copy()
        self._data_out.clear()
        return to_send

    def get_head(self):
        return self._body[0]

    def get_length(self):
        return len(self._body)

    def get_life(self):
        return self._life

    def set_life(self, delta=0):
        if self._break == 0:
            self._life = max(0, self._life + delta)
        return self._life

    def is_in_head(self, pos):
        if self._break:
            return False
        px, py = self._body[0]
        return self.rect.collidepoint(pos)
        # return abs(pos[0] - px) < self._radius and abs(pos[1] - py) < self._radius

    def eat_in_head(self):
        if self._break:
            return False
        ret = pygame.sprite.spritecollide(self, eat_sprites, True)
        if ret:
            self._data_out['sound'] = 'eat'
        return ret

    def reverse(self):
        if self.is_break():
            return
        self._pos = [self._pos[0] * -1, self._pos[1] * -1]
        self.breake()

    def breake(self):
        # if self._break > 0:
        #     return
        self._break = max([40, len(self._body) // 2 + RADIUS])
        self._data_out['sound'] = 'break'

    def add_data(self, rec: dict):
        for key, val in rec.items():
            self._data_out[key] = val


class Network:
    num = 0

    def __init__(self):
        self.sound_on = False
        self.super_speed = 1
        self.clients = []
        self.player_sockets = []
        self.player_data = dict()
        # self.eat_data = []
        self.main_socket = self.init_socket()
        self.game_time = datetime.datetime.now()
        self.common_data = {'HOST': HOST, 'PORT': Const.data['PORT'],
                            'WINNER': ''}
        self.last_winner = ('', 0, '')
        self.bots_counter = Const.data['BOTS_COUNTER']
        self.game_timer = Const.data['GAME_TIMER']
        # self.step_wait = Const.data['STEP_WAIT']
        self.rect_area = {'game_timer': [pygame.Rect(710, 170, 15, 15), pygame.Rect(770, 170, 20, 15)],
                          'bots_counter': [pygame.Rect(710, 210, 15, 15), pygame.Rect(760, 210, 20, 15)],
                          'step_wait': [pygame.Rect(710, 250, 15, 15), pygame.Rect(750, 250, 20, 15)]
                          }
        self.reset_game()

    def check_click(self, pos):
        def check_area(pos: list[int, int], rect: pygame.Rect):
            return rect.collidepoint(pos)

        if check_area(pos, self.rect_area['bots_counter'][0]):
            self.bots_counter = max(0, self.bots_counter - 1)
        elif check_area(pos, self.rect_area['bots_counter'][1]):
            self.bots_counter = min(50, self.bots_counter + 1)
        elif check_area(pos, self.rect_area['game_timer'][0]):
            self.game_timer = max(10, self.game_timer - 10)
        elif check_area(pos, self.rect_area['game_timer'][1]):
            self.game_timer = min(600, self.game_timer + 10)
        elif check_area(pos, self.rect_area['step_wait'][0]):
            Const.data['STEP_WAIT'] = max(0, Const.data['STEP_WAIT'] - 1)
        elif check_area(pos, self.rect_area['step_wait'][1]):
            Const.data['STEP_WAIT'] = min(15, Const.data['STEP_WAIT'] + 1)

    def prepare_to_send(self):
        data = dict()
        for addr, player in self.player_data.items():
            data[addr] = player.get_data()
        for i, eat in enumerate(eat_sprites):
            data[f'eat{i:03}'] = eat.get_data()
        ret = dict()
        ret['players'] = data
        if self.common_data['WINNER']:
            ret['WINNER'] = self.common_data['WINNER']
            self.common_data['WINNER'] = ''
        timer = self.game_timer - self.get_time_sec()
        ret['TIMER'] = timer
        ret['NUMBER'] = Network.num
        ret['AREA_SIZE'] = [Const.WIDTH, Const.HEIGHT]
        Network.num += 1
        return ret

    def init_socket(self):
        main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        main_socket.bind((HOST, Const.data['PORT']))
        main_socket.setblocking(False)
        main_socket.listen(1)
        print('Server started at:', HOST, Const.data['PORT'])
        return main_socket

    def init_game(self):
        if datetime.datetime.now() - self.game_time > datetime.timedelta(
                seconds=self.game_timer):
            self.game_time = datetime.datetime.now()
            self.reset_game()

    def get_time_sec(self):
        return (datetime.datetime.now().second + datetime.datetime.now().minute * 60) - (
                self.game_time.second + self.game_time.minute * 60)

    def reset_game(self):
        global all_sprites
        Network.num = 0
        self.super_speed = 1
        count = ''
        self.game_time = datetime.datetime.now()
        win_addr, win_len = '', 0
        for addr, player in self.player_data.items():
            if player.get_length() > win_len:
                win_addr = f"{addr}"
                win_name = f"{player.user_name} ({addr})"
                win_len = player.get_length()
                count = f"{win_addr}. Длина: {win_len}."
                self.last_winner = win_addr, win_len, win_name
        self.common_data['WINNER'] = count
        # print('Winner:', count)
        # print('new game!')
        wins = cur.execute(f"SELECT wins FROM users WHERE TRIM(addr) = '{self.last_winner[0]}'").fetchone()
        # print("WINS:", wins, self.last_winner)
        if wins:
            cur.execute(f"""UPDATE users SET wins = {wins[0] + 1}, name = '{self.last_winner[2]}' 
                        WHERE TRIM(addr) = '{self.last_winner[0]}'""")
            # print(wins)
            # print(self.last_winner)
        else:
            cur.execute(f"""INSERT INTO users (addr, wins, name) 
            VALUES ('{self.last_winner[0]}', 1, '{self.last_winner[2]}')""")

        con.commit()
        get_sql_stat()
        # print(win_stat)
        self.sound_on = False
        coords.clear()
        all_sprites = pygame.sprite.Group()
        for addr in self.player_data.copy():
            if addr[:3] == 'bot':
                self.player_data.pop(addr)
        for i in range(self.bots_counter):
            player = Player()
            if not Const.data['CHAOS']:
                player.set_data({'key': 'left'})
            player.add_segment(12)
            self.player_data[f"bot{i:03}"] = player
        for addr in self.player_data.keys():
            if addr[0] != 'b':
                self.player_data[addr] = Player()

    def handle(self, sock: socket.socket) -> any:
        data = None
        try:
            data = zlib.decompress(sock.recv(DATA_WIND)).decode()  # Should be ready
        except ConnectionError:
            print(f"Client suddenly closed while receiving {sock}")
            return None
        except BlockingIOError:
            pass
        except Exception as e:
            print('Receive error:', e)
        return data

    def send_data(self, sock, data):
        try:
            sock.sendall(data)  # Hope it won't block
        except ConnectionError:
            print(f"Client suddenly closed, cannot send")
            return False
        except BlockingIOError:
            pass
        return True


if __name__ == "__main__":
    packet_size_0 = 0
    srv_host = Network()
    texts = [font2.render(f"{hostname} IP: {HOST} PORT: {Const.data['PORT']}", True, 'red'),
             font2.render("Последний победитель:", True, 'green'),
             font2.render('Ботов в игре:', True, 'orange'),
             font2.render('Длина тайма:', True, 'orange'),
             font2.render('Скорость:', True, 'orange')]

    # Игровой цикл
    pygame.time.set_timer(pygame.USEREVENT + 1100, 1000, 0)
    pygame.time.set_timer(pygame.USEREVENT + 1200, 3000, 0)
    new_eat_counter = 0
    # test_time = 0
    cicle = True
    while cicle:
        srv_host.init_game()
        try:
            new_socket, addr = srv_host.main_socket.accept()
            addr = addr[0]
            srv_host.main_socket.setblocking(False)
            srv_host.player_sockets.append(new_socket)
            srv_host.player_data[addr] = srv_host.player_data.get(addr, Player())
            print('Connection from:', addr)
            res = cur.execute(f"SELECT * FROM users WHERE TRIM(addr) = '{addr}' ").fetchone()
            if not res:
                cur.execute(f"INSERT INTO users (addr, wins, name) VALUES ('{addr}', 0, '')")
                con.commit()
            get_sql_stat()
        except BlockingIOError:
            pass

        # Обработка активности
        # ------------------------------------------------------
        # Игровая механика
        all_sprites.update()
        eat_sprites.update()

        # Проверка поедания корма
        if new_eat_counter == COUNT:
            new_eat_counter = 0
        new_eat_counter += 1
        if len(eat_sprites) < EAT_COUNT:
            Eat()
            # print('EAT:', len(eat_sprites), EAT_COUNT)
            # print('CNT:', len(srv_host.player_data))

        # Передача данных игрокам
        data = srv_host.prepare_to_send()
        try:
            data = json.dumps(data)
            data = zlib.compress(data.encode('utf-8')) + b'0%%0%0%%0'
            packet_size = len(data)
        except Exception as err:
            print('Error prepare to send:', err)
        for sock in srv_host.player_sockets:
            if not srv_host.send_data(sock, data):
                srv_host.player_sockets.remove(sock)
                sock.close()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cicle = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                srv_host.check_click(event.pos)
            # if event.type == pygame.MOUSEMOTION:
            #     pygame.display.set_caption(f"{event.pos}")
            if event.type == pygame.USEREVENT + 1100:
                rnd_num = randint(0, srv_host.bots_counter - 1)
                try:
                    srv_host.player_data[f"bot{rnd_num:03}"].set_data({'key': rnd[random.randint(0, 3)]})
                except:
                    pass
            if event.type == pygame.USEREVENT + 1200:
                srv_host.super_speed = 1

        # Вывод статистики
        screen.fill(pygame.Color((0, 0, 127)))
        text = font.render(f"{'=' * 10} PLAYERS {'=' * 10}", ALIAS, 'yellow')
        screen.blit(text, (45, 50))
        i = 0
        for (addr, player) in srv_host.player_data.items():
            if srv_host.super_speed == 1:
                player.super_speed = 1
            if addr[:3] != 'bot':
                color = 'red' if addr == srv_host.last_winner[0] else 'yellow' if addr[:3] != 'bot' else 'gray'
                text = font.render(f"{i + 1:02}: [{win_stat.get(addr, [' ',player.user_name])[1]}] == LF: "
                                   f"{player.get_life()}, LN: {player.get_length()}, "
                                   f"WINS: {win_stat.get(addr, [' '])[0]}",
                                   ALIAS, color)
                screen.blit(text, (20, 70 + i * 25))
                i += 1
        srv_host.super_speed = 0
        screen.blit(texts[0], (S_WIDTH // 2 - texts[0].get_rect().width // 2, 5))
        screen.blit(texts[1], (460, 400))
        text = font2.render(f"[{srv_host.last_winner[2]}] {srv_host.last_winner[1]}",
                            ALIAS, 'green')
        screen.blit(text, (500, 450))
        game_time = srv_host.game_timer - srv_host.get_time_sec()
        if game_time <= 10 and not srv_host.sound_on:
            srv_host.sound_on = True
            ten_sound.play()
        text = font2.render(f"Timer: {game_time} сек",
                            ALIAS, 'green')
        screen.blit(text, (560, 80))
        screen.blit(texts[2], (500, 200))
        text = font2.render(f"- {srv_host.bots_counter:02} +", ALIAS, 'orange')
        screen.blit(text, (710, 200))
        screen.blit(texts[3], (500, 160))
        text = font2.render(f"- {srv_host.game_timer:03} +", ALIAS, 'orange')
        screen.blit(text, (710, 160))
        screen.blit(texts[4], (500, 240))
        text = font2.render(f"- {Const.data['STEP_WAIT']:01} +", ALIAS, 'orange')
        screen.blit(text, (710, 240))
        packet_size_0 = max([packet_size_0, packet_size])
        text = font2.render(f"Размер пакета: {10 * (packet_size_0 // 10)}", ALIAS, 'red')
        # text = font2.render(f"Размер пакета: {10 * (test_time // 10000000)}", ALIAS, 'red')
        screen.blit(text, (500, S_HEIGHT - 50))

        pygame.display.flip()

        # Получаем данные от игроков
        addr = ''
        for sock in srv_host.player_sockets.copy():
            if 'raddr' not in sock.__repr__():
                continue
            addr = sock.getpeername()
            addr = addr[0]
            data = srv_host.handle(sock)
            if data:
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = dict()
                srv_host.player_data[addr].set_data(data)
        # test_time = time.time_ns()
        s_clock.tick(S_FPS)
        # test_time = time.time_ns() - test_time

    pygame.quit()
    sys.exit()
