# nearest_city.py
"""
GetCity - Find the nearest city to any latitude/longitude coordinates

This module provides functionality to find the nearest city to given geographic coordinates.
It downloads a world cities database on first use and caches it locally.

Examples:
    >>> from getcity import get_nearest_city
    >>> city = get_nearest_city(40.7128, -74.0060)
    >>> print(f"You are near {city.name}, {city.country}")
    You are near New York, United States

    >>> # With custom population threshold
    >>> from getcity import NearestCityFinder
    >>> finder = NearestCityFinder(min_population=50000)
    >>> city = finder.find_nearest(51.5074, -0.1278)
    >>> print(city)
    London, United Kingdom (51.5074, -0.1278)
    
    >>> # Extract location from photo
    >>> from getcity import get_city_from_photo
    >>> city = get_city_from_photo("vacation.jpg")
    >>> if city:
    >>>     print(f"Photo taken near {city.name}, {city.country}")
"""
import os
import csv
import math
import sys
import time
import logging
import requests
import zipfile
import appdirs
from typing import Optional, Union, Dict, Any, Tuple, List
from PIL import Image
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt

# Import photo utilities
try:
    from . import photo_utils
    from .photo_utils import extract_gps_from_photo
except ImportError:
    import photo_utils
    from photo_utils import extract_gps_from_photo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__all__ = ["City", "NearestCityFinder", "get_nearest_city", "get_city_from_photo", "get_photo_info", "haversine"]

# Configure package directories
APP_NAME = "getcity"
APP_AUTHOR = "getcitylib"


