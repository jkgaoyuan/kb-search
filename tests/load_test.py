import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import random

BASE_URL = "http://localhost:8000"


def search_query(q):
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/search", params={"q": q, "page_size": 20}, timeout=10)
        duration = time.time() - start
        return duration, resp.status_code
    except Exception as e:
        return time.time() - start, 0


def suggest_query(q):
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/search/suggest", params={"q": q}, timeout=5)
        duration = time.time() - start
        return duration, resp.status_code
    except Exception as e:
        return time.time() - start, 0


def run_load_test(func, queries, concurrency=20, total=200):
    """运行压测

    Args:
        func: 请求函数
        queries: 查询词列表
        concurrency: 并发数
        total: 总请求数
    """
    durations = []
    errors = 0
    success = 0

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(total):
            q = random.choice(queries)
            futures.append(executor.submit(func, q))

        for future in as_completed(futures):
            duration, status = future.result()
            durations.append(duration)
            if status == 200:
                success += 1
            else:
                errors += 1

    durations.sort()
    p50 = durations[int(len(durations) * 0.5)]
    p95 = durations[int(len(durations) * 0.95)]
    p99 = durations[int(len(durations) * 0.99)]
    avg = sum(durations) / len(durations)

    print(f"\n=== 压测结果 ===")
    print(f"并发数: {concurrency}")
    print(f"总请求: {total}")
    print(f"成功: {success} ({success/total*100:.1f}%)")
    print(f"失败: {errors} ({errors/total*100:.1f}%)")
    print(f"平均延迟: {avg*1000:.2f} ms")
    print(f"P50: {p50*1000:.2f} ms")
    print(f"P95: {p95*1000:.2f} ms")
    print(f"P99: {p99*1000:.2f} ms")
    print(f"最大延迟: {max(durations)*1000:.2f} ms")

    # 验收标准
    if p95 < 2.0:
        print("✅ P95 < 2s，通过验收标准")
    else:
        print("❌ P95 >= 2s，未通过验收标准")


if __name__ == "__main__":
    # 测试搜索
    search_queries = [
        "Python", "部署", "Docker", "Kubernetes", "FastAPI",
        "数据库", "前端", "后端", "测试", "监控",
        "日志", "Redis", "PostgreSQL", "Celery", "Vue"
    ]
    print("\n--- 搜索压测 (20并发, 200请求) ---")
    run_load_test(search_query, search_queries, concurrency=20, total=200)

    # 测试自动补全
    suggest_prefixes = ["Py", "Do", "Kub", "Fas", "Red", "Post", "V"]
    print("\n--- 自动补全压测 (20并发, 200请求) ---")
    run_load_test(suggest_query, suggest_prefixes, concurrency=20, total=200)
