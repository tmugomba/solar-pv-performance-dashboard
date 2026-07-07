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

# --- Sidebar: plant selector ---
st.sidebar.header("Controls")
plant_choice = st.sidebar.selectbox("Select Plant", ["Plant 1", "Plant 2"])

# Pick the right dataset based on the dropdown selection
gen_data = gen_p1 if plant_choice == "Plant 1" else gen_p2
weather_data = weather_p1 if plant_choice == "Plant 1" else weather_p2

# Add a DATE column (date only, no time) for grouping and filtering
gen_data['DATE'] = gen_data['DATE_TIME'].dt.date

# --- Sidebar: date range slider ---
# Get the min and max dates available in the dataset, so the slider bounds match the real data
min_date = gen_data['DATE'].min()
max_date = gen_data['DATE'].max()

date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)  # default: show the full range
)

# Filter gen_data to only the selected date range - used by the first chart
gen_data_filtered = gen_data[(gen_data['DATE'] >= date_range[0]) & (gen_data['DATE'] <= date_range[1])]

# --- Daily generation trend chart ---
st.subheader(f"{plant_choice} — Daily Total AC Power Generation")

daily_total = gen_data_filtered.groupby('DATE')['AC_POWER'].sum()

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(daily_total.index, daily_total.values, marker='o')
ax.set_xlabel("Date")
ax.set_ylabel("Total AC Power (kW)")
plt.xticks(rotation=45)
st.pyplot(fig)

# --- Irradiation vs. Power comparison ---
st.subheader(f"{plant_choice} — Daily AC Power vs. Irradiation")

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

# Add DATE column, then filter merged data to the selected date range
merged['DATE'] = merged['DATE_TIME'].dt.date
merged_filtered = merged[(merged['DATE'] >= date_range[0]) & (merged['DATE'] <= date_range[1])]

# Aggregate to daily totals for both metrics
daily_comparison = merged_filtered.groupby('DATE')[['AC_POWER', 'IRRADIATION']].sum().reset_index()

# Build the dual-axis chart
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