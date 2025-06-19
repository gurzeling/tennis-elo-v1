# app.py

import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------
# 1️⃣ Load ATP & WTA data
# -----------------------------------

@st.cache_data
def load_data(years):
    dfs = []
    for year in years:
        atp_url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
        wta_url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv"
        atp_df = pd.read_csv(atp_url)
        wta_df = pd.read_csv(wta_url)
        dfs.extend([atp_df, wta_df])
    matches = pd.concat(dfs, ignore_index=True)
    matches = matches[['tourney_date', 'surface', 'winner_name', 'loser_name']]
    matches = matches.dropna(subset=['winner_name', 'loser_name', 'surface'])
    matches['surface'] = matches['surface'].str.lower()
    return matches

years = [2021, 2022, 2023]
matches = load_data(years)

# -----------------------------------
# 2️⃣ Initialize surface-specific Elo ratings
# -----------------------------------

BASE_ELO = 1500
K = 32

# Dict: {player: {surface: elo}}
elo_ratings = {}

def get_elo(player, surface):
    if player not in elo_ratings:
        elo_ratings[player] = {}
    return elo_ratings[player].get(surface, BASE_ELO)

def expected_score(Ra, Rb):
    return 1 / (1 + 10 ** ((Rb - Ra) / 400))

def update_elo(winner, loser, surface):
    Ra = get_elo(winner, surface)
    Rb = get_elo(loser, surface)
    Ea = expected_score(Ra, Rb)
    Ra_new = Ra + K * (1 - Ea)
    Rb_new = Rb - K * (1 - Ea)
    elo_ratings[winner][surface] = Ra_new
    elo_ratings[loser][surface] = Rb_new

matches = matches.sort_values('tourney_date')

for _, row in matches.iterrows():
    surface = row['surface']
    update_elo(row['winner_name'], row['loser_name'], surface)

# Get all unique players
players = sorted(elo_ratings.keys())
surfaces = ['hard', 'clay', 'grass']

# -----------------------------------
# 3️⃣ Streamlit web app with surface selector
# -----------------------------------

st.title("🎾 Tennis Elo Predictor with Surfaces (ATP & WTA)")
st.write("""
This app calculates player Elo ratings per surface using ATP & WTA match results (2021–2023).  
Pick a surface and two players to see the win probability!
""")

# Select surface
surface = st.selectbox("Select Surface", surfaces, index=0)

col1, col2 = st.columns(2)

with col1:
    player1 = st.selectbox(
        "Select Player 1",
        players,
        index=players.index("Carlos Alcaraz") if "Carlos Alcaraz" in players else 0
    )

with col2:
    player2 = st.selectbox(
        "Select Player 2",
        players,
        index=players.index("Iga Swiatek") if "Iga Swiatek" in players else 1
    )

if player1 == player2:
    st.warning("Please select two different players.")
else:
    Ra = get_elo(player1, surface)
    Rb = get_elo(player2, surface)
    prob = expected_score(Ra, Rb)
    st.success(f"🎾 **{player1}** win probability vs **{player2}** on **{surface.capitalize()}**: **{prob:.2%}**")

# -----------------------------------
# 4️⃣ Show Top 200 Players for selected surface
# -----------------------------------

top_players = []

for player in elo_ratings:
    rating = elo_ratings[player].get(surface, BASE_ELO)
    top_players.append((player, rating))

top_df = pd.DataFrame(top_players, columns=['Player', 'Elo'])
top_df = top_df.sort_values('Elo', ascending=False).head(200)

st.subheader(f"📊 Top 200 Players by Elo Rating on {surface.capitalize()}")
st.dataframe(top_df.reset_index(drop=True))
