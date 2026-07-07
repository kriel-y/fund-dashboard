#!/usr/bin/env python3
"""Update market index data for the dashboard. Fetches from Sina API (works on most networks)."""
import subprocess, json, re, sys, os
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

INDEX_MAP = {
    's_sh000001': '上证指数', 's_sz399001': '深证成指', 's_sz399006': '创业板指',
    's_sh000688': '科创50', 's_sh000300': '沪深300', 's_sh000016': '上证50',
    's_sz399852': '中证1000'
}

def main():
    print(f"Index update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Fetch from Sina
    keys = ','.join(INDEX_MAP.keys())
    r = subprocess.run(
        ['curl', '-s', f'https://hq.sinajs.cn/list={keys}',
         '-H', 'Referer: https://finance.sina.com.cn/', '--max-time', '10'],
        capture_output=True, timeout=15
    )
    text = r.stdout.decode('gbk', errors='replace')

    indices = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if '=' not in line: continue
        var_part = line.split('=', 1)
        var_name = var_part[0].replace('var ', '').strip()
        val = var_part[1].strip().strip('"')
        parts = val.split(',')
        name = INDEX_MAP.get(var_name, parts[0])
        try:
            indices.append({
                'name': name, 'price': round(float(parts[1]), 2),
                'changePct': round(float(parts[3]), 2), 'changeAmt': round(float(parts[2]), 2),
            })
        except: pass

    if len(indices) < 6:
        print(f"ERROR: Only got {len(indices)} indices, expected 7")
        sys.exit(1)

    for idx in indices:
        print(f"  {idx['name']}: {idx['price']} ({idx['changePct']:+.2f}%)")

    # Write JSON
    path = os.path.join(DIR, 'precomputed_index.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(indices, f, ensure_ascii=False)

    # Git push
    subprocess.run(['git', 'add', 'precomputed_index.json'], cwd=DIR)
    r = subprocess.run(['git', 'commit', '-m', f'index: {datetime.now().strftime("%m-%d %H:%M")}'], cwd=DIR, capture_output=True)
    msg = r.stdout.decode()
    if 'nothing to commit' in msg:
        print("No changes to commit")
    else:
        subprocess.run(['git', 'push'], cwd=DIR, timeout=30)
        print("Pushed to GitHub")

    print("Done")

if __name__ == '__main__':
    main()