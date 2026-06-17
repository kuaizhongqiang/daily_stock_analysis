"""Update AGENTS.md to remove references to deleted directories."""
with open('AGENTS.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove --serve/--serve-only lines
content = content.replace(
    'python main.py --serve\npython main.py --serve-only\nuvicorn server:app --reload --host 0.0.0.0 --port 8000\n',
    'python main.py --schedule\n'
)

# Remove Web/Desktop section
old_web = (
    '### Web / Desktop\n'
    '\n'
    '```bash\n'
    'cd apps/dsa-web\n'
    'npm ci\n'
    'npm run lint\n'
    'npm run build\n'
    '\n'
    'cd ../dsa-desktop\n'
    'npm install\n'
    'npm run build\n'
    '```'
)
new_web = (
    '### dsa CLI\n'
    '\n'
    '```bash\n'
    'pip install click\n'
    'dsa analyze 600519\n'
    'dsa resolve 茅台\n'
    'dsa submit 600519\n'
    'dsa status <job_id>\n'
    '```'
)
content = content.replace(old_web, new_web)

with open('AGENTS.md', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
