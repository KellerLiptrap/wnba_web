import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text, inspect # Import inspect
import time

# Create a persistent SQLite engine
# The database file 'wnba.db' will be created in the same directory as this script
engine = create_engine('sqlite:///wnba.db')

# Use the inspector to check if the tables already exist
inspector = inspect(engine)

# Only create and populate tables if they don't exist
# This prevents recreating the tables every time the script is run or imported
if not inspector.has_table('wnbaplayers') or not inspector.has_table('games'):
    print("Creating and populating database tables...")

    # ================================
    # Load player data into wnbaplayers
    # ================================
    df_players = pd.read_csv('wnbaboxscore.csv')
    df_players["team_full_name"] = df_players["team_location"] + " " + df_players["team_name"]
    df_players = df_players[["athlete_id", "athlete_display_name", "team_full_name"]].drop_duplicates()
    df_players = df_players.rename(columns={
        "athlete_id": "id",
        "athlete_display_name": "player_name",
        "team_full_name": "team_name"
    })
    df_players = df_players[~df_players["team_name"].isin(["TEAM CLARK", "TEAM COLLIER"])]

    df_players.to_sql(name='wnbaplayers', con=engine, if_exists='replace', index=False)

    # ================================
    # Load game data into games table
    # ================================
    df_games = pd.read_csv('wnbaboxscore.csv')
    df_games["three_points_percentage"] = df_games["three_point_field_goals_made"] / df_games["three_point_field_goals_attempted"]
    df_games = df_games[[
        "athlete_id", "game_date", "minutes", "points", "rebounds", "assists",
        "three_point_field_goals_made", "three_points_percentage"
    ]].drop_duplicates()
    df_games = df_games.rename(columns={
        "athlete_id": "id",
        "three_point_field_goals_made": "three_pointers_made"
    })
    df_games = df_games[~df_games["game_date"].isin(["2025-07-19"])]
    df_games.to_sql(name='games', con=engine, if_exists='replace', index=False)
    
    print("Database tables created successfully.")
else:
    print("Database tables already exist. Skipping creation.")

# ================================
# Function: betting_line
# ================================
def betting_line(stat, player=None, line=None, over_under=None):
    allowed_stats = {"points", "rebounds", "assists"}
    if stat not in allowed_stats:
        raise ValueError(f"Invalid stat: {stat}")
    
    query_str = f"""
        SELECT p.player_name, g.game_date, g.minutes, g.{stat}
        FROM wnbaplayers p 
        JOIN games g ON p.id = g.id
        WHERE p.player_name = :player
          AND p.team_name NOT IN ('Team Collier TEAM COLLIER', 'Team Clark TEAM CLARK')
        ORDER BY g.game_date DESC
    """

    with engine.connect() as conn:
        query = conn.execute(text(query_str), {"player": player})
        df = pd.DataFrame(query.fetchall(), columns=query.keys())

    if df.empty:
        return None, f"No data found for player: {player}"

    games_played = len(df)
    last_5_games = df.head(5)
    last_10_games = df.head(10)

    result = []
    result.append(f"Total games played by {player}: {games_played}")
    result.append(f"Averaging {stat} per game: {df[stat].mean():.2f}")
    result.append(f"In the last 10 games, averaging {stat} per game: {last_10_games[stat].mean():.2f}")

    if line is not None:
        total_games = len(df)

        if over_under == "over":
            over_5 = (last_5_games[stat] > line).sum()
            over_10 = (last_10_games[stat] > line).sum()
            over_all = (df[stat] > line).sum()
            result.append(f"\n{player} has gone OVER {line} {stat}:")
            result.append(f" - In the last 5 games: {over_5} out of 5 games ({(over_5 / 5) * 100:.1f}%)")
            result.append(f" - In the last 10 games: {over_10} out of 10 games ({(over_10 / 10) * 100:.1f}%)")
            result.append(f" - Across all {total_games} games: {over_all} out of {total_games} ({(over_all / total_games) * 100:.1f}%)")

        elif over_under == "under":
            under_5 = (last_5_games[stat] < line).sum()
            under_10 = (last_10_games[stat] < line).sum()
            under_all = (df[stat] < line).sum()
            result.append(f"\n{player} has gone UNDER {line} {stat}:")
            result.append(f" - In the last 5 games: {under_5} out of 5 games ({(under_5 / 5) * 100:.1f}%)")
            result.append(f" - In the last 10 games: {under_10} out of 10 games ({(under_10 / 10) * 100:.1f}%)")
            result.append(f" - Across all {total_games} games: {under_all} out of {total_games} ({(under_all / total_games) * 100:.1f}%)")

    return df, "\n".join(result)



# ================================
# Optional Debug Entry Point
# ================================
if __name__ == "__main__":
    print("DEBUG: bettingline module executed directly")
    # You can add a test call here to verify it works
    # For example:
    # betting_line("points", "Kelsey Plum", 20.5, "over")
    print("DEBUG: Available top-level names:", dir())
