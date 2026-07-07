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
# --- Irradiation vs. Power comparison ---
st.subheader(f"{plant_choice} — Daily AC Power vs. Irradiation")

# Pick the matching weather dataset based on the plant dropdown
weather_data = weather_p1 if plant_choice == "Plant 1" else weather_p2

# Aggregate generation data to one row per timestamp (summing all inverters)
# This matches the structure of the weather data, which has one row per timestamp
plant_total_power = gen_data.groupby('DATE_TIME')['AC_POWER'].sum().reset_index()

# Merge power and irradiation on matching timestamps
merged = pd.merge(
    plant_total_power,
    weather_data[['DATE_TIME', 'IRRADIATION']],
    on='DATE_TIME',
    how='inner'
)

# Aggregate to daily totals for both metrics
merged['DATE'] = merged['DATE_TIME'].dt.date
daily_comparison = merged.groupby('DATE')[['AC_POWER', 'IRRADIATION']].sum().reset_index()

# Build the dual-axis chart (same style as your notebook version)
fig2, ax1 = plt.subplots(figsize=(12, 4))

ax1.plot(daily_comparison['DATE'], daily_comparison['AC_POWER'], color='tab:blue', marker='o', label='AC Power')
ax1.set_xlabel('Date')
ax1.set_ylabel('Total AC Power (kW)', color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()
ax2.plot(daily_comparison['DATE'], daily_comparison['IRRADIATION'], color='tab:orange', marker='o', label='Irradiation')
ax2.set_ylabel('Total Irradiation (kW/m²)', color='tab:orange')
ax2.tick_params(axis='y', labelcolor='tab:orange')

plt.xticks(rotation=45)
fig2.tight_layout()
st.pyplot(fig2)