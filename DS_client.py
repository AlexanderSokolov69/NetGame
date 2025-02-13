import socket
import pygame

# Конфигурация клиента
HOST = '127.0.0.1'
PORT = 5555

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Подключение к серверу
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Основной цикл клиента
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обработка движения
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        client_socket.sendall("move up".encode('utf-8'))
    if keys[pygame.K_DOWN]:
        client_socket.sendall("move down".encode('utf-8'))
    if keys[pygame.K_LEFT]:
        client_socket.sendall("move left".encode('utf-8'))
    if keys[pygame.K_RIGHT]:
        client_socket.sendall("move right".encode('utf-8'))

    # Получение данных от сервера
    data = client_socket.recv(1024).decode('utf-8')
    print(data)  # Вывод состояния мира и игроков

    # Отрисовка (упрощённо)
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(30)

client_socket.close()
pygame.quit()
