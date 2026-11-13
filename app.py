
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

from io import BytesIO

def excel_bytes(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False)
    return output.getvalue()


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="SkyCast | Weather Intelligence",
    page_icon="🌍",
    layout="wide"
)

# ==========================================
# CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #081426, #102b46);
    color: white;
}

h1, h2, h3, p, label {
    color: white !important;
}

[data-testid="stMetric"] {
    background: #173653;
    border: 1px solid #286184;
    padding: 18px;
    border-radius: 15px;
}

[data-testid="stMetricValue"] {
    color: #55D6FF;
}

section[data-testid="stSidebar"] {
    background: #10243A;
}

.stButton button {
    background: #08A6CF;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}

.stButton button:hover {
    background: #087FA8;
    color: white;
}

[data-testid="stTabs"] button {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================

st.title("🌍 SKYCAST")
st.subheader("Global Weather Intelligence")
st.caption("Explore weather data from cities around the world")

# ==========================================
# LOAD EXCEL DATA
# ==========================================

st.sidebar.title("⚙️ Settings")

uploaded_file = st.sidebar.file_uploader(
    "Upload your Weather Excel File",
    type=["xlsx", "xls"]
)

default_file = "GlobalWeatherRepository.xlsx"

try:
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
    elif os.path.exists(default_file):
        df = pd.read_excel(default_file)
    else:
        st.warning("Please upload your Global Weather Excel file.")
        st.stop()

    if df.empty:
        st.error("The uploaded Excel sheet is empty.")
        st.stop()

except Exception as e:
    st.error(f"Unable to read Excel file: {e}")
    st.stop()

# ==========================================
# COLUMN DETECTION
# ==========================================

def find_column(possible_names):

    normalized = {
        str(col).lower().replace("_", " ").strip(): col
        for col in df.columns
    }

    for name in possible_names:
        key = name.lower().replace("_", " ").strip()
        if key in normalized:
            return normalized[key]

    return None


city_col = find_column([
    "city", "location name", "city name"
])

country_col = find_column([
    "country", "country name"
])

lat_col = find_column([
    "latitude", "lat"
])

lon_col = find_column([
    "longitude", "lon", "long"
])

temp_col = find_column([
    "temperature celsius",
    "temperature c",
    "temperature_celsius",
    "temp c",
    "temperature"
])

temp_f_col = find_column([
    "temperature fahrenheit",
    "temperature f",
    "temperature_fahrenheit",
    "temp f"
])

wind_col = find_column([
    "wind speed",
    "wind speed kph",
    "wind_kph",
    "wind speed mph"
])

condition_col = find_column([
    "condition text",
    "weather condition",
    "condition",
    "weather"
])

# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Filter Weather Data")

filtered = df.copy()

if country_col:

    countries = sorted(
        filtered[country_col].dropna().astype(str).unique()
    )

    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        countries
    )

    if selected_countries:
        filtered = filtered[
            filtered[country_col].astype(str).isin(
                selected_countries
            )
        ]

if condition_col:

    conditions = sorted(
        filtered[condition_col].dropna().astype(str).unique()
    )

    selected_conditions = st.sidebar.multiselect(
        "Weather Conditions",
        conditions
    )

    if selected_conditions:
        filtered = filtered[
            filtered[condition_col].astype(str).isin(
                selected_conditions
            )
        ]

search = st.sidebar.text_input("Search City")

if search and city_col:
    filtered = filtered[
        filtered[city_col].astype(str).str.contains(
            search,
            case=False,
            na=False
        )
    ]

st.sidebar.markdown("---")
st.sidebar.caption("SkyCast Weather Intelligence")

# ==========================================
# CONVERT NUMERIC COLUMNS
# ==========================================

numeric_temp = None
numeric_wind = None

if temp_col:
    numeric_temp = pd.to_numeric(
        filtered[temp_col], errors="coerce"
    )

if wind_col:
    numeric_wind = pd.to_numeric(
        filtered[wind_col], errors="coerce"
    )

# ==========================================
# DASHBOARD TABS
# ==========================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Overview",
    "🏙️ City Explorer",
    "📊 Analytics",
    "🗺️ World Map",
    "📁 Full Dataset",
    "🌤️ Live Weather"
])

