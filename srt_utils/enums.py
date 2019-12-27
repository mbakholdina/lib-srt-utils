import enum


class AutoName(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


@enum.unique
class Status(AutoName):
    idle = enum.auto()
    running = enum.auto()