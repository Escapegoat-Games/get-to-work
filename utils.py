import os
import sys
import re


def argmin(args):
    best_min = None
    idx = -1
    for i, x in enumerate(args):
        if best_min == None:
            best_min = x
            idx = i
        elif x < best_min:
            best_min = x
            idx = i
    return idx


def parse_dat(text):
    lines = text.split("\n")
    header_data = {}
    if lines[0] != "---":
        raise Exception("start of header not found")
    last_idx = 1
    for idx, l in enumerate(lines[1:], 1):
        last_idx = idx
        if l == "---":
            break
        else:
            m = re.match(r"(\w+)\s*:\s*(.+)", l)
            header_data[m.group(1)] = m.group(2)
    data = lines[last_idx+1:]
    return header_data, data


def get_resource_path():
    try:
        return sys._MEIPASS
    except AttributeError:
        return os.getcwd()
