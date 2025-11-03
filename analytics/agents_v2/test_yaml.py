import yaml
from pathlib import Path

# 경로
current_file = Path(__file__).resolve()
analytics_dir = current_file.parent.parent
playbook_dir = analytics_dir / 'playbooks'

print(f"Playbook dir: {playbook_dir}")
print(f"Exists: {playbook_dir.exists()}")

# 파일 직접 읽기
yaml_file = playbook_dir / 'base_playbook.yaml'
print(f"\nTrying to read: {yaml_file}")
print(f"File exists: {yaml_file.exists()}")

if yaml_file.exists():
    print(f"File size: {yaml_file.stat().st_size} bytes")
    
    # 내용 읽기
    print("\n--- File content (first 500 chars) ---")
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:500])
    
    print("\n--- Trying to parse YAML ---")
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        print("✓ Successfully parsed!")
        print(f"Keys: {list(data.keys())}")
        
        if 'strategies' in data:
            print(f"Strategies count: {len(data['strategies'])}")
        
    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        import traceback
        traceback.print_exc()
else:
    print("File does not exist!")

# analysis_patterns도 테스트
print("\n" + "="*60)
yaml_file2 = playbook_dir / 'analysis_patterns.yaml'
print(f"Trying to read: {yaml_file2}")
print(f"File exists: {yaml_file2.exists()}")

if yaml_file2.exists():
    print(f"File size: {yaml_file2.stat().st_size} bytes")
    
    print("\n--- Trying to parse YAML ---")
    try:
        with open(yaml_file2, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        print("✓ Successfully parsed!")
        print(f"Keys: {list(data.keys())}")
        
        if 'patterns' in data:
            print(f"Patterns count: {len(data['patterns'])}")
        
    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        import traceback
        traceback.print_exc()