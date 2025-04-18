# GeoCity

Find the nearest city to any geographic coordinates or extract location from photos with GPS metadata.

## Features

- 🌍 Find the nearest city to any latitude/longitude coordinates
- 📷 Extract location information from photos with GPS metadata
- 🏙️ Intelligent handling of metropolitan areas and suburbs
- 🗺️ Visualization tools for location data with interactive maps
- 💾 Automatic downloading and caching of world cities database

## Installation

### Standard Installation

```bash
pip install geo-city
```

### With Web Interface

```bash
pip install "geo-city[web]"
```

### Development Installation 

```bash
pip install "geo-city[dev]"
```

### Using uv (for faster dependency resolution)

```bash
uv pip install geo-city
```

## Usage Examples

### Basic Example

```python
from geo_city import get_nearest_city

# Find the nearest city to coordinates
city = get_nearest_city(40.7128, -74.0060)
print(f"You are near {city.name}, {city.country}")
# You are near New York, United States
```

### Finding a city with custom population threshold

```python
from geo_city import NearestCityFinder

# Create a finder that only considers cities with 50,000+ population
finder = NearestCityFinder(min_population=50000)
city = finder.find_nearest(51.5074, -0.1278)
print(city)
# London, United Kingdom (51.5074, -0.1278)
```

### Extract location from a photo

```python
from geo_city import get_city_from_photo

# Find the location where a photo was taken
city = get_city_from_photo("vacation.jpg")
if city:
    print(f"Photo taken near {city.name}, {city.country}")
    # Photo taken near Paris, France
```

### Command Line Usage

```bash
# Find nearest city to coordinates
geocity 40.7128 -74.0060

# Find nearest city to photo location
geocity --photo vacation.jpg

# Run built-in tests
geocity --test
```

### Web Interface

If you installed with web dependencies, you can run the web interface:

```bash
streamlit run app.py
```

## Documentation

For detailed documentation, visit [https://geocity.readthedocs.io/](https://geocity.readthedocs.io/)

## Requirements

- Python 3.7+
- requests
- PIL/Pillow 
- pandas
- numpy
- appdirs

## License

MIT License
