import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from collections import Counter
import csv
import numpy as np

st.title("Map Geolocation")

uploaded_file = st.file_uploader("Upload file CSV dengan Geolocation atau Longitude & Latitude", type="csv")

if uploaded_file is not None:
    # Deteksi delimiter otomatis
    sample = uploaded_file.read(2048).decode('utf-8')
    uploaded_file.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ','  # fallback default
    df = pd.read_csv(uploaded_file, sep=delimiter)
    df.columns = df.columns.str.strip()

    # Tampilkan kolom
    st.write("Kolom tersedia di file ini:", df.columns.tolist())

    # Tangani nilai '-' sebagai NaN
    df.replace('-', np.nan, inplace=True)

    # Hapus baris kosong pada kolom lokasi
    if 'Geolocation' in df.columns:
        df = df.dropna(subset=['Geolocation'])
    elif 'Longitude' in df.columns and 'Latitude' in df.columns:
        df = df.dropna(subset=['Longitude', 'Latitude'])

    st.write("Preview Data:")
    st.dataframe(df)

    locations = []

    if 'Geolocation' in df.columns:
        for loc in df['Geolocation']:
            try:
                lat, lon = map(float, loc.split(','))
                locations.append((lat, lon))
            except:
                pass
    elif 'Longitude' in df.columns and 'Latitude' in df.columns:
        try:
            df['Longitude'] = df['Longitude'].astype(float)
            df['Latitude'] = df['Latitude'].astype(float)
            locations = list(zip(df['Latitude'], df['Longitude']))
        except ValueError:
            st.error("Kolom Longitude dan Latitude harus berupa angka.")

    if locations:
        location_counts = Counter(locations)

        avg_lat = sum([loc[0] for loc in locations]) / len(locations)
        avg_lon = sum([loc[1] for loc in locations]) / len(locations)

        unique_locations = list(location_counts.keys())
        color_map = {loc: f"#{abs(hash(loc)) % 0xFFFFFF:06x}" for loc in unique_locations}

        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        Fullscreen(position='topright').add_to(m)

        for loc, count in location_counts.items():
            color = color_map.get(loc, "#0000FF")
            folium.Marker(
                location=loc,
                popup=f"Location: {loc[0]}, {loc[1]} (Jumlah Kemunculan: {count})",
                tooltip=f"Lat: {loc[0]}, Lon: {loc[1]}\nJumlah Kemunculan: {count}",
                icon=folium.DivIcon(html=f'<div style="background-color:{color}; color:white; border-radius:50%; width:24px; height:24px; text-align:center; line-height:24px; font-size:12px;">{count}</div>')
            ).add_to(m)

        st_folium(m, width=700, height=500)
    else:
        st.error("Kolom 'Geolocation' atau 'Longitude' dan 'Latitude' tidak ditemukan atau kosong dalam file CSV.")
