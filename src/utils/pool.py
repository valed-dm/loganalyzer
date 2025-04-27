from contextlib import contextmanager
import multiprocessing
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Generator


if TYPE_CHECKING:
    from multiprocessing.pool import Pool
else:
    Pool = ModuleType("Pool")


@contextmanager
def cpu_pool(workers: int = None) -> Generator[Pool, None, None]:
    """Context manager for a multiprocessing Pool with automatic cleanup.

    Creates a pool of worker processes for parallel execution and ensures proper
    cleanup (close and join) when the context is exited.

    Args:
        workers: Number of worker processes to create. If None (default), uses
            one less than the total CPU cores (but always at least 1).

    Yields:
        multiprocessing.Pool: The initialized Pool object ready for use.
    """
    if workers is None:
        workers = max(multiprocessing.cpu_count() - 1, 1)

    pool = multiprocessing.Pool(processes=workers)
    try:
        yield pool
    finally:
        pool.close()
        pool.join()
