import time
from typing import Any, Callable, ClassVar, Dict, Optional
from contextlib import ContextDecorator
from dataclasses import dataclass, field

from fm_solver.utils import config_utils


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class."""


@dataclass
class Timer(ContextDecorator):
    """Time your code using a class, context manager, or decorator."""

    timers: ClassVar[Dict[str, float]] = dict()
    name: Optional[str] = None
    message: str = ""
    text: str = "Elapsed time: {:0.4f} s."
    logger: Optional[Callable[[str], None]] = print
    _start_time: Optional[float] = field(default=None, init=False, repr=False)
    enabled: bool = config_utils.TIMER_ENABLED

    def __post_init__(self) -> None:
        """Initialization: add timer to dict of timers."""
        if self.name:
            self.timers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it.")

        self._start_time = time.perf_counter_ns()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time."""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it.")

        # Calculate elapsed time
        elapsed_time = (time.perf_counter_ns() - self._start_time) * 1e-9
        self._start_time = None

        msg = f'{self.message} {self.text.format(elapsed_time)}'

        # Report elapsed time
        if self.logger:
            self.logger(msg)
        if self.name:
            self.timers[self.name] += elapsed_time

        return elapsed_time

    def __enter__(self) -> "Timer":
        """Start a new timer as a context manager."""
        if self.enabled:
            self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager timer."""
        if self.enabled:
            self.stop()