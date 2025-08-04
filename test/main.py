import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time

from playerstats import get_player_stats
from bettingline import betting_line
from r import install_and_load

# Setup in-memory SQLite engine
engine = create_engine('sqlite:///:memory:')

# Load data
df = pd.read_csv('wnbaboxscore.csv')

#############################
# Main execution
#############################
def check_data_freshness(df):
    today = datetime.today().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if df.empty:
        print("⚠️ CSV is empty. Attempting to load fresh data...")
        install_and_load()
    else:
        last_game_date = df["game_date"][0]
        if last_game_date < yesterday:
            print(f"📅 Data is outdated. Last game in CSV: {last_game_date}")
            install_and_load()
        else:
            print(f"✅ Data is up to date. Last game date: {last_game_date}")

def interactive_prompt():
    while True:
        print("\n🟣 Choose an option:")
        print("1 - Season Stats")
        print("2 - Betting Line")
        print("0 - Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            player = input("Enter player name: ").strip()
            get_player_stats("season stats", player)

        elif choice == "2":
            player = input("Enter player name: ").strip()
            stat = input("Enter stat (points, rebounds, assists, three_pointers_made, three_points_percentage): ").strip()
            try:
                line = float(input("Enter betting line (e.g., 15.5): "))
            except ValueError:
                print("❌ Invalid number. Try again.")
                continue

            over_under = input("Enter (over/under): ").strip().lower()
            if over_under not in ["over", "under"]:
                print("❌ Invalid input for over/under.")
                continue

            betting_line(stat, player, line, over_under)

        elif choice == "0":
            print("👋 Exiting. Have a great day!")
            break
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    check_data_freshness(df)
    interactive_prompt()
