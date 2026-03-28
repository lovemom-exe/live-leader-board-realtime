import random
import time
import math
import functools
from typing import List, Tuple, Dict, Any

def generate_data(n: int, max_score: int = 15000) -> List[Tuple[int, int]]:
    """
    Generates n entries of (userID, totalScore).
    userID is a 6-digit integer.
    totalScore is a random integer between 0 and max_score.
    """
    data = []
    seen_users = set()
    while len(data) < n:
        user_id = random.randint(100000, 999999)
        if user_id in seen_users:
            continue
        seen_users.add(user_id)
        score = random.randint(0, max_score)
        data.append((user_id, score))
    return data

def calculate_stats(times_ns: List[float]) -> Dict[str, float]:
    """
    Calculates Average, Stdev, P95, P99 from a list of durations in nanoseconds.
    Returns values in microseconds (us).
    """
    if not times_ns:
        return {
            "Average": 0.0,
            "Stdev": 0.0,
            "P95": 0.0,
            "P99": 0.0,
            "P99.9": 0.0
        }

    # Convert to microseconds
    times_us = [t / 1000.0 for t in times_ns]
    n = len(times_us)
    
    avg = sum(times_us) / n
    
    variance = sum((t - avg) ** 2 for t in times_us) / n
    stdev = math.sqrt(variance)
    
    sorted_times = sorted(times_us)
    p95 = sorted_times[int(0.95 * n)]
    p99 = sorted_times[int(0.99 * n)]
    p999 = sorted_times[int(0.999 * n)] if int(0.999 * n) < n else sorted_times[-1]

    return {
        "Average": avg,
        "Stdev": stdev,
        "P95": p95,
        "P99": p99,
        "P99.9": p999
    }

def print_stats(name: str, operation: str, n: int, stats: Dict[str, float]):
    print(f"{name} {operation} {n} elements:")
    print(f"Average : {stats['Average']:.4f} us")
    print(f"Stdev   : {stats['Stdev']:.4f} us")
    print(f"95%     : {stats['P95']:.4f} us")
    print(f"99%     : {stats['P99']:.4f} us")
    print(f"99.9%   : {stats['P99.9']:.4f} us")
    print("-" * 30)

class BenchmarkTimer:
    """
    Context manager to measure execution time of a block and append to a list.
    """
    def __init__(self, result_list: List[float]):
        self.result_list = result_list
        self.start = 0

    def __enter__(self):
        self.start = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.perf_counter_ns()
        self.result_list.append(end - self.start)

def benchmark_decorator(func):
    """
    A decorator that prints the execution time of the function.
    Useful for coarse-grained measurement or debugging.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter_ns()
        result = func(*args, **kwargs)
        end = time.perf_counter_ns()
        print(f"Function {func.__name__} took {(end - start) / 1000.0:.4f} us")
        return result
    return wrapper
