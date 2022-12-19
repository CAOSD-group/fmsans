from typing import Any, Callable, Optional

import objsize

from fm_solver.utils import config_utils


def getsizeof(object: Any, logger: Optional[Callable[[str], None]] = print, message: str = "", text: str = "Memory: {:0.4f}") -> float:
    """Log the size of any object including all its contents in bytes."""
    if config_utils.SIZER_ENABLED:
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
        if logger:
            logger(msg) 
        return size
    return 0
