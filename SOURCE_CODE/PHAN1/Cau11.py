import time
import random
import re
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

DB_FILE = "football.sqlite"
OUT_TABLE = "pl_stats_clean"
URL = "https://fbref.com/en/comps/9/2024-2025"
SS = "2024-2025-Premier-League-Stats"
STAT_PAGES = {
    "standard": ("stats", "stats_standard", "all_stats_standard"),
    "shooting": ("shooting", "stats_shooting", "all_stats_shooting"),
    "passing": ("passing", "stats_passing", "all_stats_passing"),
    "defense": ("defense", "stats_defense", "all_stats_defense"),
    "possession": ("possession", "stats_possession", "all_stats_possession"),
    "goalkeeping": ("keepers", "stats_keeper", "all_stats_keeper"),
}
MIN_MINUTES_THRESHOLD = 90
WAIT_SEC = 1.5


def build_driver():
    print("Khoi tao Chrome driver...")
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    return driver


def human_pause(a=0.7, b=1.6):
    time.sleep(random.uniform(a, b))


def db_file_short(p):
    return p.split("/")[-1].split("\\")[-1]


def extract_table_html_from_container(driver, container_id, expected_table_id):
    try:
        container = driver.find_element(By.ID, container_id)
        html = container.get_attribute("innerHTML")
        soup = BeautifulSoup(html, "lxml")
        direct_tbl = soup.find("table", id=expected_table_id)
        if direct_tbl:
            return str(direct_tbl)
        for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
            if expected_table_id in c:
                inner = BeautifulSoup(c, "lxml")
                tbl = inner.find("table", id=expected_table_id)
                if tbl:
                    return str(tbl)
        return None
    except Exception as e:
        print(f"[extract] Loi khi trich xuat bang {expected_table_id}: {e}")
        return None


def clean_nation_value(nation_text):
    if not nation_text:
        return "N/a"
    txt = str(nation_text).strip()
    if txt in ("", "N/a"):
        return "N/a"
    m = re.search(r"[A-Z]{2,3}", txt)
    return m.group() if m else txt


def parse_table_html(table_html, page_tag):
    REDUNDANT_COLUMNS_NON_STANDARD = {
        "ranker", "age", "position", "pos", "nationality", "nation", "birth_year", "born",
        "games", "games_starts",
        "minutes", "minutes_90s",
        "goals", "assists", "goals_assists", "goals_pens",
        "pens_made", "pens_att",
        "cards_yellow", "cards_red",
        "xg", "npxg", "xg_assist", "npxg_xg_assist",
        "progressive_carries", "progressive_passes", "progressive_passes_received",
        "matches"
    }

    rows = []
    soup = BeautifulSoup(table_html, "lxml")
    table = soup.find("table")
    if not table:
        return rows

    headers = []
    thead = table.find("thead")
    if thead:
        last_tr = thead.find_all("tr")[-1]
        for th in last_tr.find_all(["th", "td"]):
            headers.append(th.get("data-stat") or th.get_text(strip=True))

    tbody = table.find("tbody")
    if not tbody:
        return rows

    for tr in tbody.find_all("tr"):
        classes = tr.get("class") or []
        if "thead" in classes:
            continue
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue

        r = {}
        for idx, cell in enumerate(cells):
            key = headers[idx] if idx < len(headers) else f"col_{idx}"
            text = cell.get_text(strip=True)
            link = cell.find("a")
            href = link.get("href") if link else ""

            kl = key.lower()

            if kl == "player":
                r["player"] = text
                if href and href.startswith("/"):
                    r["player_link"] = "https://fbref.com" + href
                continue
            if kl in ("team", "squad"):
                r["club"] = text
                continue

            if page_tag == "standard":
                if kl in ("birth_year", "born"):
                    r["birth_year"] = text
                    continue
                if kl in ("nationality", "nation"):
                    r["nation"] = clean_nation_value(text)
                    continue
                if kl in ("position", "pos"):
                    r["position"] = text
                    continue
                r[key] = text
                continue

            if page_tag != "standard":
                if kl in REDUNDANT_COLUMNS_NON_STANDARD:
                    continue
                r[key] = text

        rows.append(r)
    return rows


def curate_keep_columns(columns):
    cols = list(columns)
    blacklist = {"id", "player", "club", "player_link", "age", "birth_year", "nation", "position"}
    keep = [c for c in cols if c not in blacklist]
    return keep


def write_sqlite(db_path, table_name, records):
    if not records:
        print("[SQLITE] Khong co ban ghi de luu.")
        return

    records_sorted = sorted(records, key=lambda x: x.get("player", "").lower())
    for idx, rec in enumerate(records_sorted, 1):
        rec["id"] = str(idx)

    all_cols = set()
    for r in records_sorted:
        all_cols.update(r.keys())

    if "player_link" in all_cols:
        all_cols.discard("player_link")

    rename_meta = {
        "standard__birth_year": "birth_year",
        "standard__nationality": "nation",
        "standard__position": "position",
        "standard__Age": "age"
    }

    for old, new in rename_meta.items():
        if old in all_cols:
            all_cols.discard(old)
            all_cols.add(new)

    head_cols = ["id", "player", "club", "age", "birth_year", "nation", "position"]
    head = [c for c in head_cols if c in all_cols]
    other_cols = [c for c in sorted(all_cols) if c not in head]
    cols = head + other_cols

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS [{table_name}];")
    cur.execute(f"CREATE TABLE [{table_name}] ({', '.join(f'[{c}] TEXT' for c in cols)});")

    batch = []
    for r in records_sorted:
        mapped = dict(r)

        for old, new in rename_meta.items():
            if old in mapped and (new not in mapped or mapped.get(new) in ("", None, "N/a")):
                mapped[new] = mapped.get(old)

        row = []
        for c in cols:
            val = mapped.get(c, "N/a")
            if val is None or str(val).strip() == "" or str(val).lower() in ("nan", "none"):
                val = "N/a"
            row.append(str(val))
        batch.append(tuple(row))

    placeholders = ", ".join(["?"] * len(cols))
    cur.executemany(f"INSERT INTO [{table_name}] VALUES ({placeholders});", batch)
    conn.commit()
    conn.close()
    print(f"[SQLITE] Da ghi {len(records_sorted)} ban ghi vao {db_file_short(db_path)} (bang {table_name})")


