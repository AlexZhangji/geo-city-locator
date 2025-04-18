"""
Photo processing utilities for extracting GPS and metadata from images.

This module provides functions to extract GPS coordinates and other metadata
from digital photos, supporting various formats and devices (iOS, Android, etc.).
"""

import os
import json
import logging
from fractions import Fraction
from typing import Optional, Dict, Any, Tuple, Union
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

try:
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_labeled_exif(exif):
    """
    Convert raw EXIF data to labeled data
    """
    labeled = {}
    for (key, val) in exif.items():
        labeled[TAGS.get(key, key)] = val
    return labeled

def get_geotagging(exif):
    """
    Extract GPS information from EXIF data
    """
    if not exif:
        return None

    geotagging = {}
    
    # Check if GPS info exists
    if 'GPSInfo' not in exif:
        return None
    
    for (key, val) in exif['GPSInfo'].items():
        geotagging[GPSTAGS.get(key, key)] = val
        
    return geotagging

def get_decimal_coordinates(geotagging):
    """
    Convert GPS coordinates from degrees/minutes/seconds to decimal format
    """
    if not geotagging:
        return None
    
    # Check if we have the required GPS tags
    required_tags = ['GPSLatitude', 'GPSLatitudeRef', 'GPSLongitude', 'GPSLongitudeRef']
    if not all(tag in geotagging for tag in required_tags):
        return None
        
    lat = _convert_to_decimal(geotagging['GPSLatitude'], geotagging['GPSLatitudeRef'])
    lon = _convert_to_decimal(geotagging['GPSLongitude'], geotagging['GPSLongitudeRef'])
    
    return (lat, lon)

def _convert_to_decimal(value, ref):
    """
    Helper function to convert GPS coordinates to decimal format
    """
    try:
        degrees = value[0]
        minutes = value[1]
        seconds = value[2]
        
        # Handle different data types (some cameras store as rationals, others as floats)
        if hasattr(degrees, 'numerator'):
            d = float(degrees.numerator) / float(degrees.denominator)
        else:
            d = float(degrees)
            
        if hasattr(minutes, 'numerator'):
            m = float(minutes.numerator) / float(minutes.denominator)
        else:
            m = float(minutes)
            
        if hasattr(seconds, 'numerator'):
            s = float(seconds.numerator) / float(seconds.denominator)
        else:
            s = float(seconds)
            
        result = d + (m / 60.0) + (s / 3600.0)
        
        # If south or west, negate the value
        if ref in ['S', 'W']:
            result = -result
            
        return result
    except (TypeError, ZeroDivisionError, AttributeError) as e:
        logger.error(f"Error converting coordinates: {e}")
        return None

def extract_gps_from_photo(image_or_path) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from a photo
    
    Args:
        image_or_path: PIL Image object or path to image file
        
    Returns:
        Tuple with (latitude, longitude) if GPS data was found, None otherwise
    """
    try:
        # Handle both file paths and PIL Image objects
        if isinstance(image_or_path, str):
            if not os.path.exists(image_or_path):
                logger.error(f"Image file not found: {image_or_path}")
                return None
                
            img = Image.open(image_or_path)
        else:
            img = image_or_path
            
        # Check if image has EXIF data
        if hasattr(img, '_getexif') and img._getexif():
            exif = get_labeled_exif(img._getexif())
            geotagging = get_geotagging(exif)
            return get_decimal_coordinates(geotagging)
            
        return None
    except Exception as e:
        logger.error(f"Error extracting GPS data: {e}")
        return None

def get_exif_data(image: Union[str, Image.Image]) -> Dict[str, Any]:
    """
    Extract EXIF data from an image.
    
    Args:
        image: Path to image file or PIL Image object
        
    Returns:
        Dictionary with EXIF data or empty dict if no data found
    """
    if not PILLOW_AVAILABLE:
        raise ImportError("Pillow is required for extracting EXIF data")
    
    # If image is a string (file path), open the image
    if isinstance(image, str):
        # Check file existence
        if not os.path.exists(image):
            logger.error(f"Image file not found: {image}")
            return {}
            
        # Check for unsupported formats
        if image.lower().endswith(('.heic', '.heif')):
            logger.warning(f"HEIC/HEIF format not supported natively. Consider converting to JPG: {image}")
            return {}
            
        try:
            image = Image.open(image)
        except Exception as e:
            logger.error(f"Error opening image {image}: {e}")
            return {}
    
    # Extract EXIF data
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
    except (AttributeError, ValueError, TypeError) as e:
        logger.warning(f"Error extracting EXIF data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error extracting EXIF data: {e}")
    
    return exif_data

def get_gps_info(exif_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract GPS information from EXIF data.
    
    Args:
        exif_data: Dictionary with EXIF data
        
    Returns:
        Dictionary with GPS tags or None if no GPS data found
    """
    gps_info = {}
    
    if not exif_data:
        return None
    
    # Check for GPS data
    gps_info_tag = 'GPSInfo'
    if gps_info_tag not in exif_data:
        return None
    
    # Extract GPS tags
    gps_data = exif_data[gps_info_tag]
    if not gps_data:
        return None
        
    for tag in gps_data:
        try:
            decoded = GPSTAGS.get(tag, tag)
            gps_info[decoded] = gps_data[tag]
        except Exception as e:
            logger.warning(f"Error decoding GPS tag {tag}: {e}")
    
    return gps_info

