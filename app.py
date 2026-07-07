import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(page_title="Solar PV Performance Dashboard", layout="wide")
st.title("☀️ Solar PV Performance Dashboard")
st.write("Interactive analysis of two solar plants — generation trends, weather correlation, and fault detection.")

# --- Load and cache the data ---
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

# --- Key Findings Summary ---
with st.expander("📊 Key Findings — click to expand", expanded=True):
    st.markdown("""
    **Plant 1 generation is weather-driven, not equipment-driven**
    Daily AC power output tracks irradiation almost perfectly across the full 34-day period — 
    no unexplained dips where irradiation stayed high but power dropped.

    **Two Plant 1 inverters run consistently ~10-13% below plant average**
    Inverters `bvBOhCH3iADSZry` and `1BY6WEcLGh8j5v7` underperform the plant average throughout 
    the period. Inverter `1BY6WEcLGh8j5v7` also shows a sharp, isolated single-day anomaly on 
    **June 13**, dropping to roughly 1,300 kW while the plant average stayed near 3,200 kW.

    **Plant 2 experienced a temperature-driven mismatch, not an equipment fault**
    Between **May 19–27**, Plant 2's irradiation stayed high while power output lagged. 
    Checking inverter-by-inverter ruled out a single faulty unit — nearly all inverters were 
    affected equally. Module temperature was 35.4°C during this window vs. 31.8°C for the rest 
    of the period — a plausible thermal derating effect rather than a hardware issue.

    **Plant 1 is genuinely more efficient than Plant 2 — not just larger**
    Normalizing power output by irradiation (performance ratio) shows Plant 1 consistently 
    achieves a higher ratio (~28,000–32,000) than Plant 2 (~17,000–25,000) across nearly the 
    entire period, even though both plants receive similar sunlight. This points to a real 
    efficiency gap — likely panel quality, installation angle, or site conditions — rather 
    than Plant 1 simply having more capacity.
    """)

# --- Performance ratio helper function (needed by both KPI cards and the chart later) ---
def get_daily_performance_ratio(gen_df, weather_df):
    total_power = gen_df.groupby('DATE_TIME')['AC_POWER'].sum().reset_index()
    merged = pd.merge(total_power, weather_df[['DATE_TIME', 'IRRADIATION']], on='DATE_TIME', how='inner')
    merged['DATE'] = merged['DATE_TIME'].dt.date
    daily = merged.groupby('DATE')[['AC_POWER', 'IRRADIATION']].sum().reset_index()
    daily['PERFORMANCE_RATIO'] = daily['AC_POWER'] / daily['IRRADIATION']
    return daily

daily_ratio_p1 = get_daily_performance_ratio(gen_p1, weather_p1)
daily_ratio_p2 = get_daily_performance_ratio(gen_p2, weather_p2)

