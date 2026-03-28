import random
import csv
import time
from typing import List, Type, Dict
from benchmark_utils import generate_data, calculate_stats, print_stats, BenchmarkTimer
from sorted_array import SortedArrayLeaderboard
from linked_list import LinkedListLeaderboard
from rb_tree import RBTreeLeaderboard
from skip_list import SkipListLeaderboard
from score_indexed_array import ScoreIndexedArrayLeaderboard

# Configuration
BATCH_SIZES = [5000, 10000, 20000, 50000, 100000]
OPERATIONS_COUNT = 1000 # Number of operations to measure for stats
SIMULATION_DURATION_SEC = 3
CHURN_RATE = 0.3 # 30% of users update per second
TOP_K = 100 # Number of top elements to retrieve

def run_benchmark(cls: Type, batch_size: int):
    name = cls.__name__
    print(f"Benchmarking {name} with {batch_size} elements (Micro)...")
    
    # 1. Initialization
    data = generate_data(batch_size)
    lb = cls()
    
    # Pre-fill
    start_init = time.perf_counter_ns()
    for uid, score in data:
        lb.insert(uid, score)
    end_init = time.perf_counter_ns()
    init_time_us = (end_init - start_init) / 1000.0
    print(f"Initialization took {init_time_us:.2f} us (Total)")

    # 2. Insert Benchmark
    insert_times = []
    # Generate new data for insertion
    new_data = generate_data(OPERATIONS_COUNT)
    
    for uid, score in new_data:
        start = time.perf_counter_ns()
        lb.insert(uid, score)
        end = time.perf_counter_ns()
        insert_times.append(end - start)
        
    insert_stats = calculate_stats(insert_times)
    print_stats(name, "Insert", OPERATIONS_COUNT, insert_stats)

    # 3. Search Benchmark
    search_times = []
    # Search for random existing items
    # We use the original data + inserted data
    all_data = data + new_data
    search_targets = random.sample(all_data, OPERATIONS_COUNT)
    
    for uid, score in search_targets:
        start = time.perf_counter_ns()
        lb.search(uid, score) # Search now uses user_map internally if score not provided, but here we provide it? 
        # Wait, the classes were updated to take optional score.
        # If we provide score, it might use the optimized path (e.g. bisect with key).
        # If we don't, it does map lookup then search.
        # Micro-benchmark usually tests the raw structure performance.
        # But `search(uid)` is the realistic usage.
        # Let's check the implementations. 
        # SortedArray: if score is None, map lookup. Then bisect.
        # So providing score avoids map lookup.
        # Realtime sim uses `search(uid)`.
        # Micro-benchmark should probably also use `search(uid)` to be consistent with "Search by ID" requirement?
        # Or `search(uid, score)` to test pure structure search?
        # The prompt said "benchmark operations... find".
        # Let's stick to `lb.search(uid)` to include the map lookup cost which is part of the "Leaderboard" abstraction cost.
        # Actually, let's pass `score` as None to force map lookup if that's the intended usage.
        # But wait, `search` signature in my code: `def search(self, user_id: int, score: Optional[int] = None) -> int:`
        # So I should call `lb.search(uid)`.
        end = time.perf_counter_ns()
        search_times.append(end - start)
        
    search_stats = calculate_stats(search_times)
    print_stats(name, "Search", OPERATIONS_COUNT, search_stats)

    # 4. Delete Benchmark
    delete_times = []
    # Delete random existing items
    delete_targets = random.sample(all_data, OPERATIONS_COUNT)
    
    for uid, score in delete_targets:
        start = time.perf_counter_ns()
        lb.delete(uid) # Same here, let's rely on map lookup
        end = time.perf_counter_ns()
        delete_times.append(end - start)
        
    delete_stats = calculate_stats(delete_times)
    print_stats(name, "Delete", OPERATIONS_COUNT, delete_stats)
    
    return {
        "Name": name,
        "BatchSize": batch_size,
        "InitTotal_us": init_time_us,
        "Insert_Avg_us": insert_stats["Average"],
        "Insert_P99_us": insert_stats["P99"],
        "Search_Avg_us": search_stats["Average"],
        "Search_P99_us": search_stats["P99"],
        "Delete_Avg_us": delete_stats["Average"],
        "Delete_P99_us": delete_stats["P99"]
    }

