from optapy import (
    planning_entity,
    planning_entity_collection_property,
    planning_id,
    planning_score,
    planning_solution,
    planning_variable,
    problem_fact,
    problem_fact_collection_property,
    value_range_provider,
)
from optapy.score import HardSoftScore  # noqa: F401


@problem_fact
class Room:
    def __init__(self, id, number):
        self.id = id
        self.number = number

    @planning_id
    def get_id(self):
        return self.id

    def __str__(self):
        return f"Room(id={self.id}, number={self.number})"


@planning_entity
class Booking:
    def __init__(self, id, start_date, end_date, room=None):
        self.id = id
        self.start_date = start_date
        self.end_date = end_date
        self.room = room

    @planning_id
    def get_id(self):
        return self.id

    @planning_variable(Room, ["roomRange"])
    def get_room(self):
        return self.room

    def set_room(self, new_room):
        self.room = new_room

    def calculate_same_date(self, other):
        first_date = max(other.start_date, self.start_date)
        last_date = min(other.end_date, self.end_date)
        return max(0, last_date - first_date + 1)

    def __str__(self):
        return (
            f"Booking("
            f"id={self.id}, "
            f"start_date={self.start_date}, "
            f"end_date={self.end_date}, "
            f"room={self.room}, "
            f")"
        )


def format_list(a_list):
    return ",\\n".join(map(str, a_list))


@planning_solution
class TimeTable:
    def __init__(self, room_list, booking_list, score=None):
        self.room_list = room_list
        self.booking_list = booking_list
        self.score = score

    @problem_fact_collection_property(Room)
    @value_range_provider("roomRange")
    def get_room_list(self):
        return self.room_list

    @planning_entity_collection_property(Booking)
    def get_booking_list(self):
        return self.booking_list

    @planning_score(HardSoftScore)
    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score

    def __str__(self):
        return (
            f"TimeTable("
            f"room_list={format_list(self.room_list)},\\n"
            f"booking_list={format_list(self.booking_list)},\\n"
            f"score={str(self.score.toString()) if self.score is not None else 'None'}"
            f")"
        )
