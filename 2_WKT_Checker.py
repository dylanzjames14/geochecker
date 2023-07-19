import streamlit as st
import geopandas as gpd
from shapely import wkt
import folium
from folium import Map
from streamlit_folium import folium_static
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point
from pyproj import CRS
import json
from zipfile import ZipFile
import os
import shutil
import numpy as np

st.set_page_config(page_title="Geochecker 🌍")

st.title("🌍 WKT Checker")
st.write("This tool lets you input a WKT string, gives you statistics about the polygon or point file, \
allows you to visualize it spatially, and enables exporting the file into other formats like shapefile.zip, kml, or geojson.")

with st.expander("Show Instructions"):
    st.markdown("""
    **How to use this tool**:

    - Enter your WKT string in the input field and press 'View'.
    - View interesting statistics about the polygon or point file.
    - Visualize your geometry on the interactive map.
    - Export your data to a variety of formats.
    """)

wkt_string = st.text_area("Enter your WKT string here:", "")

try:
    if 'geom' not in st.session_state or st.session_state.wkt_string != wkt_string:
        geom = wkt.loads(wkt_string)
        gdf = gpd.GeoDataFrame(index=[0], geometry=[geom])
        gdf = gdf.set_crs("EPSG:4326")  # WGS 84
        gdf_meters = gdf.to_crs("EPSG:3395")  # Convert to World Mercator EPSG:3395 for meter calculations

        st.session_state.geom = geom
        st.session_state.gdf = gdf
        st.session_state.gdf_meters = gdf_meters
        st.session_state.wkt_string = wkt_string
except Exception as e:
    st.error(f"Failed to parse WKT string. Please make sure it's valid. Error: {str(e)}")
    st.stop()

if st.button("View"):
    geom = st.session_state.geom
    gdf = st.session_state.gdf
    gdf_meters = st.session_state.gdf_meters

    if gdf.geometry[0].geom_type == 'Point':
        st.write("This is a Point geometry, no area or length to display.")
    else:
        unit = st.selectbox("Select your preferred unit for area", ("m²", "Acres", "Hectares"))

        area = gdf_meters.geometry[0].area  # Area in sq. meters
        perimeter = gdf_meters.geometry[0].length  # Perimeter in meters

        st.write(f"Perimeter (m):", perimeter)

        if unit == "Acres":
            area /= 4046.86  # convert to acres
        elif unit == "Hectares":
            area /= 10000  # convert to hectares

        st.write(f"Area ({unit}):", area)

    m = Map(location=[geom.centroid.y, geom.centroid.x], zoom_start=10)
    folium.GeoJson(gdf).add_to(m)
    map_boundary = gdf.geometry[0].bounds
    m.fit_bounds([[map_boundary[1], map_boundary[0]], [map_boundary[3], map_boundary[2]]])

    folium_static(m)

    option = st.selectbox("Choose the export format", ("shapefile.zip", "kml", "geojson"))

    if st.button("Export"):
        if option == "shapefile.zip":
            filename = 'output.shp'
            gdf.to_file(filename)
            with ZipFile('shapefile.zip', 'w') as zipObj:
                for folderName, subfolders, filenames in os.walk('./'):
                    for file in filenames:
                        if file.endswith('.shp') or file.endswith('.shx') or file.endswith('.prj') or file.endswith('.dbf'):
                            filePath = os.path.join(folderName, file)
                            zipObj.write(filePath)
            shutil.rmtree('./')
            st.download_button("Download shapefile.zip", "shapefile.zip")

        elif option == "kml":
            gdf.to_file("output.kml", driver="KML")
            st.download_button("Download KML", "output.kml")
            os.remove("output.kml")

        elif option == "geojson":
            gdf.to_file("output.geojson", driver="GeoJSON")
            st.download_button("Download GeoJSON", "output.geojson")
            os.remove("output.geojson")
