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
