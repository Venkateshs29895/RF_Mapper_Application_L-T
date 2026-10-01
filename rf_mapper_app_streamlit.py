import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="5G RF Mapper",
    page_icon="📡",
    layout="wide"
)

st.title("📡 5G Private Network RF Mapper")
st.caption(
    "Upload an Excel RF log to visualize RSRP, RSRQ, SINR and "
    "other RF parameters on a map."
)

# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📄 Upload Excel RF Log (.xlsx)",
    type=["xlsx"]
)

if uploaded_file:

    # --------------------------------------------------------
    # READ EXCEL
    # --------------------------------------------------------

    df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    st.success(
        f"✅ File loaded successfully: {uploaded_file.name}"
    )

    # Show detected columns
    with st.expander("📋 View Excel Columns"):
        st.write(df.columns.tolist())

    # ========================================================
    # COLUMN DETECTION FUNCTION
    # ========================================================

    def normalize_column_name(name):
        return (
            str(name)
            .lower()
            .strip()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
            .replace("/", "")
        )

    def find_column(possible_names):

        normalized_names = [
            normalize_column_name(name)
            for name in possible_names
        ]

        for col in df.columns:

            normalized_col = normalize_column_name(col)

            if normalized_col in normalized_names:
                return col

        return None

    # ========================================================
    # DETECT NETWORK COLUMNS
    # ========================================================

    plmn_col = find_column([
        "PLMN",
        "PLMN ID",
        "PLMN_ID"
    ])

    cell_id_col = find_column([
        "Cell ID",
        "CellID",
        "Cell_ID",
        "NR Cell ID",
        "NR_Cell_ID",
        "NR CellID",
        "NRCELLID",
        "NCI",
        "ECI",
        "XCI",
        "Cell Identity"
    ])

    pci_col = find_column([
        "PCI",
        "Physical Cell ID",
        "Physical_Cell_ID"
    ])

    tac_col = find_column([
        "TAC",
        "Tracking Area Code",
        "Tracking_Area_Code"
    ])

    arfcn_col = find_column([
        "ARFCN",
        "NR ARFCN",
        "NR_ARFCN",
        "EARFCN"
    ])

    band_col = find_column([
        "Band",
        "NR Band",
        "NR_Band",
        "LTE Band",
        "LTE_Band"
    ])

    # ========================================================
    # DETECT LOCATION COLUMNS
    # ========================================================

    latitude_col = find_column([
        "Latitude",
        "Lat",
        "LAT"
    ])

    longitude_col = find_column([
        "Longitude",
        "Long",
        "Lon",
        "Lng",
        "LONGITUDE"
    ])

    # ========================================================
    # DETECT RF PARAMETERS
    # ========================================================

    rf_columns = []

    for col in df.columns:

        normalized = normalize_column_name(col).upper()

        if normalized in [
            "RSRP",
            "RSSI",
            "RSRQ",
            "SINR"
        ]:
            rf_columns.append(col)

    # ========================================================
    # SHOW DETECTED NETWORK PARAMETERS
    # ========================================================

    st.sidebar.header("📡 Detected Network Parameters")

    if plmn_col:
        st.sidebar.success(f"PLMN: {plmn_col}")
    else:
        st.sidebar.warning("PLMN: Not detected")

    if cell_id_col:
        st.sidebar.success(f"Cell ID: {cell_id_col}")
    else:
        st.sidebar.warning("Cell ID: Not detected")

    if pci_col:
        st.sidebar.success(f"PCI: {pci_col}")
    else:
        st.sidebar.info("PCI: Not detected")

    if tac_col:
        st.sidebar.success(f"TAC: {tac_col}")
    else:
        st.sidebar.info("TAC: Not detected")

    if arfcn_col:
        st.sidebar.success(f"ARFCN: {arfcn_col}")
    else:
        st.sidebar.info("ARFCN: Not detected")

    if band_col:
        st.sidebar.success(f"Band: {band_col}")
    else:
        st.sidebar.info("Band: Not detected")

    # ========================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================

    if latitude_col is None or longitude_col is None:

        st.error(
            "❌ Latitude and Longitude columns are required."
        )

        st.stop()

    if not rf_columns:

        st.error(
            "❌ No RF parameter detected.\n\n"
            "Required at least one of: RSRP, RSSI, RSRQ, SINR."
        )

        st.stop()

    # ========================================================
    # CONVERT LOCATION DATA
    # ========================================================

    df[latitude_col] = pd.to_numeric(
        df[latitude_col],
        errors="coerce"
    )

    df[longitude_col] = pd.to_numeric(
        df[longitude_col],
        errors="coerce"
    )

    # Remove invalid coordinates

    df = df.dropna(
        subset=[
            latitude_col,
            longitude_col
        ]
    )

    if df.empty:

        st.error(
            "❌ No valid Latitude/Longitude records found."
        )

        st.stop()

    # ========================================================
    # SIDEBAR FILTERS
    # ========================================================

    st.sidebar.markdown("---")
    st.sidebar.header("🔎 Network Filters")

    # --------------------------------------------------------
    # PLMN FILTER
    # --------------------------------------------------------

    if plmn_col:

        plmn_values = (
            df[plmn_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        plmn_values = sorted(plmn_values)

        if plmn_values:

            selected_plmn = st.sidebar.selectbox(
                "📶 PLMN",
                ["All"] + plmn_values
            )

            if selected_plmn != "All":

                df = df[
                    df[plmn_col]
                    .astype(str)
                    .str.strip()
                    == selected_plmn
                ]

    # --------------------------------------------------------
    # CELL ID FILTER
    # --------------------------------------------------------

    if cell_id_col:

        cell_values = (
            df[cell_id_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        cell_values = sorted(cell_values)

        if cell_values:

            selected_cell = st.sidebar.selectbox(
                "📡 Cell ID",
                ["All"] + cell_values
            )

            if selected_cell != "All":

                df = df[
                    df[cell_id_col]
                    .astype(str)
                    .str.strip()
                    == selected_cell
                ]

    # --------------------------------------------------------
    # PCI FILTER
    # --------------------------------------------------------

    if pci_col:

        pci_values = (
            df[pci_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        pci_values = sorted(pci_values)

        if pci_values:

            selected_pci = st.sidebar.selectbox(
                "🔢 PCI",
                ["All"] + pci_values
            )

            if selected_pci != "All":

                df = df[
                    df[pci_col]
                    .astype(str)
                    .str.strip()
                    == selected_pci
                ]

    # --------------------------------------------------------
    # TAC FILTER
    # --------------------------------------------------------

    if tac_col:

        tac_values = (
            df[tac_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        tac_values = sorted(tac_values)

        if tac_values:

            selected_tac = st.sidebar.selectbox(
                "🆔 TAC",
                ["All"] + tac_values
            )

            if selected_tac != "All":

                df = df[
                    df[tac_col]
                    .astype(str)
                    .str.strip()
                    == selected_tac
                ]

    # --------------------------------------------------------
    # ARFCN FILTER
    # --------------------------------------------------------

    if arfcn_col:

        arfcn_values = (
            df[arfcn_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        arfcn_values = sorted(arfcn_values)

        if arfcn_values:

            selected_arfcn = st.sidebar.selectbox(
                "📻 ARFCN",
                ["All"] + arfcn_values
            )

            if selected_arfcn != "All":

                df = df[
                    df[arfcn_col]
                    .astype(str)
                    .str.strip()
                    == selected_arfcn
                ]

    # --------------------------------------------------------
    # BAND FILTER
    # --------------------------------------------------------

    if band_col:

        band_values = (
            df[band_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        band_values = sorted(band_values)

        if band_values:

            selected_band = st.sidebar.selectbox(
                "📡 Band",
                ["All"] + band_values
            )

            if selected_band != "All":

                df = df[
                    df[band_col]
                    .astype(str)
                    .str.strip()
                    == selected_band
                ]

    # ========================================================
    # RF PARAMETER SELECTION
    # ========================================================

    st.sidebar.markdown("---")
    st.sidebar.header("📈 RF Parameter")

    selected_param = st.sidebar.selectbox(
        "Select RF Parameter",
        rf_columns
    )

    # Convert selected RF parameter to numeric

    df[selected_param] = pd.to_numeric(
        df[selected_param],
        errors="coerce"
    )

    # Remove invalid RF values

    df = df.dropna(
        subset=[
            latitude_col,
            longitude_col,
            selected_param
        ]
    )

    if df.empty:

        st.warning(
            "⚠️ No data available after applying the selected filters."
        )

        st.stop()

    # ========================================================
    # RF VALUE RANGE
    # ========================================================

    min_val = float(
        df[selected_param].min()
    )

    max_val = float(
        df[selected_param].max()
    )

    st.sidebar.header("⚡ RF Value Filter")

    preset = st.sidebar.radio(
        "Range Preset",
        [
            "All",
            "Excellent",
            "Good",
            "Fair",
            "Poor"
        ]
    )

    # ========================================================
    # RF THRESHOLDS
    # ========================================================

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

    # ========================================================
    # APPLY RF FILTER
    # ========================================================

    if preset != "All" and preset in thresholds:

        low, high = thresholds[preset]

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

            selected_range = (
                min_val,
                max_val
            )

            df_filtered = df.copy()

        else:

            selected_range = st.sidebar.slider(
                f"Select {selected_param} range",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val)
            )

            df_filtered = df[
                (df[selected_param] >= selected_range[0]) &
                (df[selected_param] <= selected_range[1])
            ]

    # ========================================================
    # DATA COUNT
    # ========================================================

    st.success(
        f"✅ {len(df_filtered)} data points displayed."
    )

    if df_filtered.empty:

        st.warning(
            "⚠️ No data points match the selected filters."
        )

        st.stop()

    # ========================================================
    # RF STATISTICS
    # ========================================================

    st.sidebar.markdown("---")
    st.sidebar.header("📊 RF Statistics")

    st.sidebar.metric(
        f"Average {selected_param}",
        f"{df_filtered[selected_param].mean():.2f}"
    )

    st.sidebar.metric(
        "Strongest",
        f"{df_filtered[selected_param].max():.2f}"
    )

    st.sidebar.metric(
        "Weakest",
        f"{df_filtered[selected_param].min():.2f}"
    )

    # ========================================================
    # HISTOGRAM
    # ========================================================

    st.sidebar.markdown(
        f"### 📊 {selected_param} Histogram"
    )

    fig, ax = plt.subplots()

    df_filtered[selected_param].hist(
        bins=20,
        ax=ax,
        edgecolor="black"
    )

    ax.set_title(
        f"{selected_param} Distribution"
    )

    ax.set_xlabel(
        selected_param
    )

    ax.set_ylabel(
        "Frequency"
    )

    st.sidebar.pyplot(fig)

    plt.close(fig)

    # ========================================================
    # MAP CENTER
    # ========================================================

    avg_lat = df_filtered[
        latitude_col
    ].mean()

    avg_lon = df_filtered[
        longitude_col
    ].mean()

    rf_map = folium.Map(
        location=[
            avg_lat,
            avg_lon
        ],
        zoom_start=14,
        control_scale=True
    )

    # ========================================================
    # TERRAIN LAYER
    # ========================================================

    folium.TileLayer(
        tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        name="Terrain",
        attr=(
            "Map tiles by Stamen Design. "
            "Data by OpenStreetMap."
        ),
        overlay=False,
        control=True
    ).add_to(rf_map)

    # ========================================================
    # HEATMAP
    # ========================================================

    values = df_filtered[
        selected_param
    ]

    min_signal = values.min()
    max_signal = values.max()

    if max_signal == min_signal:

        heat_data = [
            [
                row[latitude_col],
                row[longitude_col],
                1.0
            ]

            for _, row
            in df_filtered.iterrows()
        ]

    else:

        heat_data = [

            [
                row[latitude_col],
                row[longitude_col],

                (
                    row[selected_param]
                    - min_signal
                )
                /
                (
                    max_signal
                    - min_signal
                )
            ]

            for _, row
            in df_filtered.iterrows()
        ]

    HeatMap(
        heat_data,
        radius=10,
        blur=15,
        min_opacity=0.5,
        max_zoom=18
    ).add_to(rf_map)

    # ========================================================
    # RF COLOR CLASSIFICATION
    # ========================================================

    def get_color(value):

        parameter = selected_param.upper()

        if parameter == "RSRP":

            if value >= -80:
                return "green"

            elif value >= -90:
                return "orange"

            elif value >= -100:
                return "darkorange"

            else:
                return "red"

        elif parameter == "RSRQ":

            if value >= -10:
                return "green"

            elif value >= -15:
                return "orange"

            elif value >= -20:
                return "darkorange"

            else:
                return "red"

        elif parameter == "SINR":

            if value >= 20:
                return "green"

            elif value >= 13:
                return "orange"

            elif value >= 0:
                return "darkorange"

            else:
                return "red"

        elif parameter == "RSSI":

            if value >= -65:
                return "green"

            elif value >= -75:
                return "orange"

            elif value >= -85:
                return "darkorange"

            else:
                return "red"

        return "gray"

    # ========================================================
    # ADD MAP MARKERS
    # ========================================================

    for _, row in df_filtered.iterrows():

        signal_value = row[selected_param]

        # -----------------------------------------------
        # Popup HTML
        # -----------------------------------------------

        popup_html = """
        <div style="font-size:14px">
        <b>📡 RF Measurement</b><br><br>
        """

        popup_html += (
            f"<b>{selected_param}:</b> "
            f"{signal_value:.2f}<br>"
        )

        # Cell ID
        if cell_id_col:

            popup_html += (
                f"<b>Cell ID:</b> "
                f"{row[cell_id_col]}<br>"
            )

        # PCI
        if pci_col:

            popup_html += (
                f"<b>PCI:</b> "
                f"{row[pci_col]}<br>"
            )

        # TAC
        if tac_col:

            popup_html += (
                f"<b>TAC:</b> "
                f"{row[tac_col]}<br>"
            )

        # ARFCN
        if arfcn_col:

            popup_html += (
                f"<b>ARFCN:</b> "
                f"{row[arfcn_col]}<br>"
            )

        # Band
        if band_col:

            popup_html += (
                f"<b>Band:</b> "
                f"{row[band_col]}<br>"
            )

        # PLMN
        if plmn_col:

            popup_html += (
                f"<b>PLMN:</b> "
                f"{row[plmn_col]}<br>"
            )

        popup_html += (
            f"<b>Latitude:</b> "
            f"{row[latitude_col]:.6f}<br>"
        )

        popup_html += (
            f"<b>Longitude:</b> "
            f"{row[longitude_col]:.6f}"
        )

        popup_html += "</div>"

        # -----------------------------------------------
        # Tooltip
        # -----------------------------------------------

        if cell_id_col:

            tooltip_text = (
                f"Cell ID: {row[cell_id_col]} | "
                f"{selected_param}: {signal_value:.2f}"
            )

        else:

            tooltip_text = (
                f"{selected_param}: "
                f"{signal_value:.2f}"
            )

        # -----------------------------------------------
        # Marker
        # -----------------------------------------------

        folium.CircleMarker(

            location=[
                row[latitude_col],
                row[longitude_col]
            ],

            radius=4,

            color=get_color(
                signal_value
            ),

            fill=True,

            fill_opacity=0.8,

            popup=folium.Popup(
                popup_html,
                max_width=350
            ),

            tooltip=tooltip_text

        ).add_to(rf_map)

    # ========================================================
    # MAP LAYER CONTROL
    # ========================================================

    folium.LayerControl().add_to(rf_map)

    # ========================================================
    # DISPLAY MAP
    # ========================================================

    st.subheader("🗺️ RF Signal Map")

    st_folium(
        rf_map,
        width=1200,
        height=650
    )

    # ========================================================
    # FILTERED DATA TABLE
    # ========================================================

    st.subheader("📋 Filtered RF Measurements")

    display_columns = []

    # Location
    display_columns.extend([
        latitude_col,
        longitude_col
    ])

    # Network information
    for col in [
        plmn_col,
        cell_id_col,
        pci_col,
        tac_col,
        arfcn_col,
        band_col
    ]:

        if col and col not in display_columns:

            display_columns.append(col)

    # RF information
    for col in rf_columns:

        if col not in display_columns:

            display_columns.append(col)

    # Remove duplicates while preserving order
    display_columns = list(
        dict.fromkeys(display_columns)
    )

    display_df = df_filtered[
        display_columns
    ].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # DOWNLOAD FILTERED DATA
    # ========================================================

    st.subheader("⬇️ Export")

    csv_data = display_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Download Filtered RF Data",
        data=csv_data,
        file_name="filtered_rf_data.csv",
        mime="text/csv"
    )

else:

    st.info(
        "👆 Upload an Excel RF log file to start."
    )