# --- KPI Summary Cards ---
st.subheader("At a Glance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_gen_p1 = gen_p1['AC_POWER'].sum()
    st.metric("Plant 1 Total AC Power", f"{total_gen_p1:,.0f} kW")

with col2:
    total_gen_p2 = gen_p2['AC_POWER'].sum()
    st.metric("Plant 2 Total AC Power", f"{total_gen_p2:,.0f} kW")

with col3:
    avg_ratio_p1 = daily_ratio_p1['PERFORMANCE_RATIO'].mean()
    st.metric("Plant 1 Avg Performance Ratio", f"{avg_ratio_p1:,.0f}")

with col4:
    avg_ratio_p2 = daily_ratio_p2['PERFORMANCE_RATIO'].mean()
    st.metric("Plant 2 Avg Performance Ratio", f"{avg_ratio_p2:,.0f}",
               delta=f"{avg_ratio_p2 - avg_ratio_p1:,.0f} vs Plant 1")

# --- Sidebar: plant selector ---
st.sidebar.header("Controls")
plant_choice = st.sidebar.selectbox("Select Plant", ["Plant 1", "Plant 2"])

# Pick the right dataset based on the dropdown selection
gen_data = gen_p1 if plant_choice == "Plant 1" else gen_p2
weather_data = weather_p1 if plant_choice == "Plant 1" else weather_p2

# Add a DATE column (date only, no time) for grouping and filtering
gen_data['DATE'] = gen_data['DATE_TIME'].dt.date

# --- Sidebar: date range slider ---
min_date = gen_data['DATE'].min()
max_date = gen_data['DATE'].max()

date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

# Filter gen_data to only the selected date range
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

plant_total_power = gen_data.groupby('DATE_TIME')['AC_POWER'].sum().reset_index()

merged = pd.merge(
    plant_total_power,
    weather_data[['DATE_TIME', 'IRRADIATION']],
    on='DATE_TIME',
    how='inner'
)

merged['DATE'] = merged['DATE_TIME'].dt.date
merged_filtered = merged[(merged['DATE'] >= date_range[0]) & (merged['DATE'] <= date_range[1])]

daily_comparison = merged_filtered.groupby('DATE')[['AC_POWER', 'IRRADIATION']].sum().reset_index()

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

# --- Inverter-level view ---
st.subheader(f"{plant_choice} — Average Power by Inverter")

gen_data_for_inverters = gen_data[(gen_data['DATE'] >= date_range[0]) & (gen_data['DATE'] <= date_range[1])]

inverter_avg = gen_data_for_inverters.groupby('SOURCE_KEY')['DC_POWER'].mean().sort_values()

bar_colors = ['steelblue'] * len(inverter_avg)
bar_colors[0] = 'firebrick'
bar_colors[-1] = 'seagreen'

fig3, ax3 = plt.subplots(figsize=(12, 5))
ax3.bar(inverter_avg.index, inverter_avg.values, color=bar_colors)
ax3.set_xlabel("Inverter (SOURCE_KEY)")
ax3.set_ylabel("Average DC Power (kW)")
plt.xticks(rotation=90)

lowest_key = inverter_avg.index[0]
highest_key = inverter_avg.index[-1]
lowest_val = inverter_avg.iloc[0]
highest_val = inverter_avg.iloc[-1]

ax3.text(0, lowest_val + (highest_val * 0.02), f"Lowest: {lowest_key}\n({lowest_val:.0f} kW)",
         ha='center', va='bottom', fontsize=9, color='firebrick', fontweight='bold')
ax3.text(len(inverter_avg) - 1, highest_val + (highest_val * 0.02), f"Highest: {highest_key}\n({highest_val:.0f} kW)",
         ha='center', va='bottom', fontsize=9, color='seagreen', fontweight='bold')

fig3.tight_layout()
st.pyplot(fig3)

st.caption(f"Lowest performing inverter in this range: **{lowest_key}** ({lowest_val:.0f} kW) — Highest: **{highest_key}** ({highest_val:.0f} kW)")

# --- Performance Ratio: Plant 1 vs Plant 2 ---
st.subheader("Performance Ratio Comparison: Plant 1 vs. Plant 2")
st.caption("Performance ratio = AC Power ÷ Irradiation — normalizes output by weather, showing true efficiency regardless of system size.")

daily_ratio_p1_filtered = daily_ratio_p1[(daily_ratio_p1['DATE'] >= date_range[0]) & (daily_ratio_p1['DATE'] <= date_range[1])]
daily_ratio_p2_filtered = daily_ratio_p2[(daily_ratio_p2['DATE'] >= date_range[0]) & (daily_ratio_p2['DATE'] <= date_range[1])]

fig4, ax4 = plt.subplots(figsize=(12, 4))
ax4.plot(daily_ratio_p1_filtered['DATE'], daily_ratio_p1_filtered['PERFORMANCE_RATIO'], marker='o', label='Plant 1', color='tab:blue')
ax4.plot(daily_ratio_p2_filtered['DATE'], daily_ratio_p2_filtered['PERFORMANCE_RATIO'], marker='o', label='Plant 2', color='tab:green')
ax4.set_xlabel('Date')
ax4.set_ylabel('Performance Ratio (kW per kW/m²)')
plt.xticks(rotation=45)
ax4.legend()
fig4.tight_layout()
st.pyplot(fig4)