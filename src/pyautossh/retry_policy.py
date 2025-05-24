import time
from typing import Callable

class RetryPolicy:
    """
    Encapsulates retry logic with an initial delay and optional backoff.

    Parameters
    ----------
    max_attempts : int | None
        Maximum number of times to attempt the function. None for infinite retries.
    delay : float
        Initial delay between attempts in seconds.
    backoff : float, optional
        Multiplier applied to the delay after each failed attempt. Default is 1.0.
    """

    def __init__(self, max_attempts: int | None, delay: float, backoff: float = 1.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff

    def call(self, fn: Callable[[], bool]) -> bool:
        """
        Attempt to call a function until it returns True or max attempts are reached.

        Parameters
        ----------
        fn : Callable[[], bool]
            Function to call. Should return True on success, False otherwise.

        Returns
        -------
        bool
            True if fn returned True within allowed attempts; False otherwise.
        """
        attempts = 0
        current_delay = self.delay

        while self.max_attempts is None or attempts < self.max_attempts:
            attempts += 1
            if fn():
                return True

            if self.max_attempts is not None and attempts >= self.max_attempts:
                break

            time.sleep(current_delay)
            current_delay *= self.backoff

        return False
