import sys
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from unidecode import unidecode
import re
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_FILE = "football.sqlite"
STATS_TABLE = "pl_stats_clean"
TARGET_TABLE = "player_transfers"
CSV_OUTPUT_FILE = "football_transfers.csv"
BASE_URL = "https://www.footballtransfers.com/en/players/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class TransferScraper:
    def __init__(self, db_file, stats_table, target_table, csv_output):
        self.db_file = db_file
        self.stats_table = stats_table
        self.target_table = target_table
        self.csv_output = csv_output

        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        self.players_to_scrape = []
        self.results = []

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(f"DROP TABLE IF EXISTS {self.target_table};")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.target_table}(
                    player TEXT PRIMARY KEY,
                    etv_value TEXT,
                    club_on_profile TEXT,
                    last_update TEXT
                );
            """)
        print(f"✅ Table {self.target_table} has been reset in {self.db_file}")

    def _get_players(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                limit_query = "LIMIT 50"

                query = f"SELECT DISTINCT player FROM [{self.stats_table}] {limit_query}"
                df = conn.execute(query).fetchall()

                self.players_to_scrape = [x[0] for x in df]

            if limit_query:
                print(f"📋 TEST MODE: Fetching {len(self.players_to_scrape)} players (LIMIT 50).")
            else:
                print(f"📋 Found {len(self.players_to_scrape)} players to check.")
            return True
        except Exception as e:
            print(f"❌ ERROR reading database (Table: {self.stats_table}): {e}")
            return False

    def _make_slug(self, name):
        name = unidecode(name.lower())
        name = re.sub(r"[^a-z0-9\s-]", "", name)
        name = re.sub(r"\s+", "-", name.strip())
        return name

    def _fetch_player_value(self, player):
        slug = self._make_slug(player)
        urls = [
            f"{self.base_url}{slug}",
            f"{self.base_url}{slug}-1",
            f"{self.base_url}{slug}-2"
        ]

        for url in urls:
            try:
                res = self.session.get(url, timeout=15)
                time.sleep(0.3)

                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")
                value_tag = soup.select_one(".player-value .player-tag")
                club_tag = soup.select_one(".playerInfoTop-bar__club")
                date_tag = soup.find(string=re.compile(r"Last update", re.I))

                if not value_tag or not club_tag:
                    continue

                etv_value = value_tag.text.strip()
                club = club_tag.text.strip()
                last_update = date_tag.strip() if date_tag else "N/a"

                print(f"  💶 {etv_value} | 🏟 {club}")
                return (player, etv_value, club, last_update)

            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                print(f"  -> HTML parse error: {e}")
                continue

        print("  ❌ Profile not found.")
        return (player, "N/a", "N/a", "N/a")

    def _write_results(self):
        if not self.results:
            print("No results to write.")
            return

        df = pd.DataFrame(self.results, columns=["player", "etv_value", "club_on_profile", "last_update"])
        try:
            with sqlite3.connect(self.db_file) as conn:
                df.to_sql(self.target_table, conn, if_exists="replace", index=False)
                print(f"\n✅ Wrote {len(df)} records to DB (Table: {self.target_table})")
        except Exception as e:
            print(f"❌ ERROR writing to DB: {e}")
        try:
            df.to_csv(self.csv_output, index=False, encoding="utf-8-sig")
            print(f"✅ Wrote {len(df)} records to CSV: {self.csv_output}")
        except Exception as e:
            print(f"❌ ERROR writing to CSV: {e}")

    def run(self):
        self._init_db()
        if not self._get_players():
            print("Failed to get players. Check I.1 script (fbref scraper).")
            return

        total_players = len(self.players_to_scrape)
        for i, player in enumerate(self.players_to_scrape, start=1):
            print(f"[{i}/{total_players}] {player}")
            try:
                result = self._fetch_player_value(player)
                self.results.append(result)
            except Exception as e:
                print(f"⚠️ CRITICAL ERROR processing {player}: {e}")
                self.results.append((player, "N/a", "N/a", "N/a"))

        print(f"\n✅ Finished! Collected {len(self.results)} results.")

        self._write_results()

if __name__ == "__main__":
    scraper = TransferScraper(
        db_file=DB_FILE,
        stats_table=STATS_TABLE,
        target_table=TARGET_TABLE,
        csv_output=CSV_OUTPUT_FILE
    )
    scraper.run()