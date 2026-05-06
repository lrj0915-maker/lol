import re
import json

# Read the saved HTML
with open('C:/Users/Administrator/lol/lol-assistant/debug_full.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for the augment data pattern - it's in a large JSON array
# Let's find where it starts
start = html.find('[{"id":')
if start >= 0:
    print(f'Found at position {start}')
    # Try to find the matching closing bracket by counting braces
    depth = 0
    i = start
    while i < len(html):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    
    json_str = html[start:i+1]
    print(f'JSON length: {len(json_str)}')
    
    try:
        data = json.loads(json_str)
        print(f'Parsed {len(data)} items')
        print('First item:', json.dumps(data[0], indent=2)[:500])
    except Exception as e:
        print(f'Parse error: {e}')
        print('First 500 chars:', json_str[:500])
