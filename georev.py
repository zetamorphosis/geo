import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen

st.title("Map Geolocation Viewer")

uploaded_file = st.file_uploader("Upload CSV file with Geolocation or Longitude and Latitude", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    st.write("Preview Data:")
    st.dataframe(df)

    locations = []

    if 'Geolocation' in df.columns:
        for loc in df['Geolocation']:
            try:
                lat, lon = map(float, loc.split(','))
                locations.append([lat, lon])
            except:
                pass
    elif 'Longitude' in df.columns and 'Latitude' in df.columns:
        try:
            df['Longitude'] = df['Longitude'].astype(float)
            df['Latitude'] = df['Latitude'].astype(float)
            locations = df[['Latitude', 'Longitude']].dropna().values.tolist()
        except ValueError:
            st.error("Kolom Longitude dan Latitude harus berupa angka.")
    
    if locations:
        avg_lat = sum([loc[0] for loc in locations]) / len(locations)
        avg_lon = sum([loc[1] for loc in locations]) / len(locations)
    else:
        avg_lat, avg_lon = -6.119496, 106.662934

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

    Fullscreen(position='topright').add_to(m)

    for loc in locations:
        folium.Marker(
            location=loc, 
            popup=f"Location: {loc[0]}, {loc[1]}", 
            icon=folium.Icon(icon="info-sign")
        ).add_to(m)

    st_folium(m, width=700, height=500)

    if not locations:
        st.error("Kolom 'Geolocation' atau 'Longitude' dan 'Latitude' tidak ditemukan dalam file CSV.")
