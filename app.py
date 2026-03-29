"""
SafeRoute AI - Ana Uygulama
Afet Yonetiminde Yerli Uydu Verisi Entegrasyonu
TUA Astro Hackathon 2026
"""

import os
import json
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from config import *
from disaster_detector import DisasterDetector
from risk_analyzer import RiskAnalyzer
from route_planner import RoutePlanner
from scenario_generator import ScenarioGenerator
from satellite_data import SatelliteDataManager
from emergency_services import EmergencyServices

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Moduller
detector = DisasterDetector()
analyzer = RiskAnalyzer()
planner = RoutePlanner()
generator = ScenarioGenerator()
satellite = SatelliteDataManager()
emergency = EmergencyServices()

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """Uydu goruntusunu analiz et"""
    if 'image' not in request.files:
        return jsonify({"error": "Goruntu dosyasi gerekli"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Dosya secilmedi"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    disaster_type = request.form.get('disaster_type', 'earthquake')

    try:
        terrain_result = detector.analyze_satellite_image(filepath)
        disaster_result = detector.detect_disasters(filepath, disaster_type)
        risk_result = analyzer.generate_risk_map(
            terrain_result["terrain_map"], disaster_result
        )

        response = {
            "success": True,
            "terrain_analysis": {
                "statistics": terrain_result["statistics"],
                "feature_count": len(terrain_result["detected_features"]),
                "features": [
                    {
                        "type": f["type"], "name": f["name"],
                        "center": list(f["center"]),
                        "area_percentage": round(f["area_percentage"], 2)
                    }
                    for f in terrain_result["detected_features"][:20]
                ]
            },
            "disaster_analysis": {
                "type": disaster_result["disaster_type"],
                "info": disaster_result["disaster_info"],
                "severity": disaster_result["severity"],
                "affected_area": round(disaster_result["affected_area_percent"], 2),
                "zone_count": len(disaster_result["zones"]),
                "warning_count": len(disaster_result["warnings"]),
                "warnings": [
                    {"message": w["message"], "risk": w.get("risk", 0)}
                    for w in disaster_result["warnings"]
                ]
            },
            "risk_analysis": {
                "statistics": risk_result["statistics"],
                "hazards": risk_result["hazard_analysis"][:15],
                "layer_weights": risk_result["layer_weights"]
            },
            "image_path": filepath
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/demo', methods=['POST'])
def generate_demo():
    """Demo senaryo olustur"""
    data = request.get_json() or {}
    disaster_type = data.get('disaster_type', 'earthquake')
    severity = data.get('severity', 'high')
    scenario = data.get('scenario', 'kahramanmaras_earthquake')

    try:
        # Senaryo olustur
        image_path, scenario_info = generator.generate_city_scenario(
            disaster_type=disaster_type, severity=severity
        )

        # Analiz
        terrain_result = detector.analyze_satellite_image(image_path)
        disaster_result = detector.detect_disasters(image_path, disaster_type)
        risk_result = analyzer.generate_risk_map(
            terrain_result["terrain_map"], disaster_result
        )

        # Rota hesapla
        start = (50, 50)
        end = (265, 385)
        route_result = planner.find_safest_route(
            risk_result["combined_risk"], terrain_result["terrain_map"],
            start, end, num_alternatives=3
        )

        # Risk haritasi goruntusunu kaydet
        risk_image_path = _save_risk_map_image(
            risk_result["combined_risk"],
            route_result.get("primary_route", {}).get("path", []),
            [alt.get("path", []) for alt in route_result.get("alternatives", [])]
        )

        # Sentinel-2 analizi
        sentinel_data = satellite.simulate_sentinel2_data(scenario, 500, 400)
        spectral_result = None
        if sentinel_data:
            change_result = satellite.change_detection(
                sentinel_data["pre_disaster"],
                sentinel_data["post_disaster"],
                disaster_type
            )
            spectral_result = _format_spectral_results(
                sentinel_data, change_result, disaster_type
            )

        response = {
            "success": True,
            "scenario": {
                "disaster_type": disaster_type,
                "severity": severity,
                "image_path": image_path
            },
            "terrain_analysis": {
                "statistics": terrain_result["statistics"],
                "feature_count": len(terrain_result["detected_features"])
            },
            "disaster_analysis": {
                "type": disaster_result["disaster_type"],
                "severity": disaster_result["severity"],
                "affected_area": round(disaster_result["affected_area_percent"], 2),
                "warnings": [
                    {"message": w["message"], "risk": w.get("risk", 0)}
                    for w in disaster_result["warnings"]
                ]
            },
            "risk_analysis": {
                "statistics": risk_result["statistics"],
                "hazards": risk_result["hazard_analysis"][:15]
            },
            "spectral_analysis": spectral_result,
            "route": {"success": route_result.get("success", False),
                      "primary": None, "alternatives": [], "summary": route_result.get("summary", {})},
            "risk_image_path": risk_image_path
        }

        if route_result.get("success"):
            primary = route_result["primary_route"]
            simplified_path = primary["path"][::5] + [primary["path"][-1]]
            response["route"]["primary"] = {
                "path": [list(p) for p in simplified_path],
                "analysis": primary["analysis"],
                "warnings": primary["warnings"][:10],
                "navigation": primary["navigation"]
            }
            response["route"]["alternatives"] = [
                {
                    "path": [list(p) for p in alt["path"][::5] + [alt["path"][-1]]],
                    "analysis": alt["analysis"]
                }
                for alt in route_result["alternatives"]
            ]

        return jsonify(response)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/spectral-info')
def spectral_info():
    """Spektral bant ve indeks bilgileri"""
    return jsonify({
        "bands": satellite.SENTINEL2_BANDS,
        "indices": satellite.SPECTRAL_INDICES,
        "data_sources": satellite.get_data_sources_info()
    })


@app.route('/api/scenarios')
def list_scenarios():
    scenarios = []
    for dtype in DISASTER_TYPES:
        for severity in ["low", "medium", "high"]:
            scenarios.append({
                "disaster_type": dtype,
                "name": DISASTER_TYPES[dtype]["name"],
                "severity": severity,
                "severity_label": {"low": "Dusuk", "medium": "Orta", "high": "Yuksek"}[severity]
            })
    return jsonify({"scenarios": scenarios})


@app.route('/api/emergency-data', methods=['POST'])
def get_emergency_data():
    """Acil durum verileri: hastane, toplanma, AFAD, deprem, hava durumu"""
    data = request.get_json() or {}
    lat = data.get('lat', 37.5858)
    lon = data.get('lon', 36.9371)
    scenario = data.get('scenario', 'kahramanmaras')

    try:
        result = {
            "hospitals": emergency.get_nearest_hospitals(lat, lon, scenario),
            "assembly_points": emergency.get_assembly_points(lat, lon, scenario),
            "afad_units": emergency.get_afad_units(scenario),
            "recent_earthquakes": emergency.get_recent_earthquakes(lat, lon),
            "aftershock_zones": emergency.get_aftershock_risk_zones(lat, lon, 7.8),
            "population": emergency.get_population_density(lat, lon, scenario),
            "weather": emergency.get_weather_conditions(lat, lon, scenario),
            "building_assessment": emergency.get_building_risk_assessment(scenario),
            "rescue_resources": emergency.get_rescue_resources(scenario)
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)


def _format_spectral_results(sentinel_data, change_result, disaster_type):
    """Spektral analiz sonuclarini formatla"""
    metadata = sentinel_data.get("metadata", {})
    result = {
        "metadata": {
            "event": metadata.get("event", ""),
            "date": metadata.get("date", ""),
            "satellite": metadata.get("satellite", ""),
            "resolution": metadata.get("resolution", ""),
            "pre_date": metadata.get("pre_date", ""),
            "post_date": metadata.get("post_date", ""),
            "magnitude": metadata.get("magnitude", "")
        },
        "indices": {}
    }

    if disaster_type == "earthquake":
        if "ndvi_change" in change_result:
            ndvi_change = change_result["ndvi_change"]
            collapsed = change_result.get("collapsed_areas", np.zeros_like(ndvi_change, dtype=bool))
            result["indices"]["NDVI_Degisim"] = {
                "description": "Bitki indeksi degisimi (dusus = hasar)",
                "mean_change": float(np.mean(ndvi_change)),
                "max_change": float(np.max(ndvi_change)),
                "damaged_area_percent": float(np.sum(collapsed) / collapsed.size * 100)
            }
        if "ndbi_change" in change_result:
            result["indices"]["NDBI_Degisim"] = {
                "description": "Bina indeksi degisimi (artis = cokme)",
                "mean_change": float(np.mean(change_result["ndbi_change"])),
                "building_damage_percent": float(
                    np.sum(change_result.get("building_damage", False)) /
                    change_result["ndbi_change"].size * 100
                )
            }
        if "damage_intensity" in sentinel_data.get("ground_truth", {}):
            damage = sentinel_data["ground_truth"]["damage_intensity"]
            result["indices"]["Hasar_Yogunlugu"] = {
                "description": "Tahmini hasar yogunlugu",
                "mean": float(np.mean(damage[damage > 0])) if np.any(damage > 0) else 0,
                "severe_area_percent": float(np.sum(damage > 0.5) / damage.size * 100),
                "total_damaged_percent": float(np.sum(damage > 0.1) / damage.size * 100)
            }

    elif disaster_type == "fire":
        if "dnbr" in change_result:
            dnbr = change_result["dnbr"]
            result["indices"]["dNBR"] = {
                "description": "Yangin siddeti indeksi",
                "mean": float(np.mean(dnbr)),
                "high_severity_percent": float(np.sum(dnbr > 0.66) / dnbr.size * 100),
                "moderate_percent": float(np.sum((dnbr > 0.27) & (dnbr <= 0.66)) / dnbr.size * 100),
                "total_burned_percent": float(np.sum(dnbr > 0.1) / dnbr.size * 100)
            }

    elif disaster_type == "flood":
        if "ndwi_change" in change_result:
            ndwi_change = change_result["ndwi_change"]
            flooded = change_result.get("flooded_areas", np.zeros_like(ndwi_change, dtype=bool))
            result["indices"]["NDWI_Degisim"] = {
                "description": "Su indeksi degisimi (artis = su baskin)",
                "mean_change": float(np.mean(ndwi_change)),
                "flooded_area_percent": float(np.sum(flooded) / flooded.size * 100)
            }

    return result


def _save_risk_map_image(risk_map, primary_path, alt_paths):
    """Risk haritasini renkli goruntu olarak kaydet"""
    from PIL import Image

    height, width = risk_map.shape
    img = Image.new('RGBA', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            risk = risk_map[y, x]
            if risk < 0.2:
                color = (0, 200, 0, 150)
            elif risk < 0.4:
                color = (173, 255, 47, 150)
            elif risk < 0.6:
                color = (255, 215, 0, 150)
            elif risk < 0.8:
                color = (255, 140, 0, 180)
            elif risk < 0.9:
                color = (255, 69, 0, 200)
            else:
                color = (255, 0, 0, 220)
            pixels[x, y] = color

    for point in primary_path:
        r, c = point
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    pixels[nc, nr] = (0, 100, 255, 255)

    alt_colors = [(255, 255, 0, 200), (0, 255, 255, 200)]
    for i, alt_path in enumerate(alt_paths):
        color = alt_colors[i % len(alt_colors)]
        for point in alt_path:
            r, c = point
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        pixels[nc, nr] = color

    path = "data/risk_map.png"
    img.save(path)
    return path


if __name__ == '__main__':
    print("""
=============================================================
    SafeRoute AI v1.0.0
    Afet Yonetiminde Akilli Rota Planlama Sistemi
    TUA Astro Hackathon 2026
=============================================================
    Sunucu: http://localhost:5000
=============================================================
    """)
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
