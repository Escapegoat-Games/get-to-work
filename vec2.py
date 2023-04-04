import math


def add(v1, v2):
    v1_x, v1_y = v1
    v2_x, v2_y = v2
    return (v1_x + v2_x, v1_y + v2_y)


def magnitude(v):
    v_x, v_y = v
    return math.sqrt(math.pow(v_x, 2) + math.pow(v_y, 2))


def scale(v, s):
    v_x, v_y = v
    return (s*v_x, s*v_y)


def normalize(v):
    m = magnitude(v)
    return scale(v, 1/m)
