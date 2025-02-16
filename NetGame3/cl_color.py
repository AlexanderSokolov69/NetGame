#!/usr/bin/env python3
# coding:utf-8
import colorsys
import random


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

