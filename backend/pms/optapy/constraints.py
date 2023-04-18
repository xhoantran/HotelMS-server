from optapy import constraint_provider
from optapy.constraint import ConstraintFactory, Joiners
from optapy.score import HardSoftScore  # noqa: F401

from .domain import Booking


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory):
    return [
        # Hard constraints
        room_conflict(constraint_factory),
        # Soft constraints are only implemented in the optapy-quickstarts code
    ]


def room_conflict(constraint_factory: ConstraintFactory):
    # A room can accommodate at most one booking at the same time.
    return (
        constraint_factory.for_each(Booking)
        .join(
            Booking,
            # ... in the same room ...
            Joiners.equal(lambda booking: booking.room),
            # ... and the pair is unique (different id, no reverse pairs) ...
            Joiners.less_than(lambda booking: booking.id),
        )
        .filter(lambda left, right: left.calculate_same_date(right) > 0)
        .penalize(
            "Room conflict",
            HardSoftScore.ONE_HARD,
            lambda left, right: left.calculate_same_date(right),
        )
    )