# ==========================================
# TAB 1: OVERVIEW
# ==========================================

with tab1:

    st.header("Global Weather Overview")

    total_records = len(filtered)

    total_cities = (
        filtered[city_col].nunique()
        if city_col else 0
    )

    total_countries = (
        filtered[country_col].nunique()
        if country_col else 0
    )

    avg_temp = (
        numeric_temp.mean()
        if numeric_temp is not None else None
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📍 Weather Records", total_records)
    c2.metric("🏙️ Cities", total_cities)
    c3.metric("🌎 Countries", total_countries)

    c4.metric(
        "🌡️ Average Temperature",
        f"{avg_temp:.1f} °C"
        if pd.notna(avg_temp) else "N/A"
    )

    st.markdown("---")

    st.subheader("🌡️ Temperature Information")

    if numeric_temp is not None:

        valid_temp = numeric_temp.dropna()

        if not valid_temp.empty:

            a, b, c = st.columns(3)

            a.metric("Highest Temperature",
                     f"{valid_temp.max():.1f} °C")

            b.metric("Lowest Temperature",
                     f"{valid_temp.min():.1f} °C")

            c.metric("Temperature Range",
                     f"{valid_temp.max()-valid_temp.min():.1f} °C")

    if condition_col:

        st.subheader("☁️ Weather Conditions")

        counts = filtered[condition_col].value_counts().reset_index()
        counts.columns = ["Condition", "Count"]

        fig = px.pie(
            counts,
            names="Condition",
            values="Count",
            hole=0.55,
            title="Weather Condition Distribution",
            color_discrete_sequence=px.colors.sequential.Teal
        )

        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: CITY EXPLORER
# ==========================================

with tab2:

    st.header("🏙️ Explore Cities")

    if city_col:

        city_names = sorted(
            filtered[city_col].dropna().astype(str).unique()
        )

        if city_names:

            selected_city = st.selectbox(
                "Choose a city",
                city_names
            )

            city_data = filtered[
                filtered[city_col].astype(str) == selected_city
            ]

            st.subheader(f"Weather Details: {selected_city}")

            # Display every available field for selected city
            for _, record in city_data.iterrows():

                details = pd.DataFrame({
                    "Field": record.index,
                    "Value": record.values
                })

                st.dataframe(
                    details,
                    use_container_width=True,
                    hide_index=True
                )

    else:
        st.info("No recognized city column. See Full Dataset for all records.")

# ==========================================
# TAB 3: ANALYTICS
# ==========================================

with tab3:

    st.header("📊 Weather Analytics")

    if temp_col and numeric_temp is not None:

        chart_data = filtered.copy()
        chart_data["_temperature"] = pd.to_numeric(
            chart_data[temp_col], errors="coerce"
        )

        if city_col:

            chart_data = chart_data.dropna(
                subset=["_temperature"]
            )

            fig = px.bar(
                chart_data.head(50),
                x=city_col,
                y="_temperature",
                title="City-wise Temperature",
                color="_temperature",
                color_continuous_scale="Turbo"
            )

            st.plotly_chart(fig, use_container_width=True)

        if country_col:

            country_temp = (
                chart_data.groupby(country_col)["_temperature"]
                .mean()
                .reset_index()
                .sort_values("_temperature", ascending=False)
            )

            fig2 = px.bar(
                country_temp,
                x=country_col,
                y="_temperature",
                color="_temperature",
                color_continuous_scale="Plasma",
                title="Average Temperature by Country"
            )

            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("A temperature column was not detected.")

    if wind_col:

        wind_data = filtered.copy()
        wind_data["_wind"] = pd.to_numeric(
            wind_data[wind_col], errors="coerce"
        )

        fig3 = px.histogram(
            wind_data.dropna(subset=["_wind"]),
            x="_wind",
            nbins=20,
            title="Wind Speed Distribution",
            color_discrete_sequence=["#00C9FF"]
        )

        st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# TAB 4: WORLD MAP
# ==========================================

with tab4:

    st.header("🗺️ Global Weather Map")

    if lat_col and lon_col:

        map_data = filtered.copy()

        map_data[lat_col] = pd.to_numeric(
            map_data[lat_col], errors="coerce"
        )

        map_data[lon_col] = pd.to_numeric(
            map_data[lon_col], errors="coerce"
        )

        map_data = map_data.dropna(
            subset=[lat_col, lon_col]
        )

        if not map_data.empty:

            fig_map = px.scatter_geo(
                map_data,
                lat=lat_col,
                lon=lon_col,
                hover_name=city_col if city_col else None,
                color=condition_col if condition_col else None,
                projection="natural earth",
                title="Weather Locations Around the World"
            )

            st.plotly_chart(
                fig_map,
                use_container_width=True
            )

        else:
            st.warning("No valid coordinates found.")

    else:
        st.warning("Latitude and longitude columns were not detected.")

# ==========================================
# TAB 5: COMPLETE DATASET
# ==========================================

with tab5:

    st.header("📁 Complete Weather Dataset")

    st.write(f"Showing {len(filtered)} records")

    st.write("All original columns from your Excel sheet:")

    st.dataframe(
        filtered,
        use_container_width=True,
        height=500
    )

    st.download_button(
        label="⬇️ Download Filtered Excel Data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="SkyCast_Weather_Data.csv",
        mime="text/csv"
    )

    st.download_button(
        label="⬇️ Download Filtered Excel File",
        data=excel_bytes(filtered),
        file_name="SkyCast_Weather_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# TAB 6: LIVE WEATHER
# ==========================================

with tab6:

    st.header("🌤️ Live Weather Search")

    live_city = st.text_input(
        "Enter a city for live weather",
        placeholder="Example: Chennai",
        key="live_city"
    )

    if st.button("Get Live Weather"):

        if not live_city.strip():

            st.warning("Enter a city name.")

        else:

            try:

                location_response = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": live_city,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    },
                    timeout=15
                )

                location_response.raise_for_status()

                locations = location_response.json().get("results", [])

                if not locations:

                    st.error("City not found.")

                else:

                    place = locations[0]

                    weather_response = requests.get(
                        "https://api.open-meteo.com/v1/forecast",
                        params={
                            "latitude": place["latitude"],
                            "longitude": place["longitude"],
                            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                            "timezone": "auto"
                        },
                        timeout=15
                    )

                    weather_response.raise_for_status()

                    current = weather_response.json()["current"]

                    st.success(
                        f"Live weather: {place['name']}, "
                        f"{place.get('country', '')}"
                    )

                    x, y, z = st.columns(3)

                    x.metric(
                        "🌡️ Temperature",
                        f"{current['temperature_2m']} °C"
                    )

                    y.metric(
                        "💧 Humidity",
                        f"{current['relative_humidity_2m']}%"
                    )

                    z.metric(
                        "💨 Wind Speed",
                        f"{current['wind_speed_10m']} km/h"
                    )

                    st.write(
                        "Weather code:",
                        current["weather_code"]
                    )

                    st.caption(
                        "Source: Open-Meteo live weather service"
                    )

            except requests.exceptions.RequestException as e:

                st.error("Unable to connect to the live weather service.")
                st.write(str(e))

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.markdown(
    "<center>🌍 SKYCAST | Global Weather Intelligence "
    "<br>Built with Python, Streamlit, Pandas and Plotly</center>",
    unsafe_allow_html=True
)
