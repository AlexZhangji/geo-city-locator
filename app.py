import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ExifTags
import folium
from streamlit_folium import folium_static
import io
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import from geo_city package
from geo_city import get_nearest_city, NearestCityFinder, haversine, get_photo_info

st.set_page_config(
    page_title="GeoCity - Find the nearest city",
    page_icon="🌎",
    layout="wide",
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem; 
        color: #0277BD;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 0.5rem solid #4CAF50;
    }
    .info-box {
        background-color: #E3F2FD; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 0.5rem solid #2196F3;
    }
    .warning-box {
        background-color: #FFF8E1; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 0.5rem solid #FFC107;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>GeoCity Explorer 🌎</h1>", unsafe_allow_html=True)
st.markdown("""
Find the nearest cities to any geographic coordinates or extract location from photos.
This app demonstrates the functionality of the `geo-city` library.
""")

# Initialize the city finder
@st.cache_resource
def get_finder(min_population=10000):
    return NearestCityFinder(min_population=min_population)

# Create a map with markers
def create_map(center_lat, center_lon, cities=None, zoom_start=10):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    # Add marker for the search location
    folium.Marker(
        [center_lat, center_lon],
        popup="Your Location",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)
    
    # Add markers for nearby cities
    if cities:
        for i, city in enumerate(cities):
            folium.Marker(
                [city.lat, city.lon],
                popup=f"<b>{city.name}, {city.country}</b><br>Population: {city.population:,}<br>Distance: {city.distance:.2f} km",
                icon=folium.Icon(color="blue" if i > 0 else "green", icon="city", prefix="fa"),
            ).add_to(m)
            
            # Add a line connecting the search location to the nearest city
            if i == 0:
                folium.PolyLine(
                    [[center_lat, center_lon], [city.lat, city.lon]],
                    color="green",
                    weight=3,
                    opacity=0.7,
                ).add_to(m)
    
    return m

# Tabs for different features
tab1, tab2 = st.tabs(["📍 Find by Coordinates", "📷 Extract from Photo"])

# ----- Tab 1: Find by Coordinates -----
with tab1:
    st.markdown("<h2 class='sub-header'>Find Cities by Coordinates</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=40.7128, step=0.0001, format="%.6f")
        lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-74.0060, step=0.0001, format="%.6f")
        top_k = st.slider("Number of nearest cities to show", min_value=1, max_value=10, value=5)
        min_pop = st.select_slider(
            "Minimum city population",
            options=[0, 5000, 10000, 50000, 100000, 500000, 1000000],
            value=10000,
            format_func=lambda x: f"{x:,}"
        )
        
        search_button = st.button("🔍 Find Nearest Cities")
    
    with col2:
        # Pre-populated examples
        st.markdown("#### Try these examples:")
        example_locations = {
            "New York, USA": (40.7128, -74.0060),
            "Tokyo, Japan": (35.6895, 139.6917),
            "Paris, France": (48.8566, 2.3522),
            "Sydney, Australia": (-33.8688, 151.2093),
            "Cairo, Egypt": (30.0444, 31.2357),
            "Rio de Janeiro, Brazil": (-22.9068, -43.1729)
        }
        
        for name, coords in example_locations.items():
            if st.button(f"📍 {name}", key=f"btn_{name}"):
                lat, lon = coords
                search_button = True
    
    # Display results
    if search_button:
        with st.spinner("Searching for cities..."):
            finder = get_finder(min_population=min_pop)
            nearest_city = finder.find_nearest(lat, lon)
            
            if nearest_city:
                # Get top K nearest cities
                all_cities = [(city, haversine(lat, lon, city.lat, city.lon)) for city in finder.cities]
                all_cities.sort(key=lambda x: x[1])
                top_cities = []
                
                for city, distance in all_cities[:top_k]:
                    # Add distance attribute to city object
                    city.distance = distance
                    top_cities.append(city)
                
                # Display nearest city
                st.markdown(f"""
                <div class='success-box'>
                    <h3>🏙️ Nearest City: {nearest_city.name}, {nearest_city.country}</h3>
                    <p>Population: {nearest_city.population:,}</p>
                    <p>Distance: {top_cities[0].distance:.2f} km</p>
                    <p>Coordinates: ({nearest_city.lat:.6f}, {nearest_city.lon:.6f})</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display map
                st.markdown("### 🗺️ Map View")
                map_col1, map_col2 = st.columns([3, 1])
                
                with map_col1:
                    m = create_map(lat, lon, top_cities)
                    folium_static(m)
                
                with map_col2:
                    st.markdown("### Top Cities")
                    for i, city in enumerate(top_cities):
                        st.markdown(f"""
                        <div style="margin-bottom: 10px; padding: 10px; background-color: {'#E8F5E9' if i == 0 else '#F5F5F5'}; border-radius: 5px;">
                            <b>{i+1}. {city.name}, {city.country}</b><br>
                            Population: {city.population:,}<br>
                            Distance: {city.distance:.2f} km
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("No cities found. Try adjusting the minimum population threshold.")

# ----- Tab 2: Extract from Photo -----
with tab2:
    st.markdown("<h2 class='sub-header'>Extract Location from Photo</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='info-box'>
        <p>Upload a photo with GPS data embedded in EXIF metadata. Most smartphone photos contain this information
        unless it has been stripped for privacy reasons.</p>
        <p><b>Note:</b> Your photo is processed locally and not sent to any server.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose a photo...", type=["jpg", "jpeg", "png", "heic"])
    
    if uploaded_file is not None:
        try:
            # Display the image
            image_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(image_bytes))
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(image, caption="Uploaded Image", use_column_width=True)
            
            with col2:
                # Extract GPS coordinates using our photo_utils library
                logger.info(f"Extracting GPS data from uploaded image")
                photo_info = get_photo_info(image)
                
                if photo_info["success"] and photo_info["coordinates"]:
                    lat, lon = photo_info["latitude"], photo_info["longitude"]
                    logger.info(f"Successfully extracted coordinates: ({lat}, {lon})")
                    st.markdown(f"""
                    <div class='success-box'>
                        <h3>📍 GPS Data Extracted</h3>
                        <p>Latitude: {lat:.6f}</p>
                        <p>Longitude: {lon:.6f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Find nearest city
                    with st.spinner("Finding nearest city..."):
                        logger.info(f"Finding nearest city to coordinates: ({lat}, {lon})")
                        nearest_city = get_nearest_city(lat, lon)
                        
                        if nearest_city:
                            distance = haversine(lat, lon, nearest_city.lat, nearest_city.lon)
                            # Add distance attribute to the city object
                            nearest_city.distance = distance
                            logger.info(f"Found nearest city: {nearest_city.name}, {nearest_city.country} at {distance:.2f}km")
                            st.markdown(f"""
                            <div class='info-box'>
                                <h3>🏙️ Photo taken near: {nearest_city.name}, {nearest_city.country}</h3>
                                <p>Population: {nearest_city.population:,}</p>
                                <p>Distance: {distance:.2f} km</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Show map
                            st.markdown("### 🗺️ Photo Location")
                            logger.info(f"Creating map centered at ({lat}, {lon}) with marker for {nearest_city.name}")
                            m = create_map(lat, lon, [nearest_city])
                            folium_static(m)
                        else:
                            logger.warning(f"No cities found near coordinates: ({lat}, {lon})")
                            st.error("No cities found near this location.")
                else:
                    error_msg = photo_info.get("error", "Unknown error")
                    logger.warning(f"Failed to extract GPS data from image: {error_msg}")
                    st.markdown(f"""
                    <div class='warning-box'>
                        <h3>⚠️ No GPS Data Found</h3>
                        <p>This image doesn't contain GPS information in its EXIF metadata.</p>
                        <p>Possible reasons:</p>
                        <ul>
                            <li>The photo was taken with a device that doesn't record GPS</li>
                            <li>Location services were disabled when taking the photo</li>
                            <li>GPS data was removed for privacy (common when sharing online)</li>
                            <li>The image was edited and saved in a way that stripped EXIF data</li>
                        </ul>
                        <p>Error: {error_msg}</p>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            st.error(f"Error processing image: {str(e)}")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Powered by the <code>geo-city</code> library | Map data © OpenStreetMap contributors</p>
    <p>City database from <a href="https://simplemaps.com/data/world-cities" target="_blank">SimpleMaps</a></p>
</div>
""", unsafe_allow_html=True) 