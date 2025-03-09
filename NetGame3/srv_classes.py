#!/usr/bin/env python3
# coding:utf-8
import datetime
import math
import random
import sqlite3
import zlib
import socket

import msgpack
import pygame
from cl_color import Color

from const import Const, rnd, random_coord


class MySprite(pygame.sprite.Sprite):
    def __init__(self, pos=(0, 0), radius=10, color='white', *args):
        super().__init__(*args)
        self.image = pygame.Surface([2, 2])
        self.rect = self.image.get_rect()
        self._radius = 1
        self.image, self.rect, self._radius = self.new_radius(radius)
        self.move_point(pos)

    def move_point(self, pos):
        if self.rect:
            self.rect.x = pos[0] - self._radius
            self.rect.y = pos[1] - self._radius

    def new_radius(self, radius, color='white'):
        if abs(self._radius - radius) > 1:
            a = radius * 2
            image = pygame.Surface((a, a))
            pygame.draw.circle(image, color, (radius, radius), radius)
            return image, image.get_rect(), radius
        else:
            return self.image, self.rect, self._radius

    def get_radius(self):
        return self._radius


class ScrSprite(pygame.sprite.Sprite):
    def __init__(self, surf: pygame.Surface, pos: tuple[int, int], *args):
        super().__init__(*args)
        self.image = surf
        rect = self.image.get_rect()
        self.rect = rect.move(*pos)


class Eat(MySprite):
    def __init__(self, eat_grp=None):
        self._spr_grp = eat_grp
        self._pos = [0, 0]
        self._body = [random_coord()]
        self._radius = 8
        self._figure = 0
        self._color = (50, 255, 50)
        self._life = 0
        super().__init__(self._body[0], self._radius, self._color, eat_grp)
        self._count = Const.EAT_LIFE

    def get_data(self):
        # return {'body': self._body, 'radius': self._radius, 'color': self._color,
        #         'figure': self._figure, 'length': '', 'life': '', 'breake': 0}
        # pos, radius, color
        return self._body, self._radius, self._color

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
            self._spr_grp.remove(self)
        return self._count < 0


