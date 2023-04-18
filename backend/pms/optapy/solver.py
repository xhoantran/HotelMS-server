import optapy.config
from constraints import define_constraints
from optapy import solver_factory_create
from optapy.types import Duration  # noqa: F821

from .domain import Booking, Room, TimeTable


class Solver:
    def __init__(self, solver_config=None):
        if solver_config is None:
            solver_config = self.get_solver_config()
        self.solver = solver_factory_create(solver_config).buildSolver()

    def get_solver_config(self, duration: int = 30):
        return (
            optapy.config.solver.SolverConfig()
            .withEntityClasses(Booking)
            .withSolutionClass(TimeTable)
            .withConstraintProviderClass(define_constraints)
            .withTerminationSpentLimit(Duration.ofSeconds(duration))
        )

    def build_problem(self, hotel, start_date, end_date):
        room_list = [Room(1, "Room A"), Room(2, "Room B"), Room(3, "Room C")]
        booking_list = [
            Booking(1, 1, 3),
            Booking(2, 2, 3),
            Booking(3, 4, 6),
            Booking(4, 1, 2),
        ]
        return TimeTable(room_list, booking_list)

    def solve(self):
        return self.solver.solve(self.problem)
