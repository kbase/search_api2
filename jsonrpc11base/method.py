from typing import Callable
import time


class Method(object):
    """
    Method function handler, and any other metadata we may need in the future
    """
    method_implementation: Callable
    call_count: int
    cumulative_call_time: float
    error_count: int

    def __init__(self, method: Callable):
        self.method_implementation = method
        self.call_count = 0
        self.cumulative_call_time = 0
        self.error_count = 0

    def call(self, params, options):
        self.call_count += 1
        call_started = time.time()
        try:
            if params is None:
                result = self.method_implementation(options)
            else:
                result = self.method_implementation(params, options)
            self.cumulative_call_time = time.time() - call_started
            return result
        except Exception as e:
            self.error_count = 0
            raise e
