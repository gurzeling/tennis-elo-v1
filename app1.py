import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------
# 1️⃣ Load ATP/WTA + Google Sheet data
# -----------------------------------

@st.cache_data
def load_data(years, gsheet_url):
    dfs = []
    for year in years:
        try:
            atp_url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
            wta_url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv"
            atp_df = pd.read_csv(atp_url)
            wta_df = pd.read_csv(wta_url)
            dfs.extend([atp_df, wta_df])
        except Exception as e:
            st.warning(f"Error loading {year}: {e}")
            continue

    matches = pd.concat(dfs, ignore_index=True)
    matches = matches[['tourney_date', 'surface', 'winner_name', 'loser_name']]
    matches = matches.dropna()

    # Load Google Sheet CSV (live results)
    try:
        live_df = pd.read_csv(gsheet_url)
        live_df = live_df[['tourney_date', 'surface', 'winner_name', 'loser_name']]
        matches = pd.concat([matches, live_df], ignore_index=True)
        st.success("✅ Live match data loaded from Google Sheet")
    except Exception as e:
        st.warning(f"⚠️ Could not load Google Sheet data: {e}")

    matches['surface'] = matches['surface'].str.lower()
    return matches

# -----------------------------------
# 2️⃣ Elo rating system
# -----------------------------------

BASE_ELO = 1500
K = 32
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

# -----------------------------------
# 3️⃣ App setup
# -----------------------------------

st.set_page_config(page_title="Tennis Elo Predictor", layout="wide")
st.title("🎾 Tennis Elo Predictor with Live Results")
st.markdown("""
This app calculates **surface-specific Elo ratings** for ATP & WTA players based on:
- Historical results from 2021–2024  
- Live match updates from your **Google Sheet**

Select a surface and two players to see the win probability.
""")

# ✅ Add your Google Sheet CSV URL here
gsheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vScxQ3MguXYlPS3UZ6mtoXE9Zy84vYRGd0O6iZrKrfml9yfKt2kny7r5S50TD1X0kHCR9m4tHKSTz9I/pub?output=csv"

years = [2021, 2022, 2023, 2024]
matches = load_data(years, gsheet_url)
matches = matches.sort_values('tourney_date')

# Update Elo ratings from all matches
for _, row in matches.iterrows():
    update_elo(row['winner_name'], row['loser_name'], row['surface'])

surfaces = ['hard', 'clay', 'grass']
players = sorted(elo_ratings.keys())

# -----------------------------------
# 4️⃣ Prediction UI
# -----------------------------------

surface = st.selectbox("🎾 Select Surface", surfaces)

col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Player 1", players, index=players.index("Carlos Alcaraz") if "Carlos Alcaraz" in players else 0)
with col2:
    player2 = st.selectbox("Player 2", players, index=players.index("Iga Swiatek") if "Iga Swiatek" in players else 1)

if player1 == player2:
    st.warning("Please select two different players.")
else:
    Ra = get_elo(player1, surface)
    Rb = get_elo(player2, surface)
    prob = expected_score(Ra, Rb)
    st.success(f"🎾 **{player1}** win probability vs **{player2}** on **{surface.capitalize()}**: **{prob:.2%}**")

# -----------------------------------
# 5️⃣ Show Top 200 Elo Ratings
# -----------------------------------

top_players = []
for player in elo_ratings:
    rating = elo_ratings[player].get(surface, BASE_ELO)
    top_players.append((player, rating))

top_df = pd.DataFrame(top_players, columns=['Player', 'Elo'])
top_df = top_df.sort_values('Elo', ascending=False).head(200)

st.subheader(f"📊 Top 200 Players on {surface.capitalize()} Surface")
st.dataframe(top_df.reset_index(drop=True))
