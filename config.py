"""
SafeRoute AI - Afet Yönetim Sistemi Konfigürasyonu
TUA Astro Hackathon 2026
"""

import os

# Uygulama ayarları
APP_NAME = "SafeRoute AI"
APP_VERSION = "1.0.0"
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000
SECRET_KEY = os.environ.get("SECRET_KEY", "saferoute-ai-2026-hackathon")

# Harita varsayılan merkez (Türkiye)
DEFAULT_LAT = 39.9334
DEFAULT_LON = 32.8597
DEFAULT_ZOOM = 6

# Grid çözünürlüğü (metre cinsinden)
GRID_RESOLUTION = 50  # 50m x 50m grid hücreleri

# Afet türleri ve risk ağırlıkları
DISASTER_TYPES = {
    "earthquake": {
        "name": "Deprem",
        "color": "#FF0000",
        "icon": "warning",
        "base_risk": 0.9,
        "secondary_risks": ["building_collapse", "fire", "tsunami", "landslide", "gas_leak"]
    },
    "fire": {
        "name": "Yangın",
        "color": "#FF6600",
        "icon": "fire",
        "base_risk": 0.85,
        "secondary_risks": ["smoke", "explosion", "structural_damage"]
    },
    "flood": {
        "name": "Sel/Su Baskını",
        "color": "#0066FF",
        "icon": "water",
        "base_risk": 0.8,
        "secondary_risks": ["landslide", "contamination", "structural_damage"]
    },
    "landslide": {
        "name": "Heyelan",
        "color": "#8B4513",
        "icon": "mountain",
        "base_risk": 0.85,
        "secondary_risks": ["road_block", "structural_damage"]
    },
    "tsunami": {
        "name": "Tsunami",
        "color": "#000080",
        "icon": "waves",
        "base_risk": 0.95,
        "secondary_risks": ["flood", "contamination", "structural_damage"]
    }
}

# Arazi türleri ve tehlike çarpanları
TERRAIN_TYPES = {
    "building": {
        "name": "Bina",
        "risk_multiplier": 1.5,
        "earthquake_risk": 0.9,
        "fire_risk": 0.7,
        "flood_risk": 0.3,
        "description": "Yıkılma riski - uzak durun"
    },
    "forest": {
        "name": "Orman",
        "risk_multiplier": 1.3,
        "earthquake_risk": 0.2,
        "fire_risk": 0.95,
        "flood_risk": 0.4,
        "description": "Yangın yayılma riski yüksek"
    },
    "water_body": {
        "name": "Su Kütlesi (Göl/Nehir/Deniz)",
        "risk_multiplier": 1.8,
        "earthquake_risk": 0.5,
        "fire_risk": 0.0,
        "flood_risk": 0.95,
        "description": "Sel ve tsunami riski - geçiş tehlikeli"
    },
    "wetland": {
        "name": "Sulak Alan",
        "risk_multiplier": 1.6,
        "earthquake_risk": 0.6,
        "fire_risk": 0.1,
        "flood_risk": 0.9,
        "description": "Zemin kayması ve sel riski"
    },
    "road": {
        "name": "Yol",
        "risk_multiplier": 0.3,
        "earthquake_risk": 0.4,
        "fire_risk": 0.2,
        "flood_risk": 0.5,
        "description": "Geçiş için uygun - çatlak kontrolü gerekli"
    },
    "open_field": {
        "name": "Açık Alan",
        "risk_multiplier": 0.1,
        "earthquake_risk": 0.1,
        "fire_risk": 0.3,
        "flood_risk": 0.2,
        "description": "Güvenli toplanma alanı"
    },
    "park": {
        "name": "Park/Bahçe",
        "risk_multiplier": 0.2,
        "earthquake_risk": 0.15,
        "fire_risk": 0.4,
        "flood_risk": 0.3,
        "description": "Nispeten güvenli - ağaç devrilme riski"
    },
    "industrial": {
        "name": "Endüstriyel Alan",
        "risk_multiplier": 2.0,
        "earthquake_risk": 0.85,
        "fire_risk": 0.9,
        "flood_risk": 0.7,
        "description": "Kimyasal sızıntı ve patlama riski!"
    },
    "gas_station": {
        "name": "Benzin İstasyonu",
        "risk_multiplier": 2.5,
        "earthquake_risk": 0.95,
        "fire_risk": 0.99,
        "flood_risk": 0.8,
        "description": "YÜKSEK TEHLİKE - Patlama riski!"
    },
    "hospital": {
        "name": "Hastane",
        "risk_multiplier": 0.5,
        "earthquake_risk": 0.3,
        "fire_risk": 0.3,
        "flood_risk": 0.3,
        "description": "Hedef nokta - kurtarma merkezi"
    },
    "bridge": {
        "name": "Köprü",
        "risk_multiplier": 1.7,
        "earthquake_risk": 0.9,
        "fire_risk": 0.2,
        "flood_risk": 0.85,
        "description": "Yapısal hasar riski - geçiş tehlikeli olabilir"
    },
    "slope": {
        "name": "Yamaç/Eğimli Alan",
        "risk_multiplier": 1.4,
        "earthquake_risk": 0.7,
        "fire_risk": 0.5,
        "flood_risk": 0.6,
        "description": "Heyelan ve toprak kayması riski"
    },
    "power_line": {
        "name": "Enerji Hattı",
        "risk_multiplier": 1.9,
        "earthquake_risk": 0.8,
        "fire_risk": 0.85,
        "flood_risk": 0.7,
        "description": "Elektrik çarpma riski - güvenli mesafe koruyun"
    },
    "rubble": {
        "name": "Enkaz",
        "risk_multiplier": 2.0,
        "earthquake_risk": 1.0,
        "fire_risk": 0.6,
        "flood_risk": 0.5,
        "description": "Geçiş zor - arama kurtarma bölgesi"
    }
}

# Risk seviyeleri
RISK_LEVELS = {
    "very_low": {"min": 0.0, "max": 0.2, "color": "#00FF00", "label": "Çok Düşük", "passable": True},
    "low": {"min": 0.2, "max": 0.4, "color": "#ADFF2F", "label": "Düşük", "passable": True},
    "medium": {"min": 0.4, "max": 0.6, "color": "#FFD700", "label": "Orta", "passable": True},
    "high": {"min": 0.6, "max": 0.8, "color": "#FF8C00", "label": "Yüksek", "passable": True},
    "very_high": {"min": 0.8, "max": 0.9, "color": "#FF4500", "label": "Çok Yüksek", "passable": True},
    "extreme": {"min": 0.9, "max": 1.0, "color": "#FF0000", "label": "Aşırı Tehlikeli", "passable": False}
}

# Rota hesaplama ayarları
ROUTING_CONFIG = {
    "max_risk_threshold": 0.85,
    "risk_weight": 3.0,
    "distance_weight": 1.0,
    "elevation_weight": 0.5,
    "road_preference": 0.7,
    "avoid_water": True,
    "avoid_buildings_after_earthquake": True,
    "safety_buffer_meters": 100,
    "max_route_alternatives": 3
}

# Uydu görüntü analizi ayarları
SATELLITE_CONFIG = {
    "supported_formats": [".tif", ".tiff", ".png", ".jpg", ".jpeg"],
    "min_resolution": 256,
    "max_resolution": 4096,
    "bands": ["R", "G", "B", "NIR"],
    "ndvi_threshold": 0.3,
    "water_ndwi_threshold": 0.0,
    "burn_nbr_threshold": -0.1
}
