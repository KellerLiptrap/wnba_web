import pandas as pd
import streamlit as st

# Load data
df = pd.read_csv('wnbaboxscore.csv')
df['game_date'] = pd.to_datetime(df['game_date'])

# Sidebar team and position selector
st.sidebar.title("WNBA Player Filter")
team_name = st.sidebar.selectbox("Select Team", sorted(df["team_name"].unique()))
position = st.sidebar.selectbox("Select Position", ["G", "F", "C"])

# Aggregate matchups by position and opponent
matchups = df.groupby(["opponent_team_name", "athlete_position_abbreviation"]).agg({
    "points": "mean",
    "assists": "mean",
    "rebounds": "mean",
    "three_point_field_goals_made": "mean",
    "minutes": "mean",
    "athlete_display_name": "count"
}).rename(columns={"athlete_display_name": "games_sampled"}).reset_index()

# Position breakdown
matchups_by_pos = {
    "G": matchups[matchups["athlete_position_abbreviation"] == "G"],
    "F": matchups[matchups["athlete_position_abbreviation"] == "F"],
    "C": matchups[matchups["athlete_position_abbreviation"] == "C"]
}

# Header
st.title("🏀 WNBA Opponent Matchup Analysis by Player Position")
st.markdown(
    """
    This analysis shows average Minutes, Points, Assists, Rebounds, and 3PM per position
    against opposing teams. 'Games Sampled' indicates the number of games contributing to these averages.
    """
)

# Stats by category
for metric in ["points", "assists", "rebounds", "three_point_field_goals_made"]:
    st.header(f"### {metric.upper()} by Opponent and Position")

    for pos in ["G", "F", "C"]:
        st.subheader(f"{pos} ({metric.upper()})")
        df_metric = matchups_by_pos[pos].sort_values(by=metric, ascending=False)
        st.dataframe(df_metric[["opponent_team_name", metric, "minutes", "games_sampled"]])

st.markdown("---")

# Filter team and position
filtered_df = df[(df["team_name"] == team_name) & (df["athlete_position_abbreviation"] == position)]

# Sort and get last 10 games per player
filtered_df_sorted = filtered_df.sort_values(["athlete_display_name", "game_date"], ascending=[True, False])

def last_10_games_only(player_df):
    return player_df.head(10)

last_10_games = filtered_df_sorted.groupby("athlete_display_name").apply(last_10_games_only).reset_index(drop=True)

# Expand section per player
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

        # Averages
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