class City:
    """Represents a city with geographic coordinates and metadata."""
    
    def __init__(self, name, lat, lon, country=None, population=0):
        """Initialize a City object.
        
        Args:
            name (str): City name
            lat (float): Latitude in decimal degrees
            lon (float): Longitude in decimal degrees
            country (str, optional): Country name
            population (int, optional): City population
        """
        self.name = name
        self.lat = float(lat)
        self.lon = float(lon)
        self.country = country
        self.population = int(population) if population else 0
        
    def __repr__(self):
        return f"{self.name}, {self.country} ({self.lat}, {self.lon})"


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in kilometers.
    
    Args:
        lat1, lon1: Coordinates of first point in decimal degrees
        lat2, lon2: Coordinates of second point in decimal degrees
        
    Returns:
        float: Distance in kilometers
    """
    # Convert coordinates to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6371 * c  # Earth radius * c
    return km


def get_data_dir():
    """Get the data directory for storing city information.
    
    Returns:
        str: Path to data directory
    """
    try:
        # Use appdirs for standard locations across platforms
        data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    except (ImportError, AttributeError):
        # Fallback if appdirs not available
        data_dir = os.path.join(os.path.expanduser("~"), ".getcity")
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


class NearestCityFinder:
    """Finds the nearest city to given geographic coordinates."""
    
    DATA_URL = "https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.75.zip"
    CSV_NAME = "worldcities.csv"

    def __init__(self, data_dir=None, min_population=10000):
        """Initialize the city finder.
        
        Args:
            data_dir (str, optional): Directory to store city data. 
                                     If None, uses platform-specific data directory.
            min_population (int): Minimum population threshold for cities (0 for all cities)
        """
        self.data_dir = data_dir if data_dir else get_data_dir()
        self.min_population = min_population
        self.csv_path = os.path.join(self.data_dir, self.CSV_NAME)
        self.cities = []
        self._ensure_data()
        self._load_data()

    def _ensure_data(self):
        """Download and extract the city data if not already present."""
        start = time.time()
        if not os.path.exists(self.csv_path):
            os.makedirs(self.data_dir, exist_ok=True)
            zip_path = os.path.join(self.data_dir, "worldcities.zip")
            logging.info(f"Downloading cities data to {zip_path}...")
            resp = requests.get(self.DATA_URL, stream=True)
            resp.raise_for_status()
            
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info("Extracting CSV...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".csv"):
                        zf.extract(name, self.data_dir)
                        os.rename(os.path.join(self.data_dir, name), self.csv_path)
                        break
            logging.info(f"Downloaded and extracted data in {time.time() - start:.2f}s")
        else:
            logging.info("Data file already exists, skipping download")

    def _load_data(self):
        """Load city data from CSV file."""
        start = time.time()
        logging.info(f"Loading city data from {self.csv_path}...")
        total_entries = 0
        filtered_by_population = 0
        
        with open(self.csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Parse required fields
                    lat = float(row["lat"])
                    lon = float(row["lng"])
                    name = row.get("city", row.get("city_ascii", ""))
                    
                    # Parse optional fields with error handling
                    pop_str = row.get("population", "")
                    population = int(float(pop_str)) if pop_str else 0
                    total_entries += 1
                    
                    # Skip cities with population below threshold
                    if population < self.min_population:
                        filtered_by_population += 1
                        continue
                        
                except (ValueError, KeyError) as e:
                    # Skip rows with invalid data
                    continue
                
                # Create City object and add to list
                city = City(
                    name=name,
                    lat=lat,
                    lon=lon,
                    country=row.get("country", ""),
                    population=population,
                )
                self.cities.append(city)
        
        filtered_pct = filtered_by_population / total_entries * 100 if total_entries > 0 else 0
        logging.info(f"Loaded {len(self.cities)} cities in {time.time() - start:.2f}s")
        logging.info(f"Filtered out {filtered_by_population} cities below population threshold ({self.min_population})")
        logging.info(f"Kept {len(self.cities)}/{total_entries} cities ({100-filtered_pct:.1f}%)")
        
        # Log a few top cities by population for verification
        top_cities = sorted(self.cities, key=lambda c: c.population, reverse=True)[:5]
        logging.info(f"Top 5 cities by population:")
        for i, city in enumerate(top_cities, 1):
            logging.info(f"  {i}. {city.name}, {city.country}: {city.population:,} people")

    def find_nearest(self, lat, lon):
        """Return the City object nearest to the given latitude/longitude.
        
        Args:
            lat (float): Latitude in decimal degrees
            lon (float): Longitude in decimal degrees
            
        Returns:
            City: Nearest city object, or None if no cities found
        """
        # Validate inputs
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            logging.warning(f"Invalid coordinates: lat={lat}, lon={lon}")
            # Clamp to valid range
            lat = max(-90, min(90, lat))
            lon = max(-180, min(180, lon))
        
        if not self.cities:
            logging.error("No cities available!")
            return None
            
        start = time.time()
        best = None
        best_dist = float("inf")
        
        # Calculate distance to each city
        for city in self.cities:
            dist = haversine(lat, lon, city.lat, city.lon)
            if dist < best_dist:
                best_dist = dist
                best = city
        
        if best:
            # Check if this city should belong to a larger metro area
            original_best = best
            metro_city, metro_dist = self.check_belongs_to_bigger_city(best, lat, lon)
            if metro_city != original_best:
                logging.info(f"Upgraded result: {original_best.name}({original_best.population:,}) → {metro_city.name}({metro_city.population:,}), distance:{metro_dist:.1f}km")
                best = metro_city
            
            # Find top 3 for logging
            distances = [(city, haversine(lat, lon, city.lat, city.lon)) for city in self.cities]
            distances.sort(key=lambda x: x[1])
            top3 = [(city.name, dist) for city, dist in distances[:3]]
            
            logging.info(f"Nearest city to ({lat}, {lon}): {best.name} at {best_dist:.2f}km")
            logging.info(f"Top 3 closest: {top3}")
            logging.info(f"Found in {(time.time() - start) * 1000:.2f}ms")
        
        return best
        
    def find_nearest_from_photo(self, image_path: Union[str, Image.Image]) -> Optional[City]:
        """Find the nearest city to the location where a photo was taken.
        
        Args:
            image_path: Path to image file or PIL Image object
            
        Returns:
            City object or None if no GPS data in photo or no nearby city found
        """
        try:
            # Extract GPS coordinates from photo
            coords = photo_utils.extract_gps_from_photo(image_path)
            
            if not coords:
                logging.warning("No GPS coordinates found in photo")
                return None
                
            lat, lon = coords
            logging.info(f"Extracted coordinates from photo: ({lat}, {lon})")
            
            # Find nearest city
            return self.find_nearest(lat, lon)
            
        except Exception as e:
            logging.error(f"Error finding city from photo: {e}")
            return None

    def check_belongs_to_bigger_city(self, city, lat, lon, radius=10, population_ratio=10, 
                                    min_metro_population=1000000, self_sufficient_population=1000000):
        """Check if a city should be considered part of a nearby larger metro area.
        
        Criteria:
        1. Distance is within specified radius (km)
        2. Larger city's population is at least population_ratio times bigger
        3. Larger city's population exceeds min_metro_population
        4. If current city already exceeds self_sufficient_population, no upgrade needed
        
        Args:
            city (City): Currently identified nearest city
            lat (float): Query point latitude
            lon (float): Query point longitude
            radius (float): Maximum distance threshold in km
            population_ratio (int): Population ratio threshold
            min_metro_population (int): Minimum population for metro cities
            self_sufficient_population (int): Threshold above which cities are considered major
            
        Returns:
            tuple: (City, float) - Metro city and distance, or original city and 0
        """
        # If current city is already large enough, no upgrade needed
        if city.population >= self_sufficient_population:
            logging.debug(f"{city.name} population {city.population:,} exceeds {self_sufficient_population:,} threshold, no upgrade needed")
            return city, 0
            
        # Only consider larger cities
        bigger_cities = [c for c in self.cities 
                        if c.population > city.population * population_ratio 
                        and c.population >= min_metro_population]
        
        for bigger_city in bigger_cities:
            distance = haversine(lat, lon, bigger_city.lat, bigger_city.lon)
            if distance <= radius:
                return bigger_city, distance
                
        return city, 0  # No suitable larger city found


# Global instance for simpler API
_finder = None

def get_nearest_city(lat, lon, min_population=10000):
    """Find the nearest city to the given coordinates.
    
    This is a convenience function that creates or reuses a global NearestCityFinder instance.
    
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        min_population (int, optional): Minimum population threshold for cities
        
    Returns:
        City: Nearest city object, or None if no cities found
    """
    global _finder
    if _finder is None or _finder.min_population != min_population:
        _finder = NearestCityFinder(min_population=min_population)
    return _finder.find_nearest(lat, lon)


def get_city_from_photo(image_path: Union[str, Image.Image], min_population=10000) -> Optional[City]:
    """Find the nearest city to the location where a photo was taken.
    
    Args:
        image_path: Path to image file or PIL Image object
        min_population (int, optional): Minimum population threshold for cities
        
    Returns:
        City object or None if no GPS data in photo or no nearby city found
    """
    global _finder
    if _finder is None or _finder.min_population != min_population:
        _finder = NearestCityFinder(min_population=min_population)
    return _finder.find_nearest_from_photo(image_path)


def get_photo_info(image_or_path):
    """
    Extract GPS information from a photo using photo_utils
    
    Args:
        image_or_path: PIL Image object or path to an image file
        
    Returns:
        Dictionary with the following keys:
        - success: Boolean indicating if extraction was successful
        - latitude: Latitude value if success is True
        - longitude: Longitude value if success is True
        - coordinates: Tuple of (latitude, longitude) if success is True
        - error: Error message if success is False
        - exif_data: Dictionary with extracted EXIF data (if available)
        - gps_data: Dictionary with extracted GPS data (if available)
    """
    try:
        # Use the more comprehensive function from photo_utils
        result = photo_utils.get_coordinates_with_details(image_or_path)
        
        # Result already has the right format
        return result
        
    except Exception as e:
        logger.error(f"Error extracting GPS from photo: {e}")
        return {
            "success": False,
            "error": str(e),
            "latitude": None,
            "longitude": None,
            "coordinates": None,
            "exif_data": {},
            "gps_data": {}
        }


def run_tests():
    """Run built-in test cases."""
    logging.info("Running test cases...")
    t0 = time.time()
    finder = NearestCityFinder()
    loaded_time = time.time() - t0
    logging.info(f"Data loaded in {loaded_time:.2f}s")
    
    # Show some US cities for verification
    us_cities = [city for city in finder.cities if city.country == "United States"]
    us_cities.sort(key=lambda c: c.population, reverse=True)
    logging.info("\n=== Top US cities in dataset ===")
    for i, city in enumerate(us_cities[:5], 1):
        logging.info(f"  {i}. {city.name} - {city.population:,} people ({city.lat}, {city.lon})")
    logging.info("")
    
    # Test cases - coordinates and expected city names
    tests = [
        ((40.7128, -74.0060), "New York"),
        ((51.5074, -0.1278), "London"),
        ((35.6895, 139.6917), "Tokyo"),
        ((-33.8688, 151.2093), "Sydney"),
        # Metro area relation test cases
        ((35.6938, 139.7035), "Tokyo"),  # Shinjuku coordinates, should be Tokyo
        ((38.8951, -77.0364), "Washington"),  # Washington DC area
        ((22.2796, 114.1716), "Hong Kong"),  # Central Hong Kong
    ]
    
    passed = 0
    logging.info("\n=== Running test cases ===")
    for (lat, lon), expected in tests:
        logging.info(f"\nTEST: Finding nearest to ({lat}, {lon}) - expecting: {expected}")
        tq0 = time.time()
        city = finder.find_nearest(lat, lon)
        query_time = time.time() - tq0
        
        if not city:
            logging.error("✗ FAILED - No city found!")
            logging.warning(f"No city found for ({lat}, {lon})")
            continue
            
        logging.info(f"Query ({lat}, {lon}) -> {city.name} in {query_time*1000:.2f}ms")
        
        # Check if result contains expected name (flexible matching)
        if expected.lower() in city.name.lower():
            logging.info(f"✓ PASSED: {expected} matches {city.name} (distance: {haversine(lat, lon, city.lat, city.lon):.2f}km)")
            passed += 1
        else:
            logging.error(f"✗ Failed: Expected {expected}, got {city.name}")
            # Show nearby cities to help understand the mismatch
            nearby = [(c.name, haversine(lat, lon, c.lat, c.lon)) 
                     for c in finder.cities if expected.lower() in c.name.lower()]
            nearby.sort(key=lambda x: x[1])
            if nearby:
                logging.info(f"Nearest '{expected}' entries: {nearby[:3]}")
    
    total_time = time.time() - t0
    logging.info(f"Tests: {passed}/{len(tests)} passed in {total_time:.2f}s total")


def main():
    """Command-line interface entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m nearest_city <lat> <lon>")
        print("  python -m nearest_city --photo <photo_path>")
        print("  python -m nearest_city --test")
        return
        
    if sys.argv[1] == "--test":
        run_tests()
        return
        
    if sys.argv[1] == "--photo" and len(sys.argv) >= 3:
        photo_path = sys.argv[2]
        try:
            # Extract photo info
            info = get_photo_info(photo_path)
            
            if info["lat"] is not None and info["lon"] is not None:
                print(f"Photo coordinates: ({info['lat']}, {info['lon']})")
                
                # Find nearest city
                city = get_nearest_city(info["lat"], info["lon"])
                if city:
                    distance = haversine(info["lat"], info["lon"], city.lat, city.lon)
                    print(f"Nearest city: {city.name}, {city.country} ({distance:.2f}km away)")
                else:
                    print("No city found near photo location")
            else:
                print(f"No GPS data found in photo: {info['error']}")
                
        except Exception as e:
            print(f"Error processing photo: {e}")
        
        return
            
    try:
        if len(sys.argv) >= 3:
            lat, lon = float(sys.argv[1]), float(sys.argv[2])
            city = get_nearest_city(lat, lon)
            if city:
                print(f"Nearest city to ({lat}, {lon}): {city}")
            else:
                print(f"No city found near ({lat}, {lon})")
        else:
            print("Error: Both latitude and longitude are required")
    except ValueError:
        print("Error: Coordinates must be valid numbers")


if __name__ == "__main__":
    main() 