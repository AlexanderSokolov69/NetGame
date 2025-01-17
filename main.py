#!/usr/bin/env python3
# coding:utf-8
import pygame
from player import Player
from client import Client

pygame.init()  # Инициализируем pygame
HOST, PORT = "localhost", 8080  # Адрес сервера
client = Client((HOST, PORT))  # Создаем объект клиента
sсreen = pygame.display.set_mode((800, 600))  # Создаем окно с разрешением 800x600
clock = pygame.time.Clock()  # Создаем объект для работы со временем внутри игры

while True:
    for event in pygame.event.get():  # Перебираем все события которые произошли с программой
        if event.type == pygame.KEYDOWN:
            if event.key == ord('a'):
                client.move("left")
            if event.key == ord('d'):
                client.move("right")
            if event.key == ord('w'):
                client.move("up")
            if event.key == ord('s'):
                client.move("down")

        if event.type == pygame.QUIT:  # Проверяем на выход из игры
            client.sock.close()
            exit()

    sсreen.fill((0, 0, 0))  # Заполняем экран черным

    for i in client.players:
        print(i)
        player = Player((i["x"], i["y"]))
        sсreen.blit(player.image, player.rect)  # Рисуем игрока

    pygame.display.update()  # Обновляем дисплей

    clock.tick(60)  # Ограничиваем частоту кадров игры до 60