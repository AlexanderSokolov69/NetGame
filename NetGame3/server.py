#!/usr/bin/env python3
# coding:utf-8
import gc
import socket
import sys
import zlib

import msgpack
import pygame

from const import Const

Const()

pygame.init()
S_SIZE = S_WIDTH, S_HEIGHT = 850, 550
screen = pygame.display.set_mode(S_SIZE)
pygame.display.set_caption(f'ЗМЕИНЫЕ ГОНКИ. {Const.VERSION} (сервер)')
s_clock = pygame.time.Clock()

from srv_classes import Eat, Player, Network, ScrSprite

ALIAS = False
font = pygame.font.Font('data/Capsmall.ttf', size=20)
font2 = pygame.font.Font('data/Capsmall.ttf', size=25)
try:
    ten_sound = pygame.mixer.Sound('data/ten_second.ogg')
except:
    ten_sound = None

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
packet_size = 0
# test_time_0 = 999999999
# test_time = 0
scr_sprites = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
eat_sprites = pygame.sprite.Group()


if __name__ == "__main__":
    packet_size_0 = 0
    srv_host = Network(all_sprites, eat_sprites)
    texts = [font2.render(f"{hostname} IP: {Const.data['HOST']} PORT: {Const.data['PORT']}", True, 'red'),
             font2.render("Последний победитель:", True, 'green'),
             font2.render('Ботов в игре:', True, 'orange'),
             font2.render('Длина тайма:', True, 'orange'),
             font2.render('Скорость:', True, 'orange')]

    # Игровой цикл
    pygame.time.set_timer(pygame.USEREVENT + 1100, 500, 0)
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
            srv_host.player_data[addr] = srv_host.player_data.get(addr, Player(all_grp=all_sprites,
                                                                               eat_grp=eat_sprites))
            print('Connection from:', addr)
            srv_host.add_sql(addr)
        except BlockingIOError:
            pass

        # Обработка активности
        # ------------------------------------------------------
        # Игровая механика
        all_sprites.update()
        eat_sprites.update()

        # Подготовка к отрисовке экрана
        # ------------------------------------------------------
        scr_sprites.empty()
        ScrSprite(texts[0], (S_WIDTH // 2 - texts[0].get_rect().width // 2, 5), scr_sprites)
        ScrSprite(texts[1], (460, 400), scr_sprites)

        # Проверка поедания корма
        if new_eat_counter == Const.COUNT:
            new_eat_counter = 0
        new_eat_counter += 1
        if len(eat_sprites) < Const.EAT_COUNT:
            Eat(eat_grp=eat_sprites)

        # Передача данных игрокам
        data = srv_host.prepare_to_send()
        try:
            data = zlib.compress(msgpack.packb(data)) + b'0%%0%0%%0'
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
                srv_host.ai_event()
            if event.type == pygame.USEREVENT + 1200:
                srv_host.super_speed = 1

        # Вывод статистики
        screen.fill(pygame.Color((0, 0, 127)))
        text = font.render(f"{'=' * 10} PLAYERS {'=' * 10}", ALIAS, 'yellow')
        ScrSprite(text, (45, 50), scr_sprites)
        i = 0
        for (addr, player) in srv_host.player_data.items():
            if srv_host.super_speed == 1:
                player.super_speed = 1
            if addr[:3] != 'bot':
                color = 'red' if addr == srv_host.last_winner[0] else 'yellow' if addr[:3] != 'bot' else 'gray'
                text = font.render(f"{i + 1:02}: [{srv_host.win_stat.get(addr, [' ',player.user_name])[1]}] == LF: "
                                   f"{player.get_life()}, LN: {player.get_length()}, "
                                   f"WINS: {srv_host.win_stat.get(addr, [' '])[0]}",
                                   ALIAS, color)
                ScrSprite(text, (20, 70 + i * 25), scr_sprites)
                i += 1
        srv_host.super_speed = 0
        text = font2.render(f"[{srv_host.last_winner[2]}] {srv_host.last_winner[1]}",
                            ALIAS, 'green')
        ScrSprite(text, (500, 450), scr_sprites)
        game_time = srv_host.game_timer - srv_host.get_time_sec()
        if game_time <= 10 and not srv_host.sound_on:
            if ten_sound:
                srv_host.sound_on = True
                ten_sound.play()
        text = font2.render(f"Timer: {game_time} сек",
                            ALIAS, 'green')
        ScrSprite(text, (560, 80), scr_sprites)
        ScrSprite(texts[2], (500, 200), scr_sprites)
        text = font2.render(f"- {srv_host.bots_counter:02} +", ALIAS, 'orange')
        ScrSprite(text, (710, 200), scr_sprites)
        ScrSprite(texts[3], (500, 160), scr_sprites)
        text = font2.render(f"- {srv_host.game_timer:03} +", ALIAS, 'orange')
        ScrSprite(text, (710, 160), scr_sprites)
        screen.blit(texts[4], (500, 240))
        text = font2.render(f"- {srv_host.c_S_FPS:01} +", ALIAS, 'orange')
        ScrSprite(text, (710, 240), scr_sprites)
        packet_size_0 = max([packet_size_0, packet_size])
        text = font2.render(f"Размер пакета: {packet_size_0}", ALIAS, 'red')
        ScrSprite(text, (500, S_HEIGHT - 50), scr_sprites)

        scr_sprites.draw(screen)
        # if gc.isenabled():
        #     gc.collect()
        pygame.display.flip()

        # Получаем данные от игроков
        addr = ''
        for sock in srv_host.player_sockets.copy():
            if 'raddr' not in sock.__repr__():
                continue
            addr = sock.getpeername()[0]
            data = srv_host.handle(sock, addr)
            if data:
                srv_host.player_data[addr].set_data(data)
        S_FPS = 10 + srv_host.c_S_FPS * 10
        s_clock.tick(S_FPS)

    pygame.quit()
    sys.exit()
