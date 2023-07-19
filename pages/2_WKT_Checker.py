import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from shapely import wkt
from shapely.geometry import Polygon
from pyproj import CRS

def calculate_statistics(gdf, area_unit):
    # Reproject to suitable CRS for distance/area measurements
    gdf_proj = gdf.to_crs(epsg=3857)
    
    # Calculate statistics
    area = gdf_proj.area.sum()  # in square meters
    perimeter = gdf_proj.length.sum()  # in meters
    count = len(gdf)

    # Convert area to selected unit
    if area_unit == "hectares":
        area = area / 10_000
    elif area_unit == "acres":
        area = area * 0.000247105

    return area, perimeter, count

# Create Streamlit interface
st.title("WKT Viewer")

# Get WKT input
wkt_input = st.text_area("Enter WKT string:", "")

# Dropdown for area unit
area_unit = st.selectbox("Select unit for area:", ("square meters", "hectares", "acres"))

# Parse WKT
if wkt_input:
    try:
        geometry = wkt.loads(wkt_input)
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")
        
        # Create a map
        m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=13)
        
        # Add polygon(s) to the map
        for _, row in gdf.iterrows():
            folium.GeoJson(row.geometry).add_to(m)

        # Display the map
        folium_static(m)
        
        # Calculate and display statistics
        area, perimeter, count = calculate_statistics(gdf, area_unit)
        st.write(f"Area: {area} {area_unit}")
        st.write(f"Perimeter: {perimeter} meters")
        st.write(f"Number of Polygons: {count}")
    except Exception as e:
        st.write(f"Error: {str(e)}")
