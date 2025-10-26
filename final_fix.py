with open('borg_tools_scan.py', 'r') as f:
    lines = f.readlines()

# Remove the broken lines (654-658) and replace with correct ones
new_lines = []
for i, line in enumerate(lines):
    if i+1 < 653 or i+1 > 658:  # Keep all lines except 654-658
        new_lines.append(line)
    elif i+1 == 653:  # After line 653, add the correct print statements
        new_lines.append(line)
        new_lines.append('    print(f"\\nDone. Projects scanned: {len(summaries)}")\n')
        new_lines.append('    print(f"- Generated: {root / \'BORG_INDEX.md\'}")\n')
        new_lines.append('    print(f"- Generated: borg_dashboard.csv, borg_dashboard.json (in current directory)")\n')
        new_lines.append('    print(f"- Each project has: REPORT.md with TODO/AI Accel/Skills\\n")\n')

with open('borg_tools_scan.py', 'w') as f:
    f.writelines(new_lines)

print("Final fix applied")
