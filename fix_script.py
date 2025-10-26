import re

with open('borg_tools_scan.py', 'r') as f:
    content = f.read()

# Fix the broken f-string
content = re.sub(r'    print\(f"\n\'\nDone\. Projects scanned: \{len\(summaries\)\}"\)',
                r'    print(f"\nDone. Projects scanned: {len(summaries)}")',
                content)

# Replace the problematic print statements entirely
broken_block = '''    print(f"\n'
Done. Projects scanned: {len(summaries)}")
    print(f"- Wygenerowano: {root / 'BORG_INDEX.md'}")
    print(f"- Wygenerowano: borg_dashboard.csv, borg_dashboard.json (tu, gdzie uruchomiłeś)")
    print(f"- Każdy projekt ma: REPORT.md z TODO/AI Accel/Skills\n")'''

fixed_block = '''    print(f"\nDone. Projects scanned: {len(summaries)}")
    print(f"- Generated: {root / 'BORG_INDEX.md'}")
    print(f"- Generated: borg_dashboard.csv, borg_dashboard.json (in current directory)")
    print(f"- Each project has: REPORT.md with TODO/AI Accel/Skills\n")'''

content = content.replace(broken_block, fixed_block)

with open('borg_tools_scan.py', 'w') as f:
    f.write(content)

print("Fixed script saved")
