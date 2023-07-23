import streamlit as st
import leafmap.foliumap as leafmap
from PIL import Image

st.set_page_config(page_title="Spatial Annihilator", page_icon="🌍", layout="wide")

# Open the image file
img = Image.open('/data/image.png')

st.title("Welcome to Spatial Annihilator!")
st.write("A tool for analyzing common geospatial files and formats!")

# Display the image
st.image(img, use_column_width=True)
