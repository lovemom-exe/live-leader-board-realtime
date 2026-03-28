import random
import csv
import time
import sys
import os
from typing import List, Dict
from benchmark_utils import generate_data, calculate_stats, print_stats
from rb_tree import RBTreeLeaderboard

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configuration
TOTAL_USERS = 2_000_000  # 2 triệu user
OPERATIONS_COUNT = 5000  # Số lượng operations để đo lường
TOP_K = 100
SIMULATION_DURATION_SEC = 5  # Thời gian mô phỏng realtime
CHURN_RATE = 0.3  # 30% users update per second

def format_time(seconds: float) -> str:
    """Format thời gian thành dạng dễ đọc"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {mins}m {secs:.2f}s"

def test_initialization(lb: RBTreeLeaderboard, data: List[tuple]):
    """Test khởi tạo với 2 triệu user"""
    print(f"\n{'='*60}")
    print(f"TEST 1: KHỞI TẠO VÀ INSERT {TOTAL_USERS:,} USERS")
    print(f"{'='*60}\n")
    
    start_init = time.perf_counter_ns()
    total_users = len(data)
    
    # Insert với progress tracking
    batch_size = 100000  # Hiển thị progress mỗi 100k users
    for i, (uid, score) in enumerate(data, 1):
        lb.insert(uid, score)
        if i % batch_size == 0:
            elapsed = (time.perf_counter_ns() - start_init) / 1e9
            rate = i / elapsed
            remaining = (total_users - i) / rate if rate > 0 else 0
            print(f"  Progress: {i:,}/{total_users:,} users ({i*100//total_users}%) | "
                  f"Elapsed: {format_time(elapsed)} | "
                  f"Rate: {rate:.0f} ops/s | "
                  f"ETA: {format_time(remaining)}")
    
    end_init = time.perf_counter_ns()
    init_time_s = (end_init - start_init) / 1e9
    init_time_us = (end_init - start_init) / 1000.0
    
    print(f"\n✓ Hoàn thành khởi tạo!")
    print(f"  Tổng thời gian: {init_time_s:.2f}s ({init_time_us:,.0f} us)")
    print(f"  Thời gian trung bình mỗi insert: {init_time_us / total_users:.4f} us")
    print(f"  Số lượng users trong tree: {len(lb):,}")
    print(f"  Tree size: {lb.root.size:,}")
    
    return {
        "InitTotal_us": init_time_us,
        "InitTotal_s": init_time_s,
        "AvgInsert_us": init_time_us / total_users
    }

def test_insert(lb: RBTreeLeaderboard):
    """Test insert operations"""
    print(f"\n{'='*60}")
    print(f"TEST 2: INSERT {OPERATIONS_COUNT:,} NEW USERS")
    print(f"{'='*60}\n")
    
    # Generate new unique users
    existing_users = set(lb.user_map.keys())
    new_data = []
    print(f"  Đang tạo {OPERATIONS_COUNT:,} users mới...")
    while len(new_data) < OPERATIONS_COUNT:
        user_id = random.randint(100000, 999999999)  # Expanded range for 2M users
        if user_id not in existing_users:
            existing_users.add(user_id)
            score = random.randint(0, 15000)
            new_data.append((user_id, score))
    
    insert_times = []
    print(f"  Đang insert {OPERATIONS_COUNT:,} users...")
    
    for i, (uid, score) in enumerate(new_data, 1):
        start = time.perf_counter_ns()
        lb.insert(uid, score)
        end = time.perf_counter_ns()
        insert_times.append(end - start)
        
        if i % 1000 == 0:
            print(f"    Inserted {i:,}/{OPERATIONS_COUNT:,} users...")
    
    insert_stats = calculate_stats(insert_times)
    print_stats("RBTree", "Insert", OPERATIONS_COUNT, insert_stats)
    
    return {
        "Insert_Avg_us": insert_stats["Average"],
        "Insert_Stdev_us": insert_stats["Stdev"],
        "Insert_P95_us": insert_stats["P95"],
        "Insert_P99_us": insert_stats["P99"],
        "Insert_P999_us": insert_stats["P99.9"]
    }

def test_search(lb: RBTreeLeaderboard, data: List[tuple]):
    """Test search operations"""
    print(f"\n{'='*60}")
    print(f"TEST 3: SEARCH {OPERATIONS_COUNT:,} USERS")
    print(f"{'='*60}\n")
    
    # Random sample từ existing users
    search_targets = random.sample(data, min(OPERATIONS_COUNT, len(data)))
    
    search_times = []
    print(f"  Đang search {len(search_targets):,} users...")
    
    for i, (uid, score) in enumerate(search_targets, 1):
        start = time.perf_counter_ns()
        rank = lb.search(uid, score)
        end = time.perf_counter_ns()
        search_times.append(end - start)
        
        if i % 1000 == 0:
            print(f"    Searched {i:,}/{len(search_targets):,} users...")
    
    search_stats = calculate_stats(search_times)
    print_stats("RBTree", "Search", len(search_targets), search_stats)
    
    return {
        "Search_Avg_us": search_stats["Average"],
        "Search_Stdev_us": search_stats["Stdev"],
        "Search_P95_us": search_stats["P95"],
        "Search_P99_us": search_stats["P99"],
        "Search_P999_us": search_stats["P99.9"]
    }

def test_update(lb: RBTreeLeaderboard, data: List[tuple]):
    """Test update operations"""
    print(f"\n{'='*60}")
    print(f"TEST 4: UPDATE {OPERATIONS_COUNT:,} USERS")
    print(f"{'='*60}\n")
    
    # Random sample để update
    update_targets = random.sample(data, min(OPERATIONS_COUNT, len(data)))
    
    update_times = []
    print(f"  Đang update {len(update_targets):,} users...")
    
    for i, (uid, _) in enumerate(update_targets, 1):
        new_score = random.randint(0, 15000)
        start = time.perf_counter_ns()
        lb.update(uid, new_score)
        end = time.perf_counter_ns()
        update_times.append(end - start)
        
        if i % 1000 == 0:
            print(f"    Updated {i:,}/{len(update_targets):,} users...")
    
    update_stats = calculate_stats(update_times)
    print_stats("RBTree", "Update", len(update_targets), update_stats)
    
    return {
        "Update_Avg_us": update_stats["Average"],
        "Update_Stdev_us": update_stats["Stdev"],
        "Update_P95_us": update_stats["P95"],
        "Update_P99_us": update_stats["P99"],
        "Update_P999_us": update_stats["P99.9"]
    }

def test_delete(lb: RBTreeLeaderboard, data: List[tuple]):
    """Test delete operations"""
    print(f"\n{'='*60}")
    print(f"TEST 5: DELETE {OPERATIONS_COUNT:,} USERS")
    print(f"{'='*60}\n")
    
    # Random sample để delete
    delete_targets = random.sample(data, min(OPERATIONS_COUNT, len(data)))
    
    delete_times = []
    print(f"  Đang delete {len(delete_targets):,} users...")
    
    for i, (uid, _) in enumerate(delete_targets, 1):
        start = time.perf_counter_ns()
        lb.delete(uid)
        end = time.perf_counter_ns()
        delete_times.append(end - start)
        
        if i % 1000 == 0:
            print(f"    Deleted {i:,}/{len(delete_targets):,} users...")
    
    delete_stats = calculate_stats(delete_times)
    print_stats("RBTree", "Delete", len(delete_targets), delete_stats)
    
    print(f"\n  Sau khi delete: {len(lb):,} users còn lại trong tree")
    
    return {
        "Delete_Avg_us": delete_stats["Average"],
        "Delete_Stdev_us": delete_stats["Stdev"],
        "Delete_P95_us": delete_stats["P95"],
        "Delete_P99_us": delete_stats["P99"],
        "Delete_P999_us": delete_stats["P99.9"]
    }

def test_top_k(lb: RBTreeLeaderboard):
    """Test top-k queries"""
    print(f"\n{'='*60}")
    print(f"TEST 6: TOP-{TOP_K} QUERIES ({OPERATIONS_COUNT:,} queries)")
    print(f"{'='*60}\n")
    
    topk_times = []
    print(f"  Đang thực hiện {OPERATIONS_COUNT:,} top-{TOP_K} queries...")
    
    for i in range(OPERATIONS_COUNT):
        start = time.perf_counter_ns()
        top_k_result = lb.top_k(TOP_K)
        end = time.perf_counter_ns()
        topk_times.append(end - start)
        
        if i % 1000 == 0 and i > 0:
            print(f"    Completed {i:,}/{OPERATIONS_COUNT:,} queries...")
        
        # Verify result
        if i == 0:
            print(f"\n  Top {min(TOP_K, len(top_k_result))} users (sample từ query đầu tiên):")
            for idx, (uid, score) in enumerate(top_k_result[:10], 1):
                print(f"    {idx}. User {uid}: {score} points")
            if len(top_k_result) > 10:
                print(f"    ... ({len(top_k_result) - 10} more)")
    
    topk_stats = calculate_stats(topk_times)
    print_stats("RBTree", f"Top-{TOP_K}", OPERATIONS_COUNT, topk_stats)
    
    return {
        "TopK_Avg_us": topk_stats["Average"],
        "TopK_Stdev_us": topk_stats["Stdev"],
        "TopK_P95_us": topk_stats["P95"],
        "TopK_P99_us": topk_stats["P99"],
        "TopK_P999_us": topk_stats["P99.9"]
    }

def test_realtime_simulation(lb: RBTreeLeaderboard, data: List[tuple]):
    """Test realtime simulation với workload"""
    print(f"\n{'='*60}")
    print(f"TEST 7: REALTIME SIMULATION ({SIMULATION_DURATION_SEC}s)")
    print(f"{'='*60}\n")
    
    n = len(lb)
    target_ops_per_sec = int(n * CHURN_RATE)
    
    print(f"  Target: {target_ops_per_sec:,} updates/s + {target_ops_per_sec:,} searches/s")
    print(f"  Simulation duration: {SIMULATION_DURATION_SEC}s\n")
    
    update_latencies = []
    search_latencies = []
    
    start_sim = time.time()
    iterations = 0
    
    while time.time() - start_sim < SIMULATION_DURATION_SEC:
        batch_updates = min(target_ops_per_sec, len(data))
        batch_searches = min(target_ops_per_sec, len(data))
        
        update_candidates = random.sample(data, batch_updates)
        search_candidates = random.sample(data, batch_searches)
        
        batch_start = time.perf_counter_ns()
        
        # Updates
        for uid, _ in update_candidates:
            new_score = random.randint(0, 15000)
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
        
        iterations += 1
        print(f"  Sec {iterations}: Processed {batch_updates:,} updates + {batch_searches:,} searches "
              f"in {batch_duration_sec:.4f}s")
        
        if time.time() - start_sim >= SIMULATION_DURATION_SEC:
            break
        
        if batch_duration_sec < 1.0:
            time.sleep(1.0 - batch_duration_sec)
        else:
            print(f"    WARNING: Falling behind! Batch took {batch_duration_sec:.4f}s")
    
    update_stats = calculate_stats(update_latencies)
    search_stats = calculate_stats(search_latencies)
    
    print_stats("RBTree", "Realtime Update", len(update_latencies), update_stats)
    print_stats("RBTree", "Realtime Search", len(search_latencies), search_stats)
    
    return {
        "Realtime_Update_Avg_us": update_stats["Average"],
        "Realtime_Update_P99_us": update_stats["P99"],
        "Realtime_Search_Avg_us": search_stats["Average"],
        "Realtime_Search_P99_us": search_stats["P99"],
        "Realtime_Ops_Processed": len(update_latencies) + len(search_latencies)
    }

def main():
    print("\n" + "="*60)
    print(f"BENCHMARK RED-BLACK TREE VỚI {TOTAL_USERS:,} USERS")
    print("="*60)
    
    # Khởi tạo
    lb = RBTreeLeaderboard()
    
    # Generate data
    print(f"\nĐang generate {TOTAL_USERS:,} users...")
    print("(Có thể mất vài phút...)\n")
    start_gen = time.time()
    data = generate_data(TOTAL_USERS)
    gen_time = time.time() - start_gen
    print(f"✓ Generated {len(data):,} users trong {format_time(gen_time)}\n")
    
    # Chạy các tests
    results = {}
    
    # Test 1: Initialization
    init_results = test_initialization(lb, data)
    results.update(init_results)
    
    # Test 2: Insert
    insert_results = test_insert(lb)
    results.update(insert_results)
    
    # Test 3: Search
    search_results = test_search(lb, data)
    results.update(search_results)
    
    # Test 4: Update
    update_results = test_update(lb, data)
    results.update(update_results)
    
    # Test 5: Top-K
    topk_results = test_top_k(lb)
    results.update(topk_results)
    
    # Test 6: Delete (chạy sau top-k để không ảnh hưởng)
    delete_results = test_delete(lb, data)
    results.update(delete_results)
    
    # Test 7: Realtime Simulation
    realtime_results = test_realtime_simulation(lb, data)
    results.update(realtime_results)
    
    # Tổng kết
    print(f"\n{'='*60}")
    print("TỔNG KẾT KẾT QUẢ")
    print(f"{'='*60}\n")
    print(f"Tổng số users test: {TOTAL_USERS:,}")
    print(f"Thời gian khởi tạo: {results.get('InitTotal_s', 0):.2f}s")
    print(f"\nInsert - Average: {results.get('Insert_Avg_us', 0):.4f} us | P99: {results.get('Insert_P99_us', 0):.4f} us")
    print(f"Search - Average: {results.get('Search_Avg_us', 0):.4f} us | P99: {results.get('Search_P99_us', 0):.4f} us")
    print(f"Update - Average: {results.get('Update_Avg_us', 0):.4f} us | P99: {results.get('Update_P99_us', 0):.4f} us")
    print(f"Delete - Average: {results.get('Delete_Avg_us', 0):.4f} us | P99: {results.get('Delete_P99_us', 0):.4f} us")
    print(f"Top-{TOP_K} - Average: {results.get('TopK_Avg_us', 0):.4f} us | P99: {results.get('TopK_P99_us', 0):.4f} us")
    
    # Save results to CSV
    csv_file = "rb_tree_2M_results.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results.keys()))
        writer.writeheader()
        writer.writerow(results)
    
    print(f"\n✓ Kết quả đã được lưu vào {csv_file}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

