import tracemalloc
from typing import Any, Callable, ClassVar, Dict, Optional
from contextlib import ContextDecorator
from dataclasses import dataclass

import objsize

from fm_solver.utils import config_utils


class SizerError(Exception):
    """A custom exception used to report errors in use of Sizer class."""


@dataclass
class Sizer(ContextDecorator):
    """Memory profiler for objects using a class, context manager, or decorator."""

    sizers: ClassVar[Dict[str, float]] = dict()
    name: Optional[str] = None
    message: str = ""
    text: str = "Memory: {:0.4f}"
    logger: Optional[Callable[[str], None]] = print
    enabled: bool = config_utils.SIZER_ENABLED

    def __post_init__(self) -> None:
        """Initialization: add sizer to dict of sizers."""
        if self.name:
            self.sizers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new sizer"""
        self._start_memory = tracemalloc.start()

    def stop(self) -> float:
        """Stop the sizer, and report the memory consumed."""
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
            self.sizers[self.name] += memory_peak_usage

        return memory_peak_usage

    def __enter__(self) -> "Sizer":
        """Start a new sizer as a context manager."""
        if self.enabled:
            self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager sizer."""
        if self.enabled:
            self.stop()

    @staticmethod
    def get_size_of(object: Any) -> int:
        """Return the size of any object including all its contents in bytes."""
        return objsize.get_deep_size(object)

    @staticmethod
    def size_of(object: Any, logger: Optional[Callable[[str], None]] = print, message: str = "", text: str = "Memory: {:0.4f}") -> None:
        """Log the size of any object including all its contents."""
        size = objsize.get_deep_size(object)
        msg = f'{message} {text.format(size)} B.'
        size_kb = None
        size_mb = None
        size_gb = None
        if size > 1e3:
            size_kb = size * 1e-3
            msg = f'{message} {text.format(size_kb)} KB.'
            if size_kb > 1e3:
                size_mb = size_kb * 1e-3
                msg = f'{message} {text.format(size_mb)} MB.'
                if size_mb > 1e3:
                    size_gb = size_mb * 1e-3
                    msg = f'{message} {text.format(size_gb)} GB.'
        logger(msg) 