class Player(MySprite):
    def __init__(self, pos=None, radius=Const.RADIUS, all_grp=None, eat_grp=None):
        self._spr_grp = all_grp
        self._eat_grp = eat_grp
        if pos is None:
            pos = random_coord()
        self._pos = [0, 0]
        self._freeze = False
        self._body = [pos]
        self._color = Color().color
        super().__init__(self._body[0], radius, self._color, all_grp)
        self._inc = 0
        self._data = dict()
        self._data_out = dict()
        self._step = Const.STEP
        self._figure = 0
        self._break = 0
        self._sound = ''
        self._life = Const.START_LIFE
        self.user_name = ''
        self.set_data({'key': rnd[random.randint(0, 3)]})
        self.super_speed = 1
        self.segment = MySprite()
        self._under_attack = False
        self._to_del = 0

    def set_under_attack(self):
        self._under_attack = True

    def reset_under_attack(self):
        self._under_attack = False

    def is_under_attack(self):
        return self._under_attack

    def is_break(self):
        return self._break > 0

    def get_pos(self):
        return self._pos

    def set_pos(self, pos=None):
        if pos:
            old_pos, self._pos = self._pos, pos
            return old_pos
        return self._pos

    def update(self):
        self._step = max(4, Const.STEP - self.get_length() // 100)
        if self.is_break():
            self._break -= 1
        else:
            if self._to_del:
                self.del_segment(self._to_del)
                self._to_del = 0
            self._pos[0] = 0 if self._pos[0] == 0 else math.copysign(self._step, self._pos[0])
            self._pos[1] = 0 if self._pos[1] == 0 else math.copysign(self._step, self._pos[1])
            cmd = self._data.get('key', "")
            pos = self._data.get('pos', [])
            # if pos:
            #     self.move_head([pos[0] - self._body[0][0], pos[1] - self._body[0][1]])
            _pos = self._pos
            if cmd:
                if 'left' in cmd:
                    if self._pos[0] == 0 or Const.MIN_SAFE_LENGTH > self.get_length():
                        self._pos[0] = -self._step
                    self._pos[1] = 0
                elif 'right' in cmd:
                    if self._pos[0] == 0 or Const.MIN_SAFE_LENGTH > self.get_length():
                        self._pos[0] = self._step
                    self._pos[1] = 0
                elif 'down' in cmd:
                    if self._pos[1] == 0 or Const.MIN_SAFE_LENGTH > self.get_length():
                        self._pos[1] = self._step
                    self._pos[0] = 0
                elif 'up' in cmd:
                    if self._pos[1] == 0 or Const.MIN_SAFE_LENGTH > self.get_length():
                        self._pos[1] = -self._step
                    self._pos[0] = 0
                elif 'stop' in cmd and self.super_speed == 1:
                    if self._pos[0] == 0:
                        self._pos[1] = math.copysign(Const.STEP, self._pos[1]) * 2
                        # self._pos[1] *= 2
                    else:
                        self._pos[0] = math.copysign(Const.STEP, self._pos[0]) * 2
                        # self._pos[0] *= 2
                    self.to_del_segment(max(1, self.get_length() // 10))
                    self.super_speed = 0
                    self.breake()
                elif 'freeze' in cmd:
                    self._pos[1] = 0
                    self._pos[0] = 0
                    self._freeze = True
                # if abs(_pos[0]) == abs(self._pos[0]) and abs(_pos[1]) == abs(self._pos[1]):
                #     self.set_pos(_pos)
                if self._freeze and any(self._pos):
                    self.breake()
                    self._freeze = False

            if Network.num % 3 == 0:
                sprites = self._spr_grp.copy()
                sprites.remove(self)
                if self.eat_in_head():
                    self.add_segment()
                if not self.is_head_to_head(sprites):
                    self.is_body_atak(sprites)
        self._data['key'] = None
        self.move()

    def to_del_segment(self, cnt):
        self._to_del = cnt

    def is_body_atak(self, sprites):
        if self.is_break():
            return False
        start_segment = 4
        coll = 0
        step = max([1, (self.get_length() - start_segment) // 10])
        for i in range(start_segment, self.get_length(), step):
            self.segment.move_point(self._body[i])
            player = pygame.sprite.spritecollideany(self.segment, sprites)
            if player and not player.is_break():
                coll = i
                break
            if i >= Const.MIN_SAFE_LENGTH:
                sprites.add(self)
        else:
            return
        cut = self.get_length() - coll
        if self == player:
            if  any(self._pos):
                self.del_segment(cut)
                self.set_sound('ataka')
                self.set_under_attack()
        else:
            if cut <= player.get_length():
                self.del_segment(cut)
                self.set_under_attack()
                self.set_sound('ataka')
                player.add_segment(cut, 1)
                player.set_sound('ataka')
            else:
                player.reverse()

    def change_impulse(self, player):
        if self.get_length() > player.get_length():
            s1, s2 = self, player
        else:
            s1, s2 = player, self
        s_pos = s1.get_pos()
        p_pos = s2.get_pos()
        if s_pos[0] == p_pos[0] or s_pos[1] == p_pos[1]:
            s1.set_pos([p_pos[1], p_pos[0]])
            s2.set_pos([s_pos[1], s_pos[0]])
        else:
            self._pos = player.set_pos(self._pos)

    def is_head_to_head(self, sprites):
        if self.is_break():
            return False
        player = pygame.sprite.spritecollideany(self, sprites)
        if player and not player.is_break():
            if self.get_length() // player.get_length() > 10 or player.get_length() // self.get_length() > 10:
                return False
            else:
                if self.get_length() > player.get_length():
                    player.set_under_attack()
                    radius = self.get_radius()
                    player.move_head([math.copysign(1, self._pos[1]) * radius * 1.5,
                                      math.copysign(1, self._pos[0]) * radius * 1.5])
                    player.set_data({'key': rnd[random.randint(0, 4)]})
                elif self.get_length() <= player.get_length():
                    radius = player.get_radius()
                    pos = player.get_pos()
                    self.move_head([math.copysign(1, pos[1]) * radius * 1.5,
                                    math.copysign(1, pos[0]) * radius * 1.5])
                    self.set_data({'key': rnd[random.randint(0, 4)]})
                if self.get_life() == 0 and self.get_length() > 10:
                    self.del_segment(5)
                    self.life_dec()
                if player.get_life() == 0 and player.get_length() > 10:
                    player.del_segment(5)
                    self.life_dec()
                player.set_life(-1)
                player.breake()
                self.life_dec()
                self.breake()
                self.change_impulse(player)
                return True
        return False

    def life_dec(self):
        if self.get_life() > 0:
            self.set_life(-1)

    def move(self):
        segment = self._body[0].copy()
        for i in range(self.get_length()):
            if i == 0:
                self._body[i] = [(self._body[i][0] + self._pos[0]) % Const.WIDTH,
                                 (self._body[i][1] + self._pos[1]) % Const.HEIGHT]
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
        self.image, self.rect, self._radius = self.new_radius(self.calc_radius())
        self.move_point(self._body[0])

    def calc_radius(self):
        return min(150, max(Const.RADIUS, Const.RADIUS + self.get_length() // Const.SIZE_MUL))

    def del_segment(self, count=1):
        for _ in range(min(count, len(self._body) - 1)):
            self._body.pop()
        self.image, self.rect, self._radius = self.new_radius(self.calc_radius())

    def set_data(self, data):
        self._data = data
        self.user_name = self._data.get('name', '')

    def get_data(self):
        # body, radius, color, life, breake, sound, len_body
        body = [self.get_head()]
        for chip in self._body[1::min(10, max(2, self.get_length() // 100))]:
            # if not self.rect.collidepoint(*chip):
            body.append(chip)
        to_send = (body, self._radius, self._color,
                   self._life, self._break, self._sound, self.get_length())
        self._sound = ''
        return to_send

    def get_head(self):
        return self._body[0]

    def move_head(self, step):
        old = self._body[0]
        if abs(step[0]) > abs(step[1]):
            step[0] = 0
        else:
            step[1] = 0
        self._body[0] = [self._body[0][0] + step[0], self._body[0][1] + step[1]]
        return self.get_radius()

    def get_length(self):
        return len(self._body)

    def get_life(self):
        return self._life

    def set_life(self, delta=0):
        if self._break == 0:
            self._life = max(0, self._life + delta)
        return self._life

    def is_in_head(self, pos):
        if self.is_break():
            return False
        px, py = self._body[0]
        return self.rect.collidepoint(pos)
        # return abs(pos[0] - px) < self._radius and abs(pos[1] - py) < self._radius

    def eat_in_head(self):
        if self.is_break():
            return False
        ret = pygame.sprite.spritecollide(self, self._eat_grp, True)
        if ret:
            self.set_sound('eat')
        return ret

    def reverse(self):
        if self.is_break():
            return False
        self._pos = [self._pos[0] * -1, self._pos[1] * -1]
        self.breake()

    def breake(self):
        if not self.is_break():
            self._break = max(Const.RADIUS, self.get_length() // 3)
            self.set_sound('break')
        return True

    def add_data(self, rec: dict):
        for key, val in rec.items():
            self._data_out[key] = val

    def set_sound(self, sound=''):
        self._sound = sound


class Network:
    num = 0

    def __init__(self, _all_sprites, _eat_sprites):
        self._all_sprites = _all_sprites
        self._eat_sprites = _eat_sprites
        self.c_S_FPS = Const.S_FPS
        self.sound_on = False
        self.super_speed = 1
        self.clients = []
        self.player_sockets = []
        self.player_data = dict()
        self._buff = dict()
        # self.eat_data = []
        self.main_socket = self.init_socket()
        self.game_time = datetime.datetime.now()
        self.common_data = {'HOST': Const.data['HOST'], 'PORT': Const.data['PORT'],
                            'WINNER': ''}
        self.last_winner = ('', 0, '')
        self.bots_counter = Const.data['BOTS_COUNTER']
        self.game_timer = Const.data['GAME_TIMER']
        self.rect_area = {'game_timer': [pygame.Rect(710, 170, 15, 15), pygame.Rect(770, 170, 20, 15)],
                          'bots_counter': [pygame.Rect(710, 210, 15, 15), pygame.Rect(760, 210, 20, 15)],
                          'step_wait': [pygame.Rect(710, 250, 15, 15), pygame.Rect(750, 250, 20, 15)]
                          }
        self.con = None
        self.cur = None
        self.win_stat = dict()
        self.coords = set()
        self.init_sql()
        self.reset_game()

    def init_sql(self):
        self.con = sqlite3.connect('data/results.db')
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, addr VARCHAR(40), wins INTEGER, name VARCHAR(60));
                        """)
        if Const.restart:
            self.cur.execute("""DELETE FROM users""")
            self.con.commit()

    def get_sql_stat(self):
        sql_stat = self.cur.execute("SELECT * FROM users").fetchall()
        self.win_stat.clear()
        for rec in sql_stat:
            self.win_stat[rec[1]] = rec[2], rec[3]

    def add_sql(self, addr):
        res = self.cur.execute(f"SELECT * FROM users WHERE TRIM(addr) = '{addr}' ").fetchone()
        if not res:
            self.cur.execute(f"INSERT INTO users (addr, wins, name) VALUES ('{addr}', 0, '')")
            self.con.commit()
        self.get_sql_stat()

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
            self.c_S_FPS = max(0, self.c_S_FPS - 1)
        elif check_area(pos, self.rect_area['step_wait'][1]):
            self.c_S_FPS = min(30, self.c_S_FPS + 1)

    def prepare_to_send(self):
        data = dict()
        for addr, player in self.player_data.items():
            data[addr] = player.get_data()
        eats = []
        for i, eat in enumerate(self._eat_sprites):
            eats.append(eat.get_data())
        ret = dict()
        ret['players'] = data
        ret['eats'] = eats
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
        main_socket.bind((Const.data['HOST'], Const.data['PORT']))
        main_socket.setblocking(False)
        main_socket.listen(1)
        print('Server started at:', f"{Const.data['HOST']}:{Const.data['PORT']}")
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
                count = f"{player.user_name}. Длина: {win_len}."
                self.last_winner = win_addr, win_len, win_name
        self.common_data['WINNER'] = count
        # print('Winner:', count)
        # print('new game!')
        wins = self.cur.execute(f"SELECT wins FROM users WHERE TRIM(addr) = '{self.last_winner[0]}'").fetchone()
        # print("WINS:", wins, self.last_winner)
        if wins:
            self.cur.execute(f"""UPDATE users SET wins = {wins[0] + 1}, name = '{self.last_winner[2]}' 
                        WHERE TRIM(addr) = '{self.last_winner[0]}'""")
            # print(wins)
            # print(self.last_winner)
        else:
            self.cur.execute(f"""INSERT INTO users (addr, wins, name) 
            VALUES ('{self.last_winner[0]}', 1, '{self.last_winner[2]}')""")

        self.con.commit()
        self.get_sql_stat()
        # print(win_stat)
        self.sound_on = False
        self.coords.clear()
        self._all_sprites.empty()
        for addr in self.player_data.copy():
            if addr[:3] == 'bot':
                self.player_data.pop(addr)
        for i in range(self.bots_counter):
            player = Player(all_grp=self._all_sprites, eat_grp=self._eat_sprites)
            if not Const.data['CHAOS']:
                player.set_data({'key': 'left'})
            player.add_segment(12)
            self.player_data[f"bot{i:03}"] = player
        for addr in self.player_data.keys():
            if addr[0] != 'b':
                self.player_data[addr] = Player(all_grp=self._all_sprites, eat_grp=self._eat_sprites)

    def handle(self, sock: socket.socket, addr: str) -> any:
        buff = self._buff.get(addr, b'')
        try:
            buff += sock.recv(Const.data['DATA_WIND'])
        except ConnectionError:
            print(f"Client suddenly closed while receiving {sock}")
            return None
        except BlockingIOError:
            pass
        except Exception as e:
            print('Receive error:', e)
        i_data = dict()
        while (pos := buff.find(b'0%%0%0%%0')) >= 0:
            i_data = buff[:pos]
            buff = buff[pos + 9:]
        self._buff[addr] = buff
        try:
            data = msgpack.unpackb(zlib.decompress(i_data))  # Should be ready
        except:
            data = dict()
        return data

    def send_data(self, sock, data):
        try:
            sock.send(data)  # Hope it won't block
        except ConnectionError:
            print(f"Client suddenly closed, cannot send")
            return False
        except BlockingIOError:
            pass
        return True

    def ai_event(self):
        test = True
        for addr, unit in self.player_data.items():
            if unit.is_under_attack() and 'bot' in addr:
                try:
                    self.player_data[f"{addr}"].set_data({'key': rnd[random.randint(0, 4)]})
                    unit.reset_under_attack()
                    test = False
                except:
                    pass
        if test:
            bots = [addr for addr in self.player_data.keys() if 'bot' in addr]
            if bots:
                addr = random.choices(bots, k=random.randint(1, 5))
                try:
                    self.player_data[addr].set_data({'key': rnd[random.randint(0, 3)]})
                except:
                    pass


