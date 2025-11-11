"""V6 로그 파일 분석"""
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

log_dir = Path("dashboard/logs/v6_chatbot")
log_files = sorted(log_dir.glob("v6_log_*.jsonl"))

if not log_files:
    print("No log files found")
    exit()

print(f"Found {len(log_files)} log files")
print("="*100)

all_logs = []
for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                all_logs.append(json.loads(line))
            except:
                pass

print(f"\nTotal logs: {len(all_logs)}")
print("="*100)

# 통계
complexities = Counter(log['complexity'] for log in all_logs)
viz_strategies = Counter(log['visualization_strategy'] for log in all_logs)

avg_duration = sum(log['total_duration'] for log in all_logs) / len(all_logs)
avg_queries = sum(log['total_queries'] for log in all_logs) / len(all_logs)

print("\n[Complexity Distribution]")
for comp, count in complexities.most_common():
    print(f"  {comp}: {count} ({count/len(all_logs)*100:.1f}%)")

print("\n[Visualization Strategy]")
for viz, count in viz_strategies.most_common():
    print(f"  {viz}: {count} ({count/len(all_logs)*100:.1f}%)")

print(f"\n[Average Stats]")
print(f"  Duration: {avg_duration:.2f}s")
print(f"  Queries per request: {avg_queries:.2f}")

# 최근 5개 상세
print("\n" + "="*100)
print("Recent 5 logs:")
print("="*100)

for log in all_logs[-5:]:
    print(f"\nTime: {log['timestamp']}")
    print(f"Query: {log['user_query'][:80]}")
    print(f"Complexity: {log['complexity']} | Queries: {log['total_queries']} (Success: {log['successful_queries']}) | Duration: {log['total_duration']:.2f}s")
    print(f"Visualization: {log['visualization_strategy']}")

    # 노드별 실행 시간
    if log.get('node_details'):
        print(f"Nodes: ", end="")
        nodes = [f"{n['node']}({n.get('duration', 0):.1f}s)" for n in log['node_details'] if n.get('duration')]
        print(" -> ".join(nodes))

    if log.get('error_info'):
        print(f"[ERROR] {log['error_info']}")
    print("-"*100)