def filter_dataframe_by_minutes(df, threshold):
    print(f"\nLoc DataFrame cho cau thu > {threshold} phut...")
    all_keys = list(df.columns)

    minute_like = [k for k in all_keys if ("minute" in k.lower() or k.lower() in ("min", "mins")) and "standard__" in k]

    minute_like_sorted = sorted(minute_like, key=lambda s: (("90" in s) or ("per_90" in s) or ("90s" in s)))

    minute_col = None
    for c in minute_like_sorted:
        if not any(x in c.lower() for x in ("90", "per_90", "90s")):
            minute_col = c
            break

    if not minute_col:
        fallback_cols = [k for k in all_keys if
                         k.lower().endswith(("__min", "__minutes")) and "standard__" in k.lower()]
        if fallback_cols:
            minute_col = fallback_cols[0]
        else:
            print("[Warning] Khong tim thay cot 'minutes' phu hop. Bo qua loc.")
            return df

    print(f"Tim thay cot phut: {minute_col}")

    df[minute_col] = pd.to_numeric(
        df[minute_col].astype(str).str.replace(",", ""),
        errors="coerce"
    ).fillna(0)

    filtered_df = df[df[minute_col] > threshold].copy()
    print(f"Da loc tu {len(df)} hang xuong {len(filtered_df)} hang.")
    return filtered_df


def main():
    print("Bat dau FBref scraper (Chien luoc Pandas-Merge)...")
    driver = build_driver()

    list_of_dataframes = []
    standard_df = None

    try:
        for page_tag, (suffix, table_id, container_id) in STAT_PAGES.items():
            url = f"{URL}/{suffix}/{SS}"
            print(f"[{page_tag}] -> {url}")
            driver.get(url)

            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, container_id)))
            except TimeoutException:
                pass

            human_pause(WAIT_SEC, WAIT_SEC + 0.8)

            table_html = extract_table_html_from_container(driver, container_id, table_id)
            if not table_html:
                print(f"[{page_tag}] Khong tim thay bang: {table_id}")
                continue

            rows = parse_table_html(table_html, page_tag)
            print(f"[{page_tag}] parsed {len(rows)} rows")

            if not rows:
                continue
            page_df = pd.DataFrame(rows)

            if "squad" in page_df.columns:
                page_df = page_df.rename(columns={"squad": "club"})
            if "club" not in page_df.columns:
                page_df["club"] = ""

            id_cols = ["player", "club"]

            if page_tag == "standard":
                meta_cols = ["player_link", "birth_year", "nation", "position"]
                stat_cols = [c for c in page_df.columns if c not in id_cols + meta_cols]
                page_df = page_df.rename(columns={c: f"standard__{c}" for c in stat_cols})
                standard_df = page_df
            else:
                meta_cols = ["player_link"]
                stat_cols = [c for c in page_df.columns if c not in id_cols + meta_cols]
                page_df = page_df.rename(columns={c: f"{page_tag}__{c}" for c in stat_cols})
                if "player_link" in page_df.columns:
                    page_df = page_df.drop(columns=["player_link"])
                list_of_dataframes.append(page_df)

            human_pause(0.6, 1.2)

    finally:
        try:
            driver.quit()
            print("\nDa dong trinh duyet. Bat dau merge du lieu voi Pandas...")
        except Exception:
            pass

    if standard_df is None:
        print("Loi: Trang 'standard' bi loi. Khong the merge.")
        return

    master_df = standard_df

    for i, df_to_merge in enumerate(list_of_dataframes):
        print(f"Dang merge DataFrame {i + 1}/{len(list_of_dataframes)}...")
        master_df = pd.merge(
            master_df,
            df_to_merge,
            on=["player", "club"],
            how="outer"
        )

    master_df = filter_dataframe_by_minutes(master_df, MIN_MINUTES_THRESHOLD)
    if master_df.empty:
        print("Khong co cau thu nao vuot qua nguong phut. Ket thuc.")
        return

    master_df = master_df.fillna("N/a")
    master_df = master_df.loc[:, ~master_df.columns.duplicated()]

    rename_map = {
        "standard__birth_year": "birth_year",
        "standard__nationality": "nation",
        "standard__position": "position",
        "standard__Age": "age"
    }

    for old, new in rename_map.items():
        if old in master_df.columns and new not in master_df.columns:
            master_df[new] = master_df[old]

    keep_cols = curate_keep_columns(master_df.columns)
    ordered_cols = ["player", "club", "age", "birth_year", "nation", "position"]
    ordered = [c for c in ordered_cols if c in master_df.columns] + \
              [c for c in keep_cols if c not in ordered_cols]

    df_final = master_df.loc[:, [c for c in ordered if c in master_df.columns]]

    if "player_link" in df_final.columns:
        df_final = df_final.drop(columns=["player_link"])

    write_sqlite(DB_FILE, OUT_TABLE, df_final.to_dict(orient="records"))

    csv_file = DB_FILE.replace(".sqlite", ".csv")
    try:
        df_final.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"Da ghi CSV: {csv_file}")
    except Exception as e:
        print(f"Loi khi ghi CSV: {e}")


if __name__ == "__main__":
    main()