#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geo-city",
    version="0.1.0",
    author="GeoCity Team",
    author_email="example@geocity.org",
    description="Find the nearest city to any geographic coordinates or from photo metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/geo-city",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/geo-city/issues",
        "Documentation": "https://geocity.readthedocs.io/",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pillow>=8.0.0",
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "appdirs>=1.4.4",
    ],
    extras_require={
        "web": [
            "streamlit>=1.0.0",
            "folium>=0.12.0",
            "streamlit-folium>=0.6.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "geocity=geo_city.nearest_city:main",
        ],
    },
) 