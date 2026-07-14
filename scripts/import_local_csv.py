"""
Import ALL 30 CSV fields into daily_kline.
Fix: ts_code broadcast + trade_date as TEXT.
"""
import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

CSV_DIR = "D:/Users/pml/Desktop/train/股票全量数据（更至20260703）/股票全量数据"
DB_PATH = os.getenv("DB_PATH", "data/stock_data.db")
START_DATE = "20230924"

# (csv_idx, db_col_name, sql_type)
COLS = [
    (2,  'trade_date',       'TEXT'),
    (3,  'open',             'REAL'),
    (4,  'high',             'REAL'),
    (5,  'low',              'REAL'),
    (6,  'close',            'REAL'),
    (7,  'prev_close',       'REAL'),
    (8,  'change_amt',       'REAL'),
    (9,  'pct_chg',          'REAL'),
    (10, 'vol',              'REAL'),
    (11, 'amount',           'REAL'),
    (12, 'turnover',         'REAL'),
    (13, 'turnover_float',   'REAL'),
    (14, 'vol_ratio',        'REAL'),
    (15, 'pe',               'REAL'),
    (16, 'pe_ttm',           'REAL'),
    (17, 'pb',               'REAL'),
    (18, 'ps',               'REAL'),
    (19, 'pcf_ttm',          'REAL'),
    (20, 'div_yield',        'REAL'),
    (21, 'div_yield_ttm',    'REAL'),
    (22, 'total_shares',     'REAL'),
    (23, 'float_shares',     'REAL'),
    (24, 'free_float_shares','REAL'),
    (25, 'market_cap',       'REAL'),
    (26, 'float_market_cap', 'REAL'),
    (27, 'vwap',             'REAL'),
    (28, 'limit_up_price',   'REAL'),
    (29, 'limit_down_price', 'REAL'),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Dropping old tables...")
cur.execute("DROP TABLE IF EXISTS daily_kline")
cur.execute("DROP TABLE IF EXISTS stock_basic")

col_defs = ",\n    ".join([f"{name} {dtype}" for _, name, dtype in COLS])
cur.execute(f"""
CREATE TABLE daily_kline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_code TEXT,
    {col_defs},
    is_limit_up INTEGER DEFAULT 0,
    is_limit_down INTEGER DEFAULT 0
)
""")
cur.execute("CREATE INDEX idx_dk ON daily_kline(ts_code, trade_date DESC)")

cur.execute("""CREATE TABLE stock_basic (
    ts_code TEXT PRIMARY KEY, name TEXT, area TEXT,
    industry TEXT, market TEXT, list_date TEXT, is_hs TEXT)""")
conn.commit()
print("Tables recreated (trade_date as TEXT).")

files = sorted(Path(CSV_DIR).glob("*.csv"))
print(f"Found {len(files)} CSV files. Filter: >= {START_DATE}")

t0 = datetime.now()
total_rows = 0
total_files = 0
errors = []

for i, f in enumerate(files):
    ts_code = f.stem
    try:
        df = pd.read_csv(f, encoding='utf-8-sig')
        if df.empty or len(df.columns) < 30:
            continue

        # Date filter
        date_raw = pd.to_numeric(df.iloc[:, 2], errors='coerce')
        mask = date_raw.notna() & (date_raw.astype(int).astype(str) >= START_DATE)
        df = df[mask].copy()
        if df.empty:
            continue

        n = len(df)

        # Build output DataFrame — set Series columns FIRST, then scalar
        out = pd.DataFrame()
        # trade_date: int -> str to avoid float
        out['trade_date'] = pd.to_numeric(df.iloc[:, 2], errors='coerce').astype('Int64').astype(str)

        for idx, name, _ in COLS:
            if name == 'trade_date':
                continue
            out[name] = pd.to_numeric(df.iloc[:, idx], errors='coerce')

        # NOW set scalar ts_code (DataFrame already has n rows)
        out['ts_code'] = ts_code

        # Limit flags
        c = out['close']
        lu = out['limit_up_price']
        ld = out['limit_down_price']
        out['is_limit_up'] = ((c.notna()) & (lu.notna()) & (c >= lu - 0.005)).astype(int)
        out['is_limit_down'] = ((c.notna()) & (ld.notna()) & (c <= ld + 0.005)).astype(int)

        # Drop invalid rows
        out = out.dropna(subset=['open', 'high', 'low', 'close', 'vol'])
        if out.empty:
            continue

        # Reorder columns to match table (ts_code first)
        col_order = ['ts_code'] + [name for _, name, _ in COLS] + ['is_limit_up', 'is_limit_down']
        out = out[col_order]

        out.to_sql('daily_kline', conn, if_exists='append', index=False)
        total_rows += len(out)
        total_files += 1

        # stock_basic
        name_val = str(df.iloc[0, 1])
        mkt = "主板" if ts_code[0] in '06' else "创业板" if ts_code[0] == '3' else "主板"
        cur.execute("INSERT OR IGNORE INTO stock_basic (ts_code,name,market) VALUES (?,?,?)",
                     (ts_code, name_val, mkt))

        if (i + 1) % 500 == 0:
            conn.commit()
            elapsed = (datetime.now() - t0).total_seconds()
            rate = total_rows / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{len(files)} files, {total_files} imported, {total_rows:,} rows, {elapsed:.0f}s, {rate:.0f} r/s]")

    except Exception as e:
        errors.append(f"{ts_code}: {type(e).__name__}: {str(e)[:60]}")
        if len(errors) <= 3:
            print(f"  ERROR {ts_code}: {e}")

