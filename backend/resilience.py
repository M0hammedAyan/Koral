import time
import asyncio
from enum import Enum
from typing import Callable, Optional


class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, reset_timeout: int = 30):
        self.fail_threshold = fail_threshold
        self.reset_timeout = reset_timeout
        self.fail_count = 0
        self.state = State.CLOSED
        self.opened_at = 0

    def record_success(self):
        self.fail_count = 0
        self.state = State.CLOSED
        self.opened_at = 0

    def record_failure(self):
        self.fail_count += 1
        if self.fail_count >= self.fail_threshold:
            self.state = State.OPEN
            self.opened_at = time.time()

    def allow(self) -> bool:
        if self.state == State.CLOSED:
            return True
        if self.state == State.OPEN:
            if (time.time() - self.opened_at) > self.reset_timeout:
                self.state = State.HALF_OPEN
                return True
            return False
        return True


async def call_with_circuit(circuit: CircuitBreaker, func: Callable, *args, timeout: Optional[float] = None, **kwargs):
    if not circuit.allow():
        raise RuntimeError("circuit_open")

    try:
        if asyncio.iscoroutinefunction(func):
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        else:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(loop.run_in_executor(None, lambda: func(*args, **kwargs)), timeout=timeout)
    except Exception as e:
        circuit.record_failure()
        raise
    else:
        circuit.record_success()
        return result
