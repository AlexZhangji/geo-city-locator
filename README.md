# GeoCityLocator

Find the nearest city to any geographic coordinates or extract location from photos with GPS metadata.

GeoCityLocator is designed for **offline use** after initial setup. It downloads a small flat file of world cities  once, then works completely offline with lightning-fast lookups for both coordinates and photos.

## Key Benefits

- **Work Anywhere**: Whether you're in a remote area or on a flight with no internet, GeoCityLocator keeps working
- **Fast Performance**: Optimized for speed with lookups in milliseconds, even on large datasets
- **Privacy-Focused**: Your location data stays on your device - no external API calls needed
- **Versatile Input**: Works with raw coordinates or extracts GPS data directly from photos
- **Low Overhead**: Minimal resource usage makes it suitable for embedded systems and mobile apps

## Features

- 🌍 Find the nearest city to any latitude/longitude coordinates
- 📷 Extract location information from photos with GPS metadata
- 🏙️ Intelligent handling of metropolitan areas and suburbs
- 🗺️ Visualization tools for location data with interactive maps
- 💾 **Download once, use offline** - cities database is cached locally
- ⚡ **Ultra-fast lookups** - optimized for quick responses even with large datasets
- 🔄 **Works offline** - perfect for travel, field work, or areas with limited connectivity
- 📱 **Low resource usage** - efficient for both desktop and mobile applications

## Installation

### Standard Installation

```bash
pip install geo-city-locator
```

### With Web Interface

```bash
pip install "geo-city-locator[web]"
```

### Development Installation 

```bash
pip install "geo-city-locator[dev]"
```

### Using uv (for faster dependency resolution)

```bash
uv pip install geo-city-locator
```

## Usage Examples

### Basic Example

```python
from geo_city_locator import get_nearest_city

# Find the nearest city to coordinates
city = get_nearest_city(40.7128, -74.0060)
print(f"You are near {city.name}, {city.country}")
# You are near New York, United States
```

### Offline Usage

```python
from geo_city_locator import NearestCityFinder

# Create a finder instance that loads the database once
finder = NearestCityFinder()

# Make as many lookups as needed with the same instance
# without any additional database loading or network requests
nyc = finder.find_nearest(40.7128, -74.0060)
paris = finder.find_nearest(48.8566, 2.3522)
tokyo = finder.find_nearest(35.6762, 139.6503)

print(f"Cities found: {nyc.name}, {paris.name}, {tokyo.name}")
```

### Finding a city with custom population threshold

```python
from geo_city_locator import NearestCityFinder

# Create a finder that only considers cities with 50,000+ population
finder = NearestCityFinder(min_population=50000)
city = finder.find_nearest(51.5074, -0.1278)
print(city)
# London, United Kingdom (51.5074, -0.1278)
```

### Extract location from a photo

```python
from geo_city_locator import get_city_from_photo

# Find the location where a photo was taken
city = get_city_from_photo("vacation.jpg")
if city:
    print(f"Photo taken near {city.name}, {city.country}")
    # Photo taken near Paris, France
```

### Command Line Usage

```bash
# Find nearest city to coordinates
geocitylocator 40.7128 -74.0060

# Find nearest city to photo location
geocitylocator --photo vacation.jpg

# Run built-in tests
geocitylocator --test
```

### Web Interface

If you installed with web dependencies, you can run the web interface:

```bash
streamlit run app.py
```

## Documentation

For detailed documentation, visit [https://geocitylocator.readthedocs.io/](https://geocitylocator.readthedocs.io/)

## Requirements

- Python 3.7+
- requests
- PIL/Pillow 
- pandas
- numpy
- appdirs

## License

MIT License
