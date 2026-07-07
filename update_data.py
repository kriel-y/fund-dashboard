#!/usr/bin/env python3
"""Update fund NAV and index data for the dashboard.
Fetches live data and writes precomputed_nav.json + precomputed_index.json.
Also embeds NAV data directly into index.html as PRECOMPUTED_NAV for offline use.
"""
import subprocess, json, re, sys, os
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

FUND_CODES = ['022122','021642','027575','008390','008163','020602','015896','025856','019827','008279','026685']

INDEX_MAP = {
    's_sh000001': '上证指数', 's_sz399001': '深证成指', 's_sz399006': '创业板指',
    's_sh000688': '科创50', 's_sh000300': '沪深300', 's_sh000016': '上证50',
    's_sz399852': '中证1000'
}

def fetch_with_curl(url, headers=None, decode='utf-8'):
    cmd = ['curl', '-s', url, '--max-time', '10']
    if headers:
        for k, v in headers.items():
            cmd += ['-H', f'{k}: {v}']
    r = subprocess.run(cmd, capture_output=True, timeout=15)
    data = r.stdout
    if decode == 'gbk':
        return data.decode('gbk', errors='replace')
    return data.decode('utf-8', errors='replace')

def fetch_fund_nav(code):
    """Fetch NAV via fundgz JSONP API"""
    try:
        text = fetch_with_curl(f'https://fundgz.1234567.com.cn/js/{code}.js', decode='gbk')
        # jsonpgz({"fundcode":"022122","name":"...","jzrq":"...","dwjz":"...","gsz":"...","gszzl":"...","gztime":"..."});
        m = re.search(r'jsonpgz\((\{.*?\})\)', text, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            return {
                'code': code,
                'nav': float(data.get('gsz', 0)) if data.get('gsz') else 0,
                'navPrev': float(data.get('dwjz', 0)) if data.get('dwjz') else 0,
                'change': float(data.get('gszzl', 0)) if data.get('gszzl') else 0,
                'navDate': data.get('jzrq', ''),
            }
    except Exception as e:
        print(f"  fund {code}: {e}", file=sys.stderr)
    return None

def fetch_indices():
    """Fetch index data from Sina API"""
    keys = ','.join(INDEX_MAP.keys())
    try:
        text = fetch_with_curl(f'https://hq.sinajs.cn/list={keys}',
                               headers={'Referer': 'https://finance.sina.com.cn/'},
                               decode='gbk')
        indices = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if '=' not in line:
                continue
            var_part = line.split('=', 1)
            var_name = var_part[0].replace('var ', '').strip()
            val = var_part[1].strip().strip('"')
            parts = val.split(',')
            name = INDEX_MAP.get(var_name, parts[0])
            try:
                indices.append({
                    'name': name,
                    'price': round(float(parts[1]), 2),
                    'changePct': round(float(parts[3]), 2),
                    'changeAmt': round(float(parts[2]), 2),
                })
            except (ValueError, IndexError):
                pass
        return indices if len(indices) >= 6 else None
    except Exception as e:
        print(f"  indices: {e}", file=sys.stderr)
    return None

def embed_nav_in_html(nav_data):
    """Replace PRECOMPUTED_NAV block in index.html with fresh data"""
    html_path = os.path.join(DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Build new PRECOMPUTED_NAV block
    lines = ['const PRECOMPUTED_NAV = {']
    for code in FUND_CODES:
        d = nav_data.get(code, {})
        lines.append(f'  "{code}":{{"code":"{code}","nav":{d.get("nav",0)},"navPrev":{d.get("navPrev",d.get("nav",0))},"change":{d.get("change",0)},"navDate":"{d.get("navDate","")}"}},')
    lines.append('};')
    new_block = '\n'.join(lines)

    # Replace old block
    pattern = r'const PRECOMPUTED_NAV = \{.*?\};'
    html = re.sub(pattern, new_block, html, flags=re.DOTALL)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Updated PRECOMPUTED_NAV in index.html")

def main():
    print(f"=== Fund Data Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # 1. Fetch fund NAVs
    print("Fetching fund NAVs...")
    nav_data = {}
    for code in FUND_CODES:
        result = fetch_fund_nav(code)
        if result:
            nav_data[code] = result
            print(f"  {code}: nav={result['nav']}, chg={result['change']}%")

    if nav_data:
        with open(os.path.join(DIR, 'precomputed_nav.json'), 'w', encoding='utf-8') as f:
            json.dump(nav_data, f, ensure_ascii=False)
        print(f"  Wrote precomputed_nav.json ({len(nav_data)} funds)")
        embed_nav_in_html(nav_data)
    else:
        print("  WARNING: No NAV data fetched!")

    # 2. Fetch indices
    print("Fetching indices...")
    indices = fetch_indices()
    if indices:
        with open(os.path.join(DIR, 'precomputed_index.json'), 'w', encoding='utf-8') as f:
            json.dump(indices, f, ensure_ascii=False)
        for idx in indices:
            print(f"  {idx['name']}: {idx['price']} ({idx['changePct']:+.2f}%)")
        print(f"  Wrote precomputed_index.json ({len(indices)} indices)")
    else:
        print("  WARNING: No index data fetched!")

    # 3. Git commit & push
    print("Committing and pushing...")
    subprocess.run(['git', 'add', 'precomputed_nav.json', 'precomputed_index.json', 'index.html'], cwd=DIR)
    r = subprocess.run(['git', 'commit', '-m', f'auto-update: {datetime.now().strftime("%Y-%m-%d %H:%M")}'], cwd=DIR, capture_output=True)
    if r.returncode == 0 or 'nothing to commit' in r.stdout.decode():
        subprocess.run(['git', 'push'], cwd=DIR, timeout=30)
        print("  Pushed to GitHub")
    else:
        print(f"  Commit skipped: {r.stdout.decode()}")

    print("=== Done ===")

if __name__ == '__main__':
    main()