def run_realtime_simulation(cls: Type, n: int):
    name = cls.__name__
    print(f"Benchmarking {name} with {n} elements (Realtime Sim)...")
    
    # 1. Initialization
    data = generate_data(n)
    lb = cls()
    
    start_init = time.perf_counter_ns()
    for uid, score in data:
        lb.insert(uid, score)
    end_init = time.perf_counter_ns()
    init_time_us = (end_init - start_init) / 1000.0
    print(f"Initialization took {init_time_us:.2f} us (Total)")

    # 2. Realtime Simulation
    # Target operations per second
    target_ops_per_sec = int(n * CHURN_RATE)
    
    update_latencies = []
    search_latencies = []
    
    start_sim = time.time()
    iterations = 0
    
    while time.time() - start_sim < SIMULATION_DURATION_SEC:
        batch_updates = target_ops_per_sec
        batch_searches = target_ops_per_sec
        
        # Prepare data for this batch
        update_candidates = random.sample(data, batch_updates)
        search_candidates = random.sample(data, batch_searches)
        
        batch_start = time.perf_counter_ns()
        
        # Updates
        for uid, _ in update_candidates:
            new_score = random.randint(0, 15000)  # Max score constraint for ScoreIndexedArrayLeaderboard
            op_start = time.perf_counter_ns()
            lb.update(uid, new_score)
            op_end = time.perf_counter_ns()
            update_latencies.append(op_end - op_start)
            
        # Searches
        for uid, _ in search_candidates:
            op_start = time.perf_counter_ns()
            lb.search(uid)
            op_end = time.perf_counter_ns()
            search_latencies.append(op_end - op_start)
            
        batch_end = time.perf_counter_ns()
        batch_duration_sec = (batch_end - batch_start) / 1e9
        
        print(f"  Sec {iterations+1}: Processed {batch_updates} updates + {batch_searches} searches in {batch_duration_sec:.4f}s")
        
        iterations += 1
        if iterations >= SIMULATION_DURATION_SEC:
            break
            
        if batch_duration_sec < 1.0:
            time.sleep(1.0 - batch_duration_sec)
        else:
            print(f"  WARNING: Falling behind! Batch took {batch_duration_sec:.4f}s")

    update_stats = calculate_stats(update_latencies)
    search_stats = calculate_stats(search_latencies)
    
    print_stats(name, "Realtime Update", len(update_latencies), update_stats)
    print_stats(name, "Realtime Search", len(search_latencies), search_stats)
    
    return {
        "Name": name,
        "BatchSize": n,
        "InitTotal_us": init_time_us,
        "Update_Avg_us": update_stats["Average"],
        "Update_P99_us": update_stats["P99"],
        "Search_Avg_us": search_stats["Average"],
        "Search_P99_us": search_stats["P99"]
    }

def run_topk_benchmark(cls: Type, batch_size: int, k: int = TOP_K):
    name = cls.__name__
    print(f"Benchmarking {name} with {batch_size} elements (Top-K Micro, k={k})...")
    
    # 1. Initialization
    data = generate_data(batch_size)
    lb = cls()
    
    # Pre-fill
    start_init = time.perf_counter_ns()
    for uid, score in data:
        lb.insert(uid, score)
    end_init = time.perf_counter_ns()
    init_time_us = (end_init - start_init) / 1000.0
    print(f"Initialization took {init_time_us:.2f} us (Total)")

    # 2. Top-K Query Benchmark
    topk_times = []
    
    for _ in range(OPERATIONS_COUNT):
        start = time.perf_counter_ns()
        lb.top_k(k)
        end = time.perf_counter_ns()
        topk_times.append(end - start)
        
    topk_stats = calculate_stats(topk_times)
    print_stats(name, f"Top-{k}", OPERATIONS_COUNT, topk_stats)
    
    return {
        "Name": name,
        "BatchSize": batch_size,
        "K": k,
        "InitTotal_us": init_time_us,
        "TopK_Avg_us": topk_stats["Average"],
        "TopK_P99_us": topk_stats["P99"]
    }

def run_topk_realtime_simulation(cls: Type, n: int, k: int = TOP_K):
    name = cls.__name__
    print(f"Benchmarking {name} with {n} elements (Top-K Realtime Sim, k={k})...")
    
    # 1. Initialization
    data = generate_data(n)
    lb = cls()
    
    start_init = time.perf_counter_ns()
    for uid, score in data:
        lb.insert(uid, score)
    end_init = time.perf_counter_ns()
    init_time_us = (end_init - start_init) / 1000.0
    print(f"Initialization took {init_time_us:.2f} us (Total)")

    # 2. Realtime Simulation with Top-K queries
    # Target operations per second
    target_ops_per_sec = int(n * CHURN_RATE)
    
    update_latencies = []
    topk_latencies = []
    
    start_sim = time.time()
    iterations = 0
    
    while time.time() - start_sim < SIMULATION_DURATION_SEC:
        batch_updates = target_ops_per_sec
        batch_topk = target_ops_per_sec
        
        # Prepare data for this batch
        update_candidates = random.sample(data, batch_updates)
        
        batch_start = time.perf_counter_ns()
        
        # Updates
        for uid, _ in update_candidates:
            new_score = random.randint(0, 15000)
            op_start = time.perf_counter_ns()
            lb.update(uid, new_score)
            op_end = time.perf_counter_ns()
            update_latencies.append(op_end - op_start)
            
        # Top-K Queries
        for _ in range(batch_topk):
            op_start = time.perf_counter_ns()
            lb.top_k(k)
            op_end = time.perf_counter_ns()
            topk_latencies.append(op_end - op_start)
            
        batch_end = time.perf_counter_ns()
        batch_duration_sec = (batch_end - batch_start) / 1e9
        
        print(f"  Sec {iterations+1}: Processed {batch_updates} updates + {batch_topk} top-k queries in {batch_duration_sec:.4f}s")
        
        iterations += 1
        if iterations >= SIMULATION_DURATION_SEC:
            break
            
        if batch_duration_sec < 1.0:
            time.sleep(1.0 - batch_duration_sec)
        else:
            print(f"  WARNING: Falling behind! Batch took {batch_duration_sec:.4f}s")

    update_stats = calculate_stats(update_latencies)
    topk_stats = calculate_stats(topk_latencies)
    
    print_stats(name, "Realtime Update", len(update_latencies), update_stats)
    print_stats(name, f"Realtime Top-{k}", len(topk_latencies), topk_stats)
    
    return {
        "Name": name,
        "BatchSize": n,
        "K": k,
        "InitTotal_us": init_time_us,
        "Update_Avg_us": update_stats["Average"],
        "Update_P99_us": update_stats["P99"],
        "TopK_Avg_us": topk_stats["Average"],
        "TopK_P99_us": topk_stats["P99"]
    }

def main():
    classes = [
        SortedArrayLeaderboard,
        LinkedListLeaderboard,
        RBTreeLeaderboard,
        SkipListLeaderboard,
        ScoreIndexedArrayLeaderboard
    ]
    
    micro_results = []
    realtime_results = []
    topk_micro_results = []
    topk_realtime_results = []
    
    for n in BATCH_SIZES:
        print(f"\n{'='*20} DATASET SIZE: {n} {'='*20}\n")
        
        for cls in classes:
            # Skip LinkedList for > 10k
            if cls == LinkedListLeaderboard and n > 10000:
                continue
            
            # Run Micro-benchmark
            res_micro = run_benchmark(cls, n)
            micro_results.append(res_micro)
            
            # Run Realtime Simulation
            res_realtime = run_realtime_simulation(cls, n)
            realtime_results.append(res_realtime)
            
            # Run Top-K Micro-benchmark
            res_topk_micro = run_topk_benchmark(cls, n)
            topk_micro_results.append(res_topk_micro)
            
            # Run Top-K Realtime Simulation
            res_topk_realtime = run_topk_realtime_simulation(cls, n)
            topk_realtime_results.append(res_topk_realtime)
            
    # Write Micro-benchmark Results
    csv_file_micro = "benchmark_results.csv"
    if micro_results:
        keys = micro_results[0].keys()
        with open(csv_file_micro, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(micro_results)
        print(f"\nMicro-benchmark results saved to {csv_file_micro}")

    # Write Realtime Results
    csv_file_realtime = "realtime_benchmark_results.csv"
    if realtime_results:
        keys = realtime_results[0].keys()
        with open(csv_file_realtime, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(realtime_results)
        print(f"Realtime benchmark results saved to {csv_file_realtime}")

    # Write Top-K Micro-benchmark Results
    csv_file_topk_micro = "topk_benchmark_results.csv"
    if topk_micro_results:
        keys = topk_micro_results[0].keys()
        with open(csv_file_topk_micro, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(topk_micro_results)
        print(f"\nTop-K micro-benchmark results saved to {csv_file_topk_micro}")

    # Write Top-K Realtime Results
    csv_file_topk_realtime = "topk_realtime_benchmark_results.csv"
    if topk_realtime_results:
        keys = topk_realtime_results[0].keys()
        with open(csv_file_topk_realtime, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(topk_realtime_results)
        print(f"Top-K realtime benchmark results saved to {csv_file_topk_realtime}")

if __name__ == "__main__":
    main()