def _convert_to_degrees(value: tuple) -> float:
    """
    Convert GPS coordinates from EXIF format to decimal degrees.
    
    Args:
        value: GPS coordinate in EXIF format (degrees, minutes, seconds)
        
    Returns:
        Decimal degrees
    """
    try:
        # Handle different possible formats
        if isinstance(value, tuple) and len(value) == 3:
            # Traditional degrees, minutes, seconds format
            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])
            
            # Handle Fraction objects
            if isinstance(degrees, Fraction):
                degrees = float(degrees)
            if isinstance(minutes, Fraction):
                minutes = float(minutes)
            if isinstance(seconds, Fraction):
                seconds = float(seconds)
                
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
            
        elif isinstance(value, (int, float)):
            # Already in decimal format
            return float(value)
            
        else:
            # Try to parse other formats
            logger.warning(f"Unexpected GPS coordinate format: {value}")
            if isinstance(value, tuple) and len(value) > 0:
                return float(value[0])
            elif isinstance(value, (list, tuple)):
                return float(value[0])
            else:
                return float(value)
                
    except (ValueError, TypeError, IndexError) as e:
        logger.error(f"Error converting GPS coordinates: {e} (value: {value})")
        return 0.0

def get_lat_lon(gps_info: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """
    Extract latitude and longitude from GPS info.
    
    Args:
        gps_info: Dictionary with GPS tags
        
    Returns:
        Tuple of (latitude, longitude) or None if required data missing
    """
    if not gps_info:
        return None
    
    # Check for required GPS data
    required_tags = ['GPSLatitude', 'GPSLatitudeRef', 'GPSLongitude', 'GPSLongitudeRef']
    if not all(tag in gps_info for tag in required_tags):
        missing = [tag for tag in required_tags if tag not in gps_info]
        logger.warning(f"Missing GPS tags: {missing}")
        return None
    
    try:
        # Extract latitude
        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat
            
        # Extract longitude
        lon = _convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E':
            lon = -lon
            
        return lat, lon
        
    except Exception as e:
        logger.error(f"Error extracting latitude/longitude: {e}")
        return None

def get_coordinates_with_details(image: Union[str, Image.Image]) -> Dict[str, Any]:
    """
    Extract GPS coordinates and other details from a photo.
    
    Args:
        image: Path to image file or PIL Image object
        
    Returns:
        Dictionary with coordinates, EXIF data, and error message if applicable
    """
    result = {
        'success': False,
        'coordinates': None,
        'latitude': None,
        'longitude': None,
        'exif_data': {},
        'gps_data': {},
        'error': None
    }
    
    try:
        # Get EXIF data
        exif_data = get_exif_data(image)
        if exif_data:
            result['exif_data'] = {k: str(v) for k, v in exif_data.items() 
                                  if k != 'GPSInfo' and not isinstance(v, bytes)}
        
        # Get GPS info
        gps_info = get_gps_info(exif_data)
        if gps_info:
            result['gps_data'] = {k: str(v) for k, v in gps_info.items() 
                                 if not isinstance(v, bytes)}
        
        # Get coordinates
        coords = get_lat_lon(gps_info)
        if coords:
            lat, lon = coords
            result['coordinates'] = coords
            result['latitude'] = lat
            result['longitude'] = lon
            result['success'] = True
        else:
            result['error'] = "No GPS coordinates found in image"
    
    except Exception as e:
        result['error'] = f"Error processing image: {e}"
        logger.error(result['error'])
    
    return result

def main():
    """
    Command-line interface for testing the module.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Extract GPS data from photos')
    parser.add_argument('image', help='Path to image file')
    args = parser.parse_args()
    
    # Extract GPS data
    result = get_coordinates_with_details(args.image)
    
    # Print coordinates
    if result['success']:
        print(f"Coordinates: {result['latitude']}, {result['longitude']}")
    else:
        print(f"Error: {result['error']}")
        
    # Print detailed info
    print("\nDetailed information:")
    print(json.dumps(result, indent=2))
    
    return 0 if result['success'] else 1

if __name__ == "__main__":
    sys.exit(main()) 