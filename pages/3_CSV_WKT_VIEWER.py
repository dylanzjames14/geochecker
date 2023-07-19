# streamlit_app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt, geometry
import pydeck as pdk

def is_valid_wkt(wkt_string):
    try:
        wkt.loads(wkt_string)
        return True
    except:
        return False

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
    view_state = pdk.ViewState(latitude=gdf.centroid.y.mean(), longitude=gdf.centroid.x.mean(), zoom=10)

    # Render the map
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

st.title('CSV Geo Plotter')

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    string_columns = data.select_dtypes(include=['object']).columns  # only select columns with string data
    column_name = st.selectbox('Select the WKT column', string_columns)

    # Check for valid WKT strings
    if all(data[column_name].apply(is_valid_wkt)):
        # Parse WKT strings to geometric objects
        try:
            data[column_name] = data[column_name].apply(wkt.loads)
        except Exception as e:
            st.error(f"Error parsing WKT data: {e}")
            raise

        # Convert DataFrame to GeoDataFrame
        gdf = gpd.GeoDataFrame(data, geometry=data[column_name])

        # Convert any non-geometry data to None
        gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom if isinstance(geom, geometry.base.BaseGeometry) else None)

        plot_map(gdf)
    else:
        st.error("Selected column contains invalid WKT strings.")