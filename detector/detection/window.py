def check(value: float, gt: float|None, for_seconds:int, now_streak:int) -> bool:
    if gt is not None:
        return value > gt and now_streak * 1 >= for_seconds
    return False
