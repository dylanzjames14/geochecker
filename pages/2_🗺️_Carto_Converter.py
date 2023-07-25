import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt, wkb
import folium
from streamlit_folium import folium_static
from shapely.geometry import Point, Polygon, MultiPolygon
from pyproj import CRS
import pyproj
import os
import zipfile
import base64
import shutil
import simplekml
import binascii

# Set up Streamlit layout
st.set_page_config(page_title="Spatial Annihilator", page_icon="🌍", layout="wide")
st.title('🗺️ Carto Converter')
st.write('Welcome to Carto Converter! A tool for visualizing and converting geospatial files. This page simplifies your geospatial analysis by offering an easy upload-and-visualize feature for WKT, WKB, GeoJSON, KML, and Shapefile formats. Additionally, convert your geospatial files from one common file type to another.')

with st.expander("📝 Instructions"):
    st.markdown("""
    **Step 1:** Upload a geospatial file that contains WKT, WKB, GeoJSON, KML, or Shapefile format geometries. Alternatively, you can input a WKT string or WKB hex string directly.
    
    **Step 2:** Wait as your file or WKT/WKB string is processed and presented on the map.
    
    **Step 3:** View the statistics of the geometries, such as total area (for polygons) and count of points or polygons.
    
    **Step 4:** Choose to export your file to WKT, WKB, GeoJSON, KML, or Shapefile format.
    """)

# File uploader
uploaded_file = st.file_uploader("Select a file", type=["geojson", "kml", "shp", "wkb"])

# WKT input
wkt_input = st.text_area("Or input a WKT string")

# WKB input
wkb_input = st.text_area("Or input a WKB hex string")

if uploaded_file is not None or wkt_input or wkb_input:
    # Load the file
    if uploaded_file is not None:
        if uploaded_file.type == "application/vnd.ms-excel":
            df = pd.read_csv(uploaded_file)
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
        elif uploaded_file.type == "application/geo+json":
            gdf = gpd.read_file(uploaded_file)
        elif uploaded_file.type == "application/vnd.google-earth.kml+xml":
            gdf = gpd.read_file(uploaded_file, driver='KML')
        elif uploaded_file.type == "application/x-dbf":
            gdf = gpd.read_file(uploaded_file)
        elif uploaded_file.type == "application/wkb":
            wkb_bytes = uploaded_file.getvalue()
            geometry = wkb.loads(wkb_bytes)
            gdf = gpd.GeoDataFrame(pd.DataFrame([0]), geometry=[geometry], crs="EPSG:4326")
        else:
            st.error("Invalid file type. Please upload a CSV, GeoJSON, KML, WKB, or Shapefile.")
            st.stop()
    elif wkt_input:
        gdf = gpd.GeoSeries([wkt.loads(wkt_input)], crs="EPSG:4326")
    else:
        geometry = wkb.loads(binascii.unhexlify(wkb_input))
        gdf = gpd.GeoDataFrame(pd.DataFrame([0]), geometry=[geometry], crs="EPSG:4326")

    # Area units selector
    area_units = st.selectbox("Area units", ["Square Meters", "Square Kilometers", "Square Miles", "Hectares", "Acres"])
    
    # Set Projection
    gdf = gdf.to_crs(epsg=32633)  # replace 32633 with the appropriate EPSG code

    # Create the folium map
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=15, control_scale=True)

    # Add geometries to the map
    folium.GeoJson(gdf).add_to(m)

    # Fit the map to the extents of the geometries
    m.fit_bounds(m.get_bounds())

    # Display the map
    folium_static(m)

    # Display geometry stats
    if isinstance(gdf.geometry[0], (Polygon, MultiPolygon)):
        area = gdf.area.sum()
        if area_units == "Square Meters":
            pass  # do nothing, area is already in square meters
        elif area_units == "Square Kilometers":
            area /= 1e6  # convert square meters to square kilometers
        elif area_units == "Square Miles":
            area /= 2.59e+6  # convert square meters to square miles
        elif area_units == "Hectares":
            area /= 1e4  # convert square meters to hectares
        elif area_units == "Acres":
            area /= 4046.86  # convert square meters to acres
        st.subheader(f"Total area: {area:.2f} {area_units.lower()}")
        st.subheader(f"Count of polygons: {len(gdf)}")
    elif isinstance(gdf.geometry[0], Point):
        st.subheader(f"Count of points: {len(gdf)}")

    # Export options
    export_format = st.selectbox("Export format", ["WKT", "WKB", "GeoJSON", "KML", "Shapefile"])
    if st.button("Export"):
        # Revert the CRS to WGS 84 before exporting
        gdf_wgs84 = gdf.to_crs(epsg=4326)
        if export_format == "WKT":
            wkt_str = "\n".join(gdf_wgs84.geometry.apply(lambda x: x.wkt))
            st.text(wkt_str)
        elif export_format == "WKB":
            wkb_str = gdf_wgs84.geometry.apply(lambda x: wkb.dumps(x)).tolist()[0]
            st.download_button("Download WKB", wkb_str, "output.wkb")
        elif export_format == "GeoJSON":
            gdf_wgs84.to_file("output.geojson", driver='GeoJSON')
            with open("output.geojson", "rb") as f:
                st.download_button("Download GeoJSON", f.read(), "output.geojson")
        elif export_format == "KML":
            kml = simplekml.Kml()
            for index, row in gdf_wgs84.iterrows():
                if isinstance(row.geometry, Point):
                    kml.newpoint(coords=[(row.geometry.x, row.geometry.y)])
                elif isinstance(row.geometry, (Polygon, MultiPolygon)):
                    pol = kml.newpolygon(outerboundaryis=row.geometry.exterior.coords)
            kml.save("output.kml")
            with open("output.kml", "rb") as f:
                st.download_button("Download KML", f.read(), "output.kml")
        elif export_format == "Shapefile":
            gdf_wgs84.to_file("output.shp")
            # Zip all the shapefile components
            with zipfile.ZipFile("output.zip", "w") as zipf:
                for file in os.listdir():
                    if file.startswith("output.") and file != "output.zip":
                        zipf.write(file)
            # Provide the zip file for download
            with open("output.zip", "rb") as f:
                st.download_button("Download Shapefile", f.read(), "output.zip")
            # Clean up the individual shapefile components
            for file in os.listdir():
                if file.startswith("output.") and file != "output.zip":
                    os.remove(file)
