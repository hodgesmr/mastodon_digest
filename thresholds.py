from enum import Enum


class Thresholds(Enum):
    LAX = 90
    NORMAL = 95
    STRICT = 98


def get_thresholds():
    return {i.name.lower(): i.value for i in Thresholds}
