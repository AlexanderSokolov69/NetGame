#!/usr/bin/env python3
# coding:utf-8
import os
# import random
import socket
import sys
# import time
import json
import zlib
from random import choice
import pygame

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

DATA_WIND = Const.data['DATA_WIND']
SIZE_MUL = 2
l_text, h_text, step_text = 200, 200, 70
background = pygame.Color((0, 50, 0))
time_color = pygame.Color((10, 80, 10))
pygame.init()
size = width, height = 1400, 900
if FULLSCREEN:
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
FPS = 40


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

    def check_user_name(self):
        if not self.user_name:
            self.user_name = self.local_ip

    def exec(self, scr: pygame.Surface):
        mouse_pos = 0, 0
        click = False
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
                    else:
                        try:
                            sym = chr(event.key)
                            if 'a' <= sym <= 'z' or sym in '1234567890-=/.':
                                self.user_name = f"{self.user_name}{sym}"[:20].capitalize()
                        except:
                            pass

            scr.fill('black')
            scr.blit(self.image, (0, 0))
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


class Camera:
    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._center_x = width // 2
        self._center_y = height // 2
        self._queue = []
        self.q_len = 30
        self._window = 0

    def move(self, new_x, new_y, number=0):
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


color = choice(['white', 'red', 'blue', 'green', 'yellow'])
rnd = ['left', 'right', 'up', 'down']
buff = b''
my_addr = '-.-.-.-'
sound_brake = pygame.mixer.Sound('data/break1.ogg')
sound_eat = pygame.mixer.Sound('data/eat.ogg')
sound_ataka = pygame.mixer.Sound('data/brake.ogg')

font_win = pygame.font.Font('data/Capsmall.ttf', 50)
font_time = pygame.font.Font('data/Capsmall.ttf', 80)
img_list = [load_image('snake.png'), load_image('snake2.png'),
            load_image('snake3.png'), load_image('snake4.png')]
font = pygame.font.Font('data/Capsmall.ttf', size=20)


