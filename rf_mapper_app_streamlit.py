import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📱 RF Heatmap Visualizer")

uploaded_file = st.file_uploader("📄 Upload Excel file (.xlsx) with Latitude, Longitude, and RF data", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Check if PLMN column exists
    plmn_col = None
    for col in df.columns:
        if col.upper() == "PLMN":
            plmn_col = col
            break

    rf_columns = [col for col in df.columns if col.upper() in ["RSRP", "RSSI", "RSRQ", "SINR"]]
    if not {"Latitude", "Longitude"}.issubset(df.columns) or not rf_columns:
        st.error("❌ File must contain 'Latitude', 'Longitude' and at least one RF parameter like RSRP, RSSI, RSRQ, or SINR.")
    else:
        if plmn_col:
            unique_plmns = sorted(df[plmn_col].dropna().astype(str).unique())
            selected_plmn = st.sidebar.selectbox("🔍 Filter by PLMN (optional)", ["All"] + unique_plmns)
            if selected_plmn != "All":
                df = df[df[plmn_col].astype(str) == selected_plmn]

        selected_param = st.selectbox("📈 Select RF Parameter to Visualize", rf_columns)

        df = df.dropna(subset=["Latitude", "Longitude", selected_param])
        min_val = float(df[selected_param].min())
        max_val = float(df[selected_param].max())

        st.sidebar.header("⚡ Filter RF Values")

        # 🎛️ Custom range presets
        preset = st.sidebar.radio("Range Preset", ["All", "Excellent", "Good", "Fair", "Poor"])
        if selected_param.upper() == "RSRP":
            thresholds = {"Excellent": (-80, max_val), "Good": (-90, -80), "Fair": (-100, -90), "Poor": (min_val, -100)}
        elif selected_param.upper() == "RSRQ":
            thresholds = {"Excellent": (-10, max_val), "Good": (-15, -10), "Fair": (-20, -15), "Poor": (min_val, -20)}
        elif selected_param.upper() == "SINR":
            thresholds = {"Excellent": (20, max_val), "Good": (13, 20), "Fair": (0, 13), "Poor": (min_val, 0)}
        elif selected_param.upper() == "RSSI":
            thresholds = {"Excellent": (-65, max_val), "Good": (-75, -65), "Fair": (-85, -75), "Poor": (min_val, -85)}
        else:
            thresholds = {}

        if preset != "All" and preset in thresholds:
            selected_range = thresholds[preset]
        else:
            selected_range = st.sidebar.slider(
                f"Select range for {selected_param}",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val)
            )

        df_filtered = df[(df[selected_param] >= selected_range[0]) & (df[selected_param] <= selected_range[1])]

        st.success(f"✅ {len(df_filtered)} data points within selected range.")

        # 📊 Histogram
        st.sidebar.markdown(f"### 📊 {selected_param} Histogram")
        fig, ax = plt.subplots()
        df_filtered[selected_param].hist(bins=20, ax=ax, color="skyblue", edgecolor="black")
        ax.set_title(f"{selected_param} Distribution")
        ax.set_xlabel(selected_param)
        ax.set_ylabel("Frequency")
        st.sidebar.pyplot(fig)

        # 🧮 Summary
        st.sidebar.markdown(f"**Average {selected_param}:** {df_filtered[selected_param].mean():.2f}")
        st.sidebar.markdown(f"**Strongest:** {df_filtered[selected_param].max():.2f}")
        st.sidebar.markdown(f"**Weakest:** {df_filtered[selected_param].min():.2f}")

        if df_filtered["Latitude"].notna().any() and df_filtered["Longitude"].notna().any():
            avg_lat = df_filtered["Latitude"].mean()
            avg_lon = df_filtered["Longitude"].mean()
            rf_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)
            folium.TileLayer(
                tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
                name="Stamen Terrain",
                attr="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL."
            ).add_to(rf_map)

            heat_data = [
                [row["Latitude"], row["Longitude"], row[selected_param]]
                for _, row in df_filtered.iterrows()
            ]
            HeatMap(
                heat_data,
                radius=10,
                blur=15,
                min_opacity=0.5,
                max_zoom=1
            ).add_to(rf_map)

            def get_color(value):
                p = selected_param.upper()
                if p == "RSRP":
                    if value >= -80: return "green"
                    elif value >= -90: return "orange"
                    elif value >= -100: return "darkorange"
                    else: return "red"
                elif p == "RSRQ":
                    if value >= -10: return "green"
                    elif value >= -15: return "orange"
                    elif value >= -20: return "darkorange"
                    else: return "red"
                elif p == "SINR":
                    if value >= 20: return "green"
                    elif value >= 13: return "orange"
                    elif value >= 0: return "darkorange"
                    else: return "red"
                elif p == "RSSI":
                    if value >= -65: return "green"
                    elif value >= -75: return "orange"
                    elif value >= -85: return "darkorange"
                    else: return "red"
                return "gray"

            for _, row in df_filtered.iterrows():
                signal_value = row[selected_param]
                tooltip = f"{selected_param}: {signal_value:.2f}"
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=4,
                    color=get_color(signal_value),
                    fill=True,
                    fill_opacity=0.8,
                    popup=tooltip,
                    tooltip=tooltip
                ).add_to(rf_map)

            st.subheader("🗺️ RF Signal Map")
            st_folium(rf_map, width=1000, height=600)
        else:
            st.warning("⚠️ No valid Latitude/Longitude found in the filtered data. Please adjust filters or check your file.")
