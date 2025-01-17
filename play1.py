#!/usr/bin/env python3
# coding:utf-8
import pygame
from player import Player

pygame.init()  # Инициализируем pygame
sсreen = pygame.display.set_mode((800, 600))  # Создаем окно с разрешением 800x600
clock = pygame.time.Clock()  # Создаем объект для работы со временем внутри игры

player = Player()

while True:
    for event in pygame.event.get():  # Перебираем все события которые произошли с программой
        if event.type == pygame.QUIT:  # Проверяем на выход из игры
            exit()

    sсreen.fill((0, 0, 0))  # Заполняем экран черным
    sсreen.blit(player.image, player.rect)  # Рисуем игрока
    pygame.display.update()  # Обновляем дисплей

    clock.tick(60)  # Ограничиваем частоту кадров игры до 60