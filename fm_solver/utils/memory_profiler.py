import tracemalloc
from typing import Any, Callable, ClassVar, Dict, Optional
from contextlib import ContextDecorator
from dataclasses import dataclass

from fm_solver.utils import config_utils


class MemoryProfilerError(Exception):
    """A custom exception used to report errors in use of MemoryProfiler class."""


@dataclass
class MemoryProfiler(ContextDecorator):
    """Memory profiler for objects using a class, context manager, or decorator."""

    memory_profilers: ClassVar[Dict[str, float]] = dict()
    name: Optional[str] = None
    message: str = ""
    text: str = "Memory: {:0.4f}"
    logger: Optional[Callable[[str], None]] = print
    enabled: bool = config_utils.MEMORYPROFILER_ENABLED

    def __post_init__(self) -> None:
        """Initialization: add sizer to dict of memory profilers."""
        if self.name:
            self.memory_profilers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new memory profiler"""
        self._start_memory = tracemalloc.start()

    def stop(self) -> float:
        """Stop the memory profiler, and report the memory consumed."""
        # Calculate memory usage
        _, memory_peak_usage = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()

        msg = f'{self.message} {self.text.format(memory_peak_usage)} B.'
        memory_peak_usage_kb = None
        memory_peak_usage_mb = None
        memory_peak_usage_gb = None
        if memory_peak_usage > 1e3:
            memory_peak_usage_kb = memory_peak_usage * 1e-3
            msg = f'{self.message} {self.text.format(memory_peak_usage_kb)} KB.'
            if memory_peak_usage_kb > 1e3:
                memory_peak_usage_mb = memory_peak_usage_kb * 1e-3
                msg = f'{self.message} {self.text.format(memory_peak_usage_mb)} MB.'
                if memory_peak_usage_mb > 1e3:
                    memory_peak_usage_gb = memory_peak_usage_mb * 1e-3
                    msg = f'{self.message} {self.text.format(memory_peak_usage_gb)} GB.'

        # Report elapsed time
        if self.logger:
            self.logger(msg)
        if self.name:
            self.memory_profilers[self.name] = memory_peak_usage

        return memory_peak_usage

    def __enter__(self) -> "MemoryProfiler":
        """Start a new memory profiler as a context manager."""
        if self.enabled:
            self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager memory profiler."""
        if self.enabled:
            self.stop()
