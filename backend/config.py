#!/usr/bin/env python3
"""
Configuration file for API endpoints and environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
STATIONS_API_BASE_URL_NOKTTV = "https://openapi.vrain.vn/v1/stations"
STATS_API_BASE_URL_NOKTTV = "https://openapi.vrain.vn/v1/stations/stats"
API_KEY = "25ab243d80604b50a42afc1e270fcc51"
STATS_API_BASE_URL_KTTV = "https://kttv-open.vrain.vn/v1/stations/stats"
STATIONS_API_BASE_URL_KTTV = "https://kttv-open.vrain.vn/v1/stations"

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hydro_db")

# Backend Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000")) 