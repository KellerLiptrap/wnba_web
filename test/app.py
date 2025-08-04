import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time

from playerstats import get_player_stats
from bettingline import betting_line
from r import install_and_load

import streamlit as st

# Setup in-memory SQLite engine
engine = create_engine('sqlite:///:memory:')

st.set_page_config(page_title="WNBA Betting Lines", page_icon=":basketball:", layout="wide")

# Load data
df = pd.read_csv('wnbaboxscore.csv')

bad_team_names = ["TEAM CLARK", "TEAM COLLIER"]
df = pd.read_csv('wnbaboxscore.csv')


#############################
# Main execution
#############################
def check_data_freshness(df):
    today = datetime.today().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if df.empty:
        st.warning("⚠️ CSV is empty. Attempting to load fresh data...")
        install_and_load()
        bad_team_names = ["TEAM CLARK", "TEAM COLLIER"]
        df = pd.read_csv('wnbaboxscore.csv')
        df_clean = df[~df['opponent_team_name'].isin(bad_team_names)].copy()
        df_clean.to_csv("wnba_box_scores_cleaned2.csv", index=False)
    else:
        last_game_date = df["game_date"][0]
        if last_game_date < yesterday:
            st.warning(f"📅 Data is outdated. Last game in CSV: {last_game_date}")
            install_and_load()
            bad_team_names = ["TEAM CLARK", "TEAM COLLIER"]
            df = pd.read_csv('wnbaboxscore.csv')
            df_clean = df[~df['opponent_team_name'].isin(bad_team_names)].copy()
            df_clean.to_csv("wnba_box_scores_cleaned2.csv", index=False)

        else:
            st.success(f"✅ Data is up to date. Last game date: {last_game_date}")

def show_betting_line():
    st.title("📈 WNBA Betting Line Calculator")

    player = st.text_input("Enter player name for betting line:")
    stat = st.selectbox("Select stat:", ["points", "rebounds", "assists", "three_pointers_made", "three_points_percentage"])
    line = st.number_input("Enter betting line (e.g., 15.5):", step=0.5)
    over_under = st.selectbox("Select over/under:", ["over", "under"])

    if st.button("Get Betting Line"):
        if player and line and over_under:
            try:
                df_result, summary = betting_line(stat, player, line, over_under)
                st.subheader(f"📊 Game Log for {player}")
                if df_result is not None and not df_result.empty:
                    st.dataframe(df_result.style.format({
                        "minutes": "{:.1f}",
                        stat: "{:.1f}"
                    }))
                    st.subheader("📈 Summary")
                    st.code(summary, language="markdown")
                else:
                    st.warning(summary)
            except ValueError as e:
                st.error(f"❌ {e}")
        else:
            st.error("❌ Please fill all fields.")

def show_matchups():
    df = pd.read_csv('wnbaboxscore.csv')
    df['game_date'] = pd.to_datetime(df['game_date'])

    df = df[~df['team_name'].isin(['Team Clark', 'Team Collier'])]


    st.title("🏀 WNBA Opponent Matchup Analysis by Player Position")
    st.markdown(
        """
        This analysis shows average Minutes, Points, Assists, Rebounds, and 3PM per position
        against opposing teams. 'Games Sampled' indicates the number of games contributing to these averages.
        """
    )

    team_name = st.sidebar.selectbox("Select Team", sorted(df["team_name"].unique()))
    position = st.sidebar.selectbox("Select Position", ["G", "F", "C"])

    matchups = df.groupby(["opponent_team_name", "athlete_position_abbreviation"]).agg({
        "points": "mean",
        "assists": "mean",
        "rebounds": "mean",
        "three_point_field_goals_made": "mean",
        "minutes": "mean",
        "athlete_display_name": "count"
    }).rename(columns={"athlete_display_name": "games_sampled"}).reset_index()

    matchups_by_pos = {
        "G": matchups[matchups["athlete_position_abbreviation"] == "G"],
        "F": matchups[matchups["athlete_position_abbreviation"] == "F"],
        "C": matchups[matchups["athlete_position_abbreviation"] == "C"]
    }

    for metric in ["points", "assists", "rebounds", "three_point_field_goals_made"]:
        st.header(f"### {metric.upper()} by Opponent and Position")
        for pos in ["G", "F", "C"]:
            st.subheader(f"{pos} ({metric.upper()})")
            df_metric = matchups_by_pos[pos].sort_values(by=metric, ascending=False)
            st.dataframe(df_metric[["opponent_team_name", metric, "minutes", "games_sampled"]])

    st.markdown("---")

    filtered_df = df[(df["team_name"] == team_name) & (df["athlete_position_abbreviation"] == position)]
    filtered_df_sorted = filtered_df.sort_values(["athlete_display_name", "game_date"], ascending=[True, False])

    def last_10_games_only(player_df):
        return player_df.head(10)

    last_10_games = filtered_df_sorted.groupby("athlete_display_name").apply(last_10_games_only).reset_index(drop=True)

    st.header(f"📊 Last 10 Games per Player for {team_name} ({position})")

    for player, group in last_10_games.groupby("athlete_display_name"):
        with st.expander(f"{player} - Game Logs"):
            group = group.copy()
            group['PTS+REB+AST'] = group['points'] + group['rebounds'] + group['assists']
            group['PTS+AST'] = group['points'] + group['assists']
            group['PTS+REB'] = group['points'] + group['rebounds']
            group['REB+AST'] = group['rebounds'] + group['assists']

            display_cols = ['game_date', 'opponent_team_name', 'minutes', 'points', 'rebounds', 'assists',
                            'three_point_field_goals_made', 'PTS+REB+AST', 'PTS+AST', 'PTS+REB', 'REB+AST']
            st.dataframe(group[display_cols])

            avg_stats = {
                "Minutes": group['minutes'].mean(),
                "Points": group['points'].mean(),
                "Rebounds": group['rebounds'].mean(),
                "Assists": group['assists'].mean(),
                "3PM": group['three_point_field_goals_made'].mean(),
                "PTS+REB+AST": group['PTS+REB+AST'].mean(),
                "PTS+AST": group['PTS+AST'].mean(),
                "PTS+REB": group['PTS+REB'].mean(),
                "REB+AST": group['REB+AST'].mean()
            }

            st.markdown("#### Averages over Last 10 Games")
            st.json(avg_stats)

def interactive_prompt():
    st.title("🏀 WNBA Betting Lines and Player Stats")

    check_data_freshness(df)

    option = st.radio("Choose a section to explore:", ["🏀 Betting Line Calculator", "📊 Matchup Stats by Position"])

    if option == "🏀 Betting Line Calculator":
        show_betting_line()

    elif option == "📊 Matchup Stats by Position":
        show_matchups()

if __name__ == "__main__":
    interactive_prompt()
    st.write("✅ Thank you for using the WNBA Betting Lines app!")
