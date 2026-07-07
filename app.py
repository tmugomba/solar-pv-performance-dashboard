import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Page setup ---
# st.set_page_config controls the browser tab title and layout width
st.set_page_config(page_title="Solar PV Performance Dashboard", layout="wide")
st.title("☀️ Solar PV Performance Dashboard")
st.write("Interactive analysis of two solar plants — generation trends, weather correlation, and fault detection.")

# --- Load and cache the data ---
# @st.cache_data means this function only re-runs when the file changes,
# not every single time the user interacts with the app (much faster)
@st.cache_data
def load_data():
    gen_p1 = pd.read_csv('data/Plant_1_Generation_Data.csv')
    gen_p1['DATE_TIME'] = pd.to_datetime(gen_p1['DATE_TIME'], format='%d-%m-%Y %H:%M')

    gen_p2 = pd.read_csv('data/Plant_2_Generation_Data.csv')
    gen_p2['DATE_TIME'] = pd.to_datetime(gen_p2['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

    weather_p1 = pd.read_csv('data/Plant_1_Weather_Sensor_Data.csv')
    weather_p1['DATE_TIME'] = pd.to_datetime(weather_p1['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

    weather_p2 = pd.read_csv('data/Plant_2_Weather_Sensor_Data.csv')
    weather_p2['DATE_TIME'] = pd.to_datetime(weather_p2['DATE_TIME'], format='%Y-%m-%d %H:%M:%S')

    return gen_p1, gen_p2, weather_p1, weather_p2

gen_p1, gen_p2, weather_p1, weather_p2 = load_data()

# --- Sidebar: plant selector (this is the first interactive control) ---
st.sidebar.header("Controls")
plant_choice = st.sidebar.selectbox("Select Plant", ["Plant 1", "Plant 2"])

# Pick the right dataset based on the dropdown selection
gen_data = gen_p1 if plant_choice == "Plant 1" else gen_p2

# --- Daily generation trend chart ---
st.subheader(f"{plant_choice} — Daily Total AC Power Generation")

gen_data['DATE'] = gen_data['DATE_TIME'].dt.date
daily_total = gen_data.groupby('DATE')['AC_POWER'].sum()

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(daily_total.index, daily_total.values, marker='o')
ax.set_xlabel("Date")
ax.set_ylabel("Total AC Power (kW)")
plt.xticks(rotation=45)
st.pyplot(fig)