"""Fix index.html - add Cloudflare Worker proxy for fund NAV"""
import re, os

os.chdir(r'C:\Users\nora.bai\Documents\fund-dashboard')

with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add WORKER_URL constant
if 'var navSource' in c and 'var WORKER_URL' not in c:
    c = c.replace("var navSource = 'cache';",
                  "var navSource = 'cache';\nconst WORKER_URL = 'https://hermes.1239737251.workers.dev';")
    print("Added WORKER_URL")

# 2. Add Worker proxy for fund NAV
# Find by looking for the fundgz line
fundgz_comment = '// 1. fundgz live API'
if fundgz_comment in c:
    idx = c.find(fundgz_comment)
    # Find the end of this try block (after the first catch)
    end_idx = c.find('} catch(_) {}', idx) + len('} catch(_) {}')
    old_block = c[idx:end_idx]
    
    new_block = """  // 1. Cloudflare Worker proxy (bypasses corp firewall)
  try {
    const resp = await fetch(WORKER_URL + '/fund/' + code);
    const text = await resp.text();
    const m = text.match(/jsonpgz\(([\s\S]+)\)/);
    if (m) {
      const data = JSON.parse(m[1]);
      if (data && data.gsz !== undefined) {
        navSource = 'live';
        return {nav:parseFloat(data.gsz)||0, navPrev:parseFloat(data.dwjz)||0, change:parseFloat(data.gszzl)||0, navDate:data.jzrq||''};
      }
    }
  } catch(_) {}
""" + "  " + old_block.lstrip()

    # Actually simpler: just insert before the fundgz block
    # Replace the 1. comment to become 2.
    old_block2 = "  // 1. fundgz live API — try first for real-time data"
    new_block2 = """  // 1. Cloudflare Worker proxy (bypasses corp firewall)
  try {
    const resp = await fetch(WORKER_URL + '/fund/' + code);
    const text = await resp.text();
    const m = text.match(/jsonpgz\\(([\\s\\S]+)\\)/);
    if (m) {
      const data = JSON.parse(m[1]);
      if (data && data.gsz !== undefined) {
        navSource = 'live';
        return {nav:parseFloat(data.gsz)||0, navPrev:parseFloat(data.dwjz)||0, change:parseFloat(data.gszzl)||0, navDate:data.jzrq||''};
      }
    }
  } catch(_) {}
  
  // 2. fundgz direct JSONP (fallback)"""
    
    c = c.replace(old_block2, new_block2)
    print("Added Worker proxy for fund NAV")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done. Size:", len(c))
for term in ['WORKER_URL', 'Cloudflare Worker']:
    print(f"  {term}: {c.count(term)}")