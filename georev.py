import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from collections import Counter
import csv
import numpy as np

st.title("Map Geolocation")

uploaded_files = st.file_uploader(
    "Upload file CSV (boleh lebih dari 1)", 
    type="csv", 
    accept_multiple_files=True
)

if uploaded_files:
    all_dfs = []
    all_columns_info = []

    for idx, uploaded_file in enumerate(uploaded_files):
        sample = uploaded_file.read(2048).decode('utf-8')
        uploaded_file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ','

        df = pd.read_csv(uploaded_file, sep=delimiter)
        df.columns = df.columns.str.strip()
        df.replace('-', np.nan, inplace=True)

        all_columns_info.append(f"**File {idx + 1}** (`{uploaded_file.name}`): " + " | ".join(df.columns.tolist()))

        if 'Geolocation' in df.columns:
            df = df.dropna(subset=['Geolocation'])
        if 'Longitude' in df.columns and 'Latitude' in df.columns:
            df = df.dropna(subset=['Longitude', 'Latitude'])

        df['source_file'] = uploaded_file.name
        all_dfs.append(df)

        st.markdown(f"### 📄 Preview File {idx + 1}: `{uploaded_file.name}`")
        st.dataframe(df)

    st.markdown("### 📌 Kolom tersedia di masing-masing file:")
    for col_info in all_columns_info:
        st.markdown(col_info)

    df_with_ab = [df for df in all_dfs if 'A Number' in df.columns and 'B Number' in df.columns]
    df_no_ab = [df for df in all_dfs if not ('A Number' in df.columns and 'B Number' in df.columns)]

    if df_with_ab:
        df_ab = pd.concat(df_with_ab, ignore_index=True)
        unique_a = sorted(df_ab['A Number'].dropna().unique())
        unique_b = sorted(df_ab['B Number'].dropna().unique())

        unique_a_display = ['All'] + unique_a
        unique_b_display = ['All'] + unique_b

        st.markdown("### 📞 Filter Panggilan")
        selected_a = st.multiselect("Pilih A Number (Pemanggil):", unique_a_display, default=['All'])
        selected_b = st.multiselect("Pilih B Number (Penerima):", unique_b_display, default=['All'])

        if 'All' not in selected_a:
            df_ab = df_ab[df_ab['A Number'].isin(selected_a)]
        if 'All' not in selected_b:
            df_ab = df_ab[df_ab['B Number'].isin(selected_b)]

        df = pd.concat([df_ab] + df_no_ab, ignore_index=True)
    else:
        df = pd.concat(all_dfs, ignore_index=True)

    locations = []

    if 'Geolocation' in df.columns:
        for loc in df['Geolocation'].dropna():
            try:
                lat, lon = map(float, loc.split(','))
                locations.append((lat, lon))
                df.loc[df['Geolocation'] == loc, 'Latitude'] = lat
                df.loc[df['Geolocation'] == loc, 'Longitude'] = lon
            except:
                pass

    if 'Longitude' in df.columns and 'Latitude' in df.columns:
        try:
            df['Longitude'] = df['Longitude'].astype(float)
            df['Latitude'] = df['Latitude'].astype(float)
            latlong_locations = list(zip(df['Latitude'], df['Longitude']))
            locations.extend(latlong_locations)
        except:
            st.warning("Nilai Latitude/Longitude tidak valid di beberapa baris.")

    if locations:
        location_counts = Counter(locations)

        valid_lats = [loc[0] for loc in locations if pd.notna(loc[0])]
        valid_lons = [loc[1] for loc in locations if pd.notna(loc[1])]

        if valid_lats and valid_lons:
            avg_lat = sum(valid_lats) / len(valid_lats)
            avg_lon = sum(valid_lons) / len(valid_lons)

            unique_locations = list(location_counts.keys())
            color_map = {loc: f"#{abs(hash(loc)) % 0xFFFFFF:06x}" for loc in unique_locations}

            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
            Fullscreen(position='topright').add_to(m)

            for loc, count in location_counts.items():
                if pd.notna(loc[0]) and pd.notna(loc[1]):
                    color = color_map.get(loc, "#0000FF")

                    matched = df[
                        (df['Latitude'].round(6) == round(loc[0], 6)) & 
                        (df['Longitude'].round(6) == round(loc[1], 6))
                    ]

                    detail_rows = []
                    for _, row in matched.iterrows():
                        detail = ""
                        skip_cols = ['Latitude', 'Longitude', 'Geolocation', 'source_file']

                        for col, val in row.items():
                            if col not in skip_cols and pd.notna(val):
                                detail += f"<b>{col}:</b> {val}<br>"

                        if detail:
                            detail_rows.append(detail)

                    isi_popup = f"""
                    <b>Location:</b> {loc[0]}, {loc[1]}<br>
                    <b>Jumlah Kemunculan:</b> {count}<br><hr>
                    {"<hr>".join(detail_rows) if detail_rows else ""}
                    """

                    folium.Marker(
                        location=loc,
                        popup=folium.Popup(f"""
                        <div style='max-height:300px; overflow-y:auto;'>
                            {isi_popup}
                        </div>
                        """, max_width=400),
                        tooltip=f"{loc[0]}, {loc[1]}",
                        icon=folium.DivIcon(html=f'''
                            <div style="background-color:{color}; color:white; 
                                        border-radius:50%; width:24px; height:24px; 
                                        text-align:center; line-height:24px; 
                                        font-size:12px;">{count}</div>
                        ''')
                    ).add_to(m)

            st.markdown("### 🗺️ Peta Lokasi:")
            st_folium(m, width=700, height=500)
        else:
            st.warning("Tidak ada koordinat valid untuk dihitung titik tengah.")
    else:
        st.error("Tidak ditemukan data lokasi yang valid dari file yang diupload.")
