"""Fix the fetchFundNav pattern matching"""
import re

path = r'C:\Users\nora.bai\Documents\fund-dashboard\index.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Find the exact text around "fundgz live API"
idx = c.find('fundgz live API')
if idx >= 0:
    chunk = c[idx:idx+500]
    print("Found at", idx)
    print(repr(chunk[:200]))
else:
    print("Not found!")
    
# Find using regex
m = re.search(r'// \d\. fundgz live API.*?try \{[\s\S]*?\} catch\(\_\) \{\}', c)
if m:
    print(f"Regex match: {m.start()}-{m.end()}")
    matched = m.group()
    print(repr(matched[:200]))
else:
    print("Regex also failed - trying simpler")
    # Try just matching the comment line
    m2 = re.search(r'// 1\. fundgz live API[\s\S]*?catch\(\_\) \{\}', c)
    if m2:
        print(f"Simple regex: {m2.start()}")
        print(repr(m2.group()[:200]))