conn.commit()

cur.execute(
    "INSERT INTO sync_log (data_type, ts_code, last_date, status, message) VALUES (?,?,?,?,?)",
    ("daily_kline", "ALL", datetime.now().strftime("%Y-%m-%d"), "success",
     f"local_csv_full30: {total_files} stocks, {total_rows} rows, since {START_DATE}")
)
conn.commit()

elapsed = (datetime.now() - t0).total_seconds()
cur.execute("SELECT COUNT(DISTINCT ts_code), COUNT(*), MIN(trade_date), MAX(trade_date) FROM daily_kline")
s, t, mn, mx = cur.fetchone()
print(f"\n=== DONE ===")
print(f"  Stocks: {total_files}/{len(files)}")
print(f"  Rows:   {total_rows:,}")
print(f"  Errors: {len(errors)}")
print(f"  Time:   {elapsed:.0f}s ({total_rows/elapsed:.0f} r/s)")
print(f"  DB: {s} stocks, {t:,} rows, {mn} ~ {mx}")

# Verify
cur.execute("SELECT ts_code, trade_date FROM daily_kline LIMIT 3")
print(f"\n  Sample: {[(r[0],r[1]) for r in cur.fetchall()]}")

cur.execute("SELECT COUNT(*) FROM daily_kline WHERE ts_code='600487.SH'")
cnt = cur.fetchone()[0]
print(f"  600487.SH: {cnt} rows")

cur.execute("""SELECT trade_date,open,high,low,close,prev_close,change_amt,pct_chg,vol,amount,
               turnover,turnover_float,vol_ratio,pe,pe_ttm,pb,ps,pcf_ttm,div_yield,div_yield_ttm,
               total_shares,float_shares,free_float_shares,market_cap,float_market_cap,vwap,
               limit_up_price,limit_down_price,is_limit_up,is_limit_down
               FROM daily_kline WHERE ts_code='600487.SH' ORDER BY trade_date DESC LIMIT 1""")
row = cur.fetchone()
if row:
    labels = ['date','open','high','low','close','prev_close','chg','pct','vol','amt','turnover','turn_float','vr','pe','pe_ttm','pb','ps','pcf','div','div_ttm','total_sh','float_sh','free_sh','mcap','float_mcap','vwap','lim_up','lim_dn','is_up','is_dn']
    print(f"\n  600487.SH latest:")
    for d, v in zip(labels, row):
        print(f"    {d:14s} = {v}")

conn.close()
