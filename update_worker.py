"""Update index.html to use Cloudflare Worker proxy"""
import os

path = r'C:\Users\nora.bai\Documents\fund-dashboard\index.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add WORKER_URL constant after navSource
c = c.replace("var navSource = 'cache';",
    "var navSource = 'cache';\nvar WORKER_URL = 'https://hermes.1239737251.workers.dev';")

# 2. Add Worker proxy as first step in fetchFundNav
old_first = "  // 1. fundgz live API -- try first for real-time data\n  try {\n    const data = await jsonp(`https://fundgz.1234567.com.cn/js/${code}.js`, 5000);\n    if (data && data.gsz !== undefined) {\n      navSource = 'live';\n      return {nav:parseFloat(data.gsz)||0, navPrev:parseFloat(data.dwjz)||0, change:parseFloat(data.gszzl)||0, navDate:data.jzrq||''};\n    }\n  } catch(_) {}"

new_first = """  // 1. Cloudflare Worker proxy (bypasses corp firewall)
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
  // 2. fundgz live API (direct JSONP)
  try {
    const data = await jsonp(`https://fundgz.1234567.com.cn/js/${code}.js`, 5000);
    if (data && data.gsz !== undefined) {
      navSource = 'live';
      return {nav:parseFloat(data.gsz)||0, navPrev:parseFloat(data.dwjz)||0, change:parseFloat(data.gszzl)||0, navDate:data.jzrq||''};
    }
  } catch(_) {}"""

if old_first in c:
    c = c.replace(old_first, new_first)
    print("fetchFundNav updated")
else:
    print("WARNING: fetchFundNav pattern not found!")
    # Debug: find the actual pattern
    import re
    m = re.search(r'// 1\. fundgz live API', c)
    if m:
        print(f"Pattern found at position {m.start()}, line around: {repr(c[m.start():m.start()+200])}")

# 3. Add Worker proxy for index fetching
old_idx = """  // 2. Sina API via script tag
  try {
    const result = await new Promise((resolve) => {"""

new_idx = """  // 2. Cloudflare Worker proxy
  try {
    const resp = await fetch(WORKER_URL + '/index');
    const text = await resp.text();
    const lines = text.split('\\n');
    const nameMap = {'hq_str_s_sh000001':'\\u4e0a\\u8bc1\\u6307\\u6570','hq_str_s_sz399001':'\\u6df1\\u8bc1\\u6210\\u6307','hq_str_s_sz399006':'\\u521b\\u4e1a\\u677f\\u6307','hq_str_s_sh000688':'\\u79d1\\u521b50','hq_str_s_sh000300':'\\u6caa\\u6df1300','hq_str_s_sh000016':'\\u4e0a\\u8bc150','hq_str_s_sz399852':'\\u4e2d\\u8bc11000'};
    const indices = [];
    lines.forEach(function(line) {
      line = line.trim();
      if (!line || !line.includes('=')) return;
      const parts = line.split('=');
      const varName = parts[0].replace('var ','').trim();
      const val = parts[1].trim().replace(/"/g,'');
      const vals = val.split(',');
      const name = nameMap[varName];
      if (name) {
        indices.push({name: name, price: parseFloat(vals[1])||0, changeAmt: parseFloat(vals[2])||0, changePct: parseFloat(vals[3])||0});
      }
    });
    if (indices.length >= 6) return indices;
  } catch(_) {}
  // 3. Sina API via script tag
  try {
    const result = await new Promise((resolve) => {"""

if old_idx in c:
    c = c.replace(old_idx, new_idx)
    print("fetchIndices updated")
else:
    print("WARNING: fetchIndices pattern not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print(f"Done. File size: {len(c)} bytes")