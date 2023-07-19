# streamlit_app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import pydeck as pdk

def plot_map(gdf):
    """
    This function gets a GeoDataFrame and plots it on a map.
    """

    # Change the geometry column to a string format that pydeck can understand
    gdf['geometry'] = gdf['geometry'].apply(lambda x: str(x))

    # Create a new pydeck layer for the polygons
    layer = pdk.Layer(
        "PolygonLayer",
        gdf,
        get_polygon="geometry",
        get_fill_color=[0, 0, 255],  # Blue color fill
        pickable=True,
        extruded=False,
    )

    # Set the viewport to the center of the map
    view_state = pdk.ViewState(latitude=gdf.geometry.centroid.y.mean(), longitude=gdf.geometry.centroid.x.mean(), zoom=10)

    # Render the map
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))


st.title('CSV Geo Plotter')

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    column_name = st.selectbox('Select the WKT column', data.columns)

    # Parse WKT strings to geometric objects
    data[column_name] = data[column_name].apply(wkt.loads)
    
    # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry=data[column_name])

    plot_map(gdf)
