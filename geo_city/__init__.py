"""
GeoCity - Find the nearest city to any latitude/longitude coordinates or photos with GPS data.
"""

from .nearest_city import (
    City,
    NearestCityFinder,
    get_nearest_city,
    get_city_from_photo,
    get_photo_info,
    haversine,
)

__version__ = "0.1.0"
__all__ = [
    "City",
    "NearestCityFinder",
    "get_nearest_city",
    "get_city_from_photo",
    "get_photo_info",
    "haversine",
] 