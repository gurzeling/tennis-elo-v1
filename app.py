# app.py

import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------
# 1️⃣ Load real match data
# -----------------------------------

@st.cache_data
def load_data(years):
    dfs = []
    for year in years:
        url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
        df = pd.read_csv(url)
        dfs.append(df)
    matches = pd.concat(dfs, ignore_index=True)
    matches = matches[['tourney_date', 'surface', 'winner_name', 'loser_name']]
    matches = matches.dropna(subset=['winner_name', 'loser_name'])
    return matches

years = [2021, 2022, 2023]
matches = load_data(years)

# -----------------------------------
# 2️⃣ Calculate Elo ratings
# -----------------------------------

BASE_ELO = 1500
K = 32

elo_ratings = {}

def get_elo(player):
    return elo_ratings.get(player, BASE_ELO)

def expected_score(Ra, Rb):
    return 1 / (1 + 10 ** ((Rb - Ra) / 400))

def update_elo(winner, loser):
    Ra = get_elo(winner)
    Rb = get_elo(loser)
    Ea = expected_score(Ra, Rb)
    Ra_new = Ra + K * (1 - Ea)
    Rb_new = Rb - K * (1 - Ea)
    elo_ratings[winner] = Ra_new
    elo_ratings[loser] = Rb_new

matches = matches.sort_values('tourney_date')

for _, row in matches.iterrows():
    update_elo(row['winner_name'], row['loser_name'])

players = sorted(elo_ratings.keys())

# -----------------------------------
# 3️⃣ Build Streamlit web app
# -----------------------------------

st.title("🎾 Tennis Elo Predictor")
st.write("""
This app calculates player ratings using an Elo system based on real ATP match results.
Pick two players below to see the predicted win probability!
""")

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
        index=players.index("Novak Djokovic") if "Novak Djokovic" in players else 1
    )

if player1 == player2:
    st.warning("Please select two different players.")
else:
    Ra = get_elo(player1)
    Rb = get_elo(player2)
    prob = expected_score(Ra, Rb)
    st.success(f"🎾 **{player1}** win probability vs **{player2}**: **{prob:.2%}**")

# -----------------------------------
# 4️⃣ Show Top 20 Elo Players
# -----------------------------------

top_players = pd.DataFrame(list(elo_ratings.items()), columns=['Player', 'Elo'])
top_players = top_players.sort_values('Elo', ascending=False).head(20)

st.subheader("📊 Top 20 Players by Elo Rating")
st.table(top_players.reset_index(drop=True))
