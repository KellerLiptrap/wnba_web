import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import time

# Create in-memory SQLite database
engine = create_engine('sqlite:///:memory:')

# ================================
# Load and prepare player data
# ================================
df_players = pd.read_csv('wnbaboxscore.csv')
df_players["team_full_name"] = df_players["team_location"] + " " + df_players["team_name"]
df_players = df_players[["athlete_id", "athlete_display_name", "team_full_name"]].drop_duplicates()

df_players = df_players.rename(columns={
    "athlete_id": "id",
    "athlete_display_name": "player_name",
    "team_full_name": "team_name"
})

# Filter out All-Star teams
df_players = df_players[~df_players["team_name"].isin(["TEAM CLARK", "TEAM COLLIER"])]

df_players.to_sql(name='wnbaplayers', con=engine, if_exists='replace', index=False)

# ================================
# Load and prepare game data
# ================================
df_games = pd.read_csv('wnbaboxscore.csv')
df_games["three_points_percentage"] = df_games["three_point_field_goals_made"] / df_games["three_point_field_goals_attempted"]
df_games = df_games[["athlete_id", "game_date", "minutes", "points", "rebounds", "assists", "three_point_field_goals_made", "three_points_percentage"]].drop_duplicates()

df_games = df_games.rename(columns={
    "athlete_id": "id",
    "three_point_field_goals_made": "three_pointers_made"
})

df_games = df_games[~df_games["game_date"].isin(["2025-07-19"])]
df_games.to_sql(name='games', con=engine, if_exists='replace', index=False)

# ================================
# Function: get_player_stats
# ================================
def get_player_stats(method, player=None):
    if method == "season stats":
        games_number = input("Enter number of games or all for whole season: ")

        with engine.connect() as conn:
            query = conn.execute(
                text("""
                    SELECT p.player_name, g.game_date, g.minutes , g.points, g.rebounds, g.assists, g.three_pointers_made, g.three_points_percentage
                    FROM wnbaplayers p 
                    JOIN games g ON p.id = g.id
                    WHERE p.player_name = :player
                    AND p.team_name != 'Team Collier TEAM COLLIER' AND p.team_name != 'Team Clark TEAM CLARK'
                    ORDER BY g.game_date DESC
                """),
                {"player": player}
            )
            df = pd.DataFrame(query.fetchall(), columns=query.keys())
            if df.empty:
                print(f"No data found for player: {player}")
                return

        if games_number == "all":
            print(df)
            print(f"Total games played by {player}: {len(df)}")
            print(f"Averages for the season: "
                  f"Average minutes per game {df['minutes'].mean():.2f}, "
                  f"Average points per game {df['points'].mean():.2f}, "
                  f"Average rebounds per game: {df['rebounds'].mean():.2f}, "
                  f"Average assists per game: {df['assists'].mean():.2f}, "
                  f"Average three-pointers made per game: {df['three_pointers_made'].mean():.2f}, "
                  f"Average three-point percentage: {df['three_points_percentage'].mean() * 100:.2f}%")

        elif games_number.isdigit():
            games_number = int(games_number)
            print(df.head(games_number))
            print(f"Averages in last {games_number} games: "
                  f"{df['points'].head(games_number).mean():.2f} PPG, "
                  f"{df['rebounds'].head(games_number).mean():.2f} RPG, "
                  f"{df['assists'].head(games_number).mean():.2f} APG, "
                  f"{df['three_pointers_made'].head(games_number).mean():.2f} 3PM, "
                  f"{df['three_points_percentage'].head(games_number).mean() * 100:.2f}% 3P%")

# ================================
# Optional Debug: Verify module structure
# ================================
if __name__ == "__main__":
    print("DEBUG: playerstats module executed directly")
    print("DEBUG: Available top-level names:", dir())
