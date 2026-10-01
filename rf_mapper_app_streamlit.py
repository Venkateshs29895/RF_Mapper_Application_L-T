
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📱 RF Heatmap Visualizer")

uploaded_file = st.file_uploader(
    "📄 Upload Excel file (.xlsx) with Latitude, Longitude, and RF data",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.write("📋 Columns found in file:", df.columns.tolist())

    # Detect PLMN column
    plmn_col = None
    for col in df.columns:
        if "plmn" in col.lower():
            plmn_col = col
            break

    # Detect Cell ID column (including common alternatives)
    cell_id_col = None
    for col in df.columns:
        normalized = col.lower().replace(" ", "").replace("_", "")
        if normalized in ["cellid", "eci", "nci", "xci"]:
            cell_id_col = col
            break

    # Detect RF parameters
    rf_columns = [
        col for col in df.columns
        if col.strip().upper() in ["RSRP", "RSSI", "RSRQ", "SINR"]
    ]

    # Validate required columns
    if not {"Latitude", "Longitude"}.issubset(df.columns) or not rf_columns:
        st.error(
            "❌ File must contain 'Latitude', 'Longitude' "
            "and at least one RF parameter such as "
            "RSRP, RSSI, RSRQ, or SINR."
        )

    else:
        # PLMN filter
        if plmn_col and not df[plmn_col].dropna().empty:
            unique_plmns = sorted(
                df[plmn_col].dropna().astype(str).unique()
            )

            st.sidebar.header("📶 PLMN Filter")
            selected_plmn = st.sidebar.selectbox(
                "Filter by PLMN",
                ["All"] + list(unique_plmns)
            )

            if selected_plmn != "All":
                df = df[
                    df[plmn_col].astype(str) == selected_plmn
                ]

        elif plmn_col:
            st.warning("⚠️ PLMN column exists but contains no valid values.")
        else:
            st.info("ℹ️ No PLMN column detected.")

        # Cell ID filter
        if cell_id_col and not df[cell_id_col].dropna().empty:
            unique_cells = sorted(
                df[cell_id_col].dropna().astype(str).unique()
            )

            st.sidebar.header("📡 Cell ID Filter")
            selected_cell = st.sidebar.selectbox(
                "Select Cell ID",
                ["All"] + list(unique_cells)
            )

            if selected_cell != "All":
                df = df[
                    df[cell_id_col].astype(str) == selected_cell
                ]

        elif cell_id_col:
            st.warning("⚠️ Cell ID column exists but contains no valid values.")
        else:
            st.info("ℹ️ No Cell ID column detected.")

        # RF parameter selection
        selected_param = st.selectbox(
            "📈 Select RF Parameter to Visualize",
            rf_columns
        )

        # Convert numeric columns safely
        df["Latitude"] = pd.to_numeric(
            df["Latitude"], errors="coerce"
        )
        df["Longitude"] = pd.to_numeric(
            df["Longitude"], errors="coerce"
        )
        df[selected_param] = pd.to_numeric(
            df[selected_param], errors="coerce"
        )

        # Remove invalid records
        df = df.dropna(
            subset=["Latitude", "Longitude", selected_param]
        )

        if df.empty:
            st.warning(
                "⚠️ No valid data available for the selected filters."
            )
            st.stop()

        min_val = float(df[selected_param].min())
        max_val = float(df[selected_param].max())

        # RF range filter
        st.sidebar.header("⚡ Filter RF Values")

        preset = st.sidebar.radio(
            "Range Preset",
            ["All", "Excellent", "Good", "Fair", "Poor"]
        )

        # RF thresholds
        if selected_param.upper() == "RSRP":
            thresholds = {
                "Excellent": (-80, max_val),
                "Good": (-90, -80),
                "Fair": (-100, -90),
                "Poor": (min_val, -100)
            }

        elif selected_param.upper() == "RSRQ":
            thresholds = {
                "Excellent": (-10, max_val),
                "Good": (-15, -10),
                "Fair": (-20, -15),
                "Poor": (min_val, -20)
            }

        elif selected_param.upper() == "SINR":
            thresholds = {
                "Excellent": (20, max_val),
                "Good": (13, 20),
                "Fair": (0, 13),
                "Poor": (min_val, 0)
            }

        elif selected_param.upper() == "RSSI":
            thresholds = {
                "Excellent": (-65, max_val),
                "Good": (-75, -65),
                "Fair": (-85, -75),
                "Poor": (min_val, -85)
            }

        else:
            thresholds = {}

        # Apply preset or manual range
        if preset != "All" and preset in thresholds:
            low, high = thresholds[preset]

            # Clamp preset values to available data
            selected_range = (
                max(min_val, low),
                min(max_val, high)
            )

            if selected_range[0] > selected_range[1]:
                df_filtered = df.iloc[0:0].copy()
            else:
                df_filtered = df[
                    (df[selected_param] >= selected_range[0]) &
                    (df[selected_param] <= selected_range[1])
                ]

        else:
            if min_val == max_val:
                selected_range = (min_val, max_val)
                df_filtered = df.copy()
            else:
                selected_range = st.sidebar.slider(
                    f"Select range for {selected_param}",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)
                )

                df_filtered = df[
                    (df[selected_param] >= selected_range[0]) &
                    (df[selected_param] <= selected_range[1])
                ]

        st.success(
            f"✅ {len(df_filtered)} data points within selected range."
        )

        if df_filtered.empty:
            st.warning("⚠️ No data points match the selected RF range.")
            st.stop()

        # Histogram
        st.sidebar.markdown(f"### 📊 {selected_param} Histogram")

        fig, ax = plt.subplots()
        df_filtered[selected_param].hist(
            bins=20,
            ax=ax,
            color="skyblue",
            edgecolor="black"
        )
        ax.set_title(f"{selected_param} Distribution")
        ax.set_xlabel(selected_param)
        ax.set_ylabel("Frequency")
        st.sidebar.pyplot(fig)
        plt.close(fig)

        # RF statistics
        st.sidebar.markdown(
            f"**Average {selected_param}:** "
            f"{df_filtered[selected_param].mean():.2f}"
        )
        st.sidebar.markdown(
            f"**Strongest:** "
            f"{df_filtered[selected_param].max():.2f}"
        )
        st.sidebar.markdown(
            f"**Weakest:** "
            f"{df_filtered[selected_param].min():.2f}"
        )

        # Map
        avg_lat = df_filtered["Latitude"].mean()
        avg_lon = df_filtered["Longitude"].mean()

        rf_map = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=14
        )

        # Terrain layer
        folium.TileLayer(
            tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
            name="Stamen Terrain",
            attr=(
                "Map tiles by Stamen Design, under CC BY 3.0. "
                "Data by OpenStreetMap, under ODbL."
            ),
            overlay=False,
            control=True
        ).add_to(rf_map)

        # RF heatmap
        # Normalize signal values to avoid negative heat weights
        values = df_filtered[selected_param]
        min_signal = values.min()
        max_signal = values.max()

        if max_signal == min_signal:
            heat_data = [
                [row["Latitude"], row["Longitude"], 1.0]
                for _, row in df_filtered.iterrows()
            ]
        else:
            heat_data = [
                [
                    row["Latitude"],
                    row["Longitude"],
                    (row[selected_param] - min_signal) /
                    (max_signal - min_signal)
                ]
                for _, row in df_filtered.iterrows()
            ]

        HeatMap(
            heat_data,
            radius=10,
            blur=15,
            min_opacity=0.5,
            max_zoom=18
        ).add_to(rf_map)

        # RF signal color classification
        def get_color(value):
            p = selected_param.upper()

            if p == "RSRP":
                if value >= -80:
                    return "green"
                elif value >= -90:
                    return "orange"
                elif value >= -100:
                    return "darkorange"
                else:
                    return "red"

            elif p == "RSRQ":
                if value >= -10:
                    return "green"
                elif value >= -15:
                    return "orange"
                elif value >= -20:
                    return "darkorange"
                else:
                    return "red"

            elif p == "SINR":
                if value >= 20:
                    return "green"
                elif value >= 13:
                    return "orange"
                elif value >= 0:
                    return "darkorange"
                else:
                    return "red"

            elif p == "RSSI":
                if value >= -65:
                    return "green"
                elif value >= -75:
                    return "orange"
                elif value >= -85:
                    return "darkorange"
                else:
                    return "red"

            return "gray"

        # Add RF measurement markers
        for _, row in df_filtered.iterrows():
            signal_value = row[selected_param]

            tooltip = f"{selected_param}: {signal_value:.2f}"

            if cell_id_col:
                tooltip += f" | Cell ID: {row[cell_id_col]}"

            if plmn_col:
                tooltip += f" | PLMN: {row[plmn_col]}"

            folium.CircleMarker(
                location=[
                    row["Latitude"],
                    row["Longitude"]
                ],
                radius=4,
                color=get_color(signal_value),
                fill=True,
                fill_opacity=0.8,
                popup=tooltip,
                tooltip=tooltip
            ).add_to(rf_map)

        # Display map
        st.subheader("🗺️ RF Signal Map")

        st_folium(
            rf_map,
            width=1000,
            height=600
        )