class SnakeHead:
    def __init__(self):
        self._history = dict()
        snake_head = img_list[3]
        snake_head2 = pygame.transform.flip(snake_head, True, False)
        self._img = {'right': snake_head,
                     'left': snake_head2,
                     'down': pygame.transform.rotate(snake_head2, -90),
                     'up': pygame.transform.rotate(snake_head2, 90)}

    def get_head(self, body, pos, radius, addr):
        if len(body) == 1:
            return None, None
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
        _img = pygame.transform.scale(self._img[a_state], (radius * 2, radius * 2))
        _rect = _img.get_rect().move(pos[0] - radius, pos[1] - radius)
        return _img, _rect, _shift_x, _shift_y


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
s_head = SnakeHead()
convert_error = True
packet_number = 0
tm_winner = ''
while game:
    camera = Camera(0, 0)
    my_pos = [0, 0]
    game = menu.exec(screen)
    menu.check_user_name()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Подключение к серверу: {Const.data['HOST']}:{Const.data['PORT']}")
            s.connect((Const.data['HOST'], Const.data['PORT']))
            my_addr = s.getsockname()[0]
            print(' ADDR:', my_addr)
            flag = game
            end_clr = [255, 255, 255]

            while flag:
                cmd = {'key': [], 'name': menu.user_name}
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        flag = False
                    if event.type == (pygame.USEREVENT + 1000):
                        tm_winner = ''
                        break
                    # if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    #     flag = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        cmd['pos'] = event.pos
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
                    if keys[pygame.K_ESCAPE]:
                        flag = False
                st = json.dumps(cmd)
                try:
                    s.sendall(zlib.compress(st.encode()))
                except Exception as err:
                    print('Error of send:', err)
                try:
                    buff += s.recv(DATA_WIND)
                    # print(buff)
                except Exception as err:
                    print('Error of receive:', err)
                if isinstance(data, dict):
                    old_data = data.copy()
                else:
                    old_data = dict()
                data = dict()
                while (pos := buff.find(b'0%%0%0%%0')) >= 0:
                    data = buff[:pos]
                    buff = buff[pos + 9:]
                    try:
                        data = json.loads(zlib.decompress(data).decode('utf-8'))
                        n = data['NUMBER']
                        if packet_number < n or n == 0:
                            convert_error = True
                            packet_number = n
                        else:
                            convert_error = False
                        Const.WIDTH, Const.HEIGHT = data.get('AREA_SIZE', [Const.WIDTH, Const.HEIGHT])
                    except json.JSONDecodeError:
                        print('JSON convert error.', data)
                        convert_error = False
                        continue
                    except Exception as err:
                        print('==> ', err)
                        convert_error = False
                        continue

                if convert_error:
                    winner = data.get('WINNER', '')
                    if winner:
                        # print('Победитель:', winner)
                        if not tm_winner:
                            pygame.time.set_timer(pygame.USEREVENT + 1000, 5000, 1)
                            print('Победитель:', winner)
                            tm_winner = f"Победитель: {winner}"
                    tm = data.get('TIMER', 999)
                    # pygame.display.set_caption(f"До конца раунда осталось: {tm} секунд...")
                    if tm < 2 or tm == 999:
                        screen.fill(pygame.Color(end_clr))
                        end_clr = max(0, end_clr[0] - 6), max(0, end_clr[1] - 4), max(0, end_clr[2] - 6)
                    else:
                        end_clr = [250, 255, 250]
                        screen.fill(background)

                    surf = font_time.render(f"ТАЙМЕР: {tm}", False, time_color)
                    screen.blit(surf, (60, 20))
                    if tm_winner:
                        surf = font_time.render(tm_winner, False, time_color)
                        screen.blit(surf, (50, height - 100))

                    # dr = 255 / (Const.WIDTH // 50)
                    # dg = 255 / (Const.HEIGHT // 50)
                    #
                    # r = 0
                    # g = 0
                    # b = 100
                    # for x in range(0, Const.WIDTH, 50):
                    #     g = 0
                    #     for y in range(0, Const.HEIGHT, 50):
                    #         pos = camera.shift((x + 22, y + 22))
                    #         if 0 <= pos[0] <= width and 0 <= pos[1] <= height:
                    #             pygame.draw.rect(screen, (int(r), int(g), random.randint(100, 255)), (*pos, 6, 6), 1)
                    #         g = g + dg
                    #     r = r + dr
                    try:
                        my_pos = data['players'][my_addr]['body'][0]
                    except Exception as e:
                        print('GET POS ==>', e)
                        data = old_data
                        # my_pos = data['players'][my_addr]['body'][0]
                    camera.move(*my_pos, data.get('NUMBER', 0))

                    for addr, player in data.get('players', dict()).items():
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
                        my_head = addr == my_addr
                        # print(radius)
                        color_r, color_g, color_b = player['color']
                        dr_color = (255 - color_r) // len_body
                        dg_color = (255 - color_g) // len_body
                        db_color = (255 - color_b) // len_body
                        txt_pos = [0, 0]
                        contour = 0
                        img, rect, *shift = s_head.get_head(body, camera.shift(body[0]), radius, addr)
                        for i, pos in enumerate(body):
                            pos = camera.shift(pos)
                            # if 0 <= pos[0] <= width and 0 <= pos[1] <= height:
                            if True:
                                # surf_1 = font.render(f"{hero_length}", False,
                                #                      'lightblue', background)
                                surf_0 = font.render(f"{hero_life}", False,
                                                     'pink', background)
                                # screen.blit(surf_0, (txt_pos[0], txt_pos[1]))
                                # screen.blit(surf_1, (txt_pos[0] + 10, txt_pos[1]))

                                _radius = radius
                                if i == 0:
                                    txt_pos = pos
                                    div = min(2, len(body))
                                    color = (color_r // div, color_g // div, color_b // div)
                                    radius -= 4
                                    # if my_head:
                                    #     pygame.draw.circle(screen, 'red', pos, _radius + 2, 2)
                                    if len(body) == 1:
                                        pygame.draw.circle(screen, color, pos, _radius, contour)
                                    #
                                    #     pygame.draw.circle(screen, 'white', pos, _radius)
                                    # else:
                                    if not img:
                                        pygame.draw.circle(screen, color, pos, _radius, contour)
                                else:
                                    color = (color_r + dr_color * i,
                                             color_g + dg_color * i,
                                             color_b + db_color * i)
                                    radius = max(3, radius / 1.1)
                                    pygame.draw.circle(screen, color, pos, _radius, contour)
                                    contour = 6
                            # pygame.draw.circle(screen, color, pos, _radius + 2)
                            if img:
                                screen.blit(img, rect)
                                screen.blit(surf_0, (rect[0] + shift[0], rect[1] + shift[1]))
                else:
                    screen.fill(background)
                pygame.display.flip()
                # clock.tick(FPS)
    except ConnectionResetError:
        print('Try reconnect')
        continue
    except Exception as err:
        print('All errors: ', err)
pygame.quit()
sys.exit()
