"""
SafeRoute AI - Afet Tespit Motoru
Uydu görüntülerinden afet tespiti ve analizi
"""

import numpy as np
from PIL import Image
import cv2
import os
from config import DISASTER_TYPES, TERRAIN_TYPES, SATELLITE_CONFIG


class DisasterDetector:
    """Uydu görüntülerinden afet ve arazi analizi yapan ana sınıf"""

    def __init__(self):
        self.color_ranges = self._define_color_ranges()
        self.detection_history = []

    def _define_color_ranges(self):
        """HSV renk aralıkları ile arazi türlerini tanımla"""
        return {
            "water_body": {
                "lower": np.array([90, 50, 50]),
                "upper": np.array([130, 255, 255]),
                "name": "Su Kütlesi"
            },
            "forest": {
                "lower": np.array([35, 50, 50]),
                "upper": np.array([85, 255, 255]),
                "name": "Orman/Yeşil Alan"
            },
            "fire": {
                "lower": np.array([0, 150, 150]),
                "upper": np.array([20, 255, 255]),
                "name": "Yangın/Sıcak Bölge"
            },
            "road": {
                "lower": np.array([0, 0, 80]),
                "upper": np.array([180, 50, 180]),
                "name": "Yol/Asfalt"
            },
            "building": {
                "lower": np.array([0, 0, 150]),
                "upper": np.array([180, 80, 255]),
                "name": "Bina/Yapı"
            },
            "rubble": {
                "lower": np.array([10, 30, 60]),
                "upper": np.array([30, 150, 160]),
                "name": "Enkaz/Yıkıntı"
            },
            "wetland": {
                "lower": np.array([35, 20, 40]),
                "upper": np.array([90, 80, 120]),
                "name": "Sulak Alan"
            },
            "open_field": {
                "lower": np.array([20, 40, 100]),
                "upper": np.array([40, 180, 255]),
                "name": "Açık Alan"
            }
        }

    def analyze_satellite_image(self, image_path):
        """
        Uydu görüntüsünü analiz et ve arazi haritası çıkar

        Returns:
            dict: {
                "terrain_map": 2D numpy array (arazi türleri),
                "risk_map": 2D numpy array (risk değerleri 0-1),
                "detected_features": list of detected features,
                "disaster_zones": list of disaster zones,
                "statistics": analysis statistics
            }
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Görüntü yüklenemedi: {image_path}")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        height, width = img.shape[:2]

        terrain_map = np.full((height, width), "open_field", dtype=object)
        confidence_map = np.zeros((height, width))
        detected_features = []

        # Her arazi türü için maskeleme
        for terrain_type, color_range in self.color_ranges.items():
            mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])

            # Morfolojik işlemler ile gürültü azaltma
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Bölgeleri bul
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 100:  # Çok küçük bölgeleri atla
                    continue

                # Confidence hesapla (alan büyüklüğüne göre)
                confidence = min(area / (width * height) * 100, 1.0)

                # Arazi haritasını güncelle
                mask_bool = mask > 0
                better = confidence > confidence_map
                update = mask_bool & better
                terrain_map[update] = terrain_type
                confidence_map[update] = confidence

                # Bölge merkezi ve sınırlarını kaydet
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    x, y, w, h = cv2.boundingRect(contour)

                    detected_features.append({
                        "type": terrain_type,
                        "name": color_range["name"],
                        "center": (cx, cy),
                        "bounds": (x, y, w, h),
                        "area": area,
                        "area_percentage": (area / (width * height)) * 100,
                        "confidence": confidence
                    })

        # İstatistikleri hesapla
        statistics = self._calculate_statistics(terrain_map, width, height)

        return {
            "terrain_map": terrain_map,
            "confidence_map": confidence_map,
            "detected_features": detected_features,
            "image_size": (width, height),
            "statistics": statistics
        }

    def detect_disasters(self, image_path, disaster_type="earthquake"):
        """
        Uydu görüntüsünden afet bölgelerini tespit et

        Args:
            image_path: Görüntü dosya yolu
            disaster_type: Afet türü

        Returns:
            dict: Afet analiz sonuçları
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Görüntü yüklenemedi: {image_path}")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = img.shape[:2]

        disaster_zones = []
        warnings = []

        if disaster_type == "earthquake":
            disaster_zones, warnings = self._detect_earthquake_damage(img, hsv, gray, width, height)
        elif disaster_type == "fire":
            disaster_zones, warnings = self._detect_fire(img, hsv, gray, width, height)
        elif disaster_type == "flood":
            disaster_zones, warnings = self._detect_flood(img, hsv, gray, width, height)
        elif disaster_type == "landslide":
            disaster_zones, warnings = self._detect_landslide(img, hsv, gray, width, height)

        return {
            "disaster_type": disaster_type,
            "disaster_info": DISASTER_TYPES.get(disaster_type, {}),
            "zones": disaster_zones,
            "warnings": warnings,
            "severity": self._calculate_severity(disaster_zones),
            "affected_area_percent": sum(z.get("area_percent", 0) for z in disaster_zones)
        }

    def _detect_earthquake_damage(self, img, hsv, gray, width, height):
        """Deprem hasarı tespit et"""
        zones = []
        warnings = []
        total_area = width * height

        # Enkaz tespiti (düzensiz dokular, gri-kahve tonlar)
        rubble_lower = np.array([10, 30, 60])
        rubble_upper = np.array([30, 150, 160])
        rubble_mask = cv2.inRange(hsv, rubble_lower, rubble_upper)

        # Kenar tespiti ile yapısal hasar analizi
        edges = cv2.Canny(gray, 50, 150)
        edge_density = cv2.GaussianBlur(edges.astype(np.float32), (21, 21), 0)

        # Yüksek kenar yoğunluğu = olası yapısal hasar
        damage_threshold = np.percentile(edge_density, 85)
        damage_mask = (edge_density > damage_threshold).astype(np.uint8) * 255

        # Kombine hasar maskesi
        combined = cv2.bitwise_or(rubble_mask, damage_mask)
        kernel = np.ones((15, 15), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 200:
                continue

            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)
                area_percent = (area / total_area) * 100

                severity = "high" if area_percent > 5 else "medium" if area_percent > 1 else "low"

                zones.append({
                    "type": "structural_damage",
                    "name": "Yapısal Hasar Bölgesi",
                    "center": (cx, cy),
                    "bounds": (x, y, w, h),
                    "area": area,
                    "area_percent": area_percent,
                    "severity": severity,
                    "risk_level": 0.9 if severity == "high" else 0.7 if severity == "medium" else 0.5
                })

        # Bina yakınlarında çökme uyarısı
        building_mask = cv2.inRange(hsv, np.array([0, 0, 150]), np.array([180, 80, 255]))
        building_contours, _ = cv2.findContours(building_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in building_contours:
            area = cv2.contourArea(contour)
            if area < 300:
                continue
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                warnings.append({
                    "type": "building_collapse_risk",
                    "message": f"⚠️ Bina tespit edildi ({cx},{cy}) - Deprem sonrası çökme riski! Güvenli mesafe koruyun.",
                    "location": (cx, cy),
                    "risk": 0.85
                })

        # Su kütlesi yakınında tsunami/sel uyarısı
        water_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        water_area = np.sum(water_mask > 0)
        if water_area > total_area * 0.05:
            warnings.append({
                "type": "secondary_flood_risk",
                "message": "🌊 Yakında su kütlesi tespit edildi - Deprem sonrası sel/tsunami riski!",
                "risk": 0.75
            })

        # Orman yakınında yangın uyarısı
        forest_mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
        forest_area = np.sum(forest_mask > 0)
        if forest_area > total_area * 0.1:
            warnings.append({
                "type": "secondary_fire_risk",
                "message": "🔥 Yakında orman alanı tespit edildi - Deprem sonrası yangın riski! Gaz hatları kontrol edilmeli.",
                "risk": 0.6
            })

        return zones, warnings

    def _detect_fire(self, img, hsv, gray, width, height):
        """Yangın tespiti"""
        zones = []
        warnings = []
        total_area = width * height

        # Aktif yangın (kırmızı-turuncu tonlar)
        fire_lower1 = np.array([0, 150, 150])
        fire_upper1 = np.array([20, 255, 255])
        fire_lower2 = np.array([160, 150, 150])
        fire_upper2 = np.array([180, 255, 255])

        fire_mask1 = cv2.inRange(hsv, fire_lower1, fire_upper1)
        fire_mask2 = cv2.inRange(hsv, fire_lower2, fire_upper2)
        fire_mask = cv2.bitwise_or(fire_mask1, fire_mask2)

        # Duman tespiti (gri tonlar, düşük doygunluk)
        smoke_lower = np.array([0, 0, 100])
        smoke_upper = np.array([180, 60, 200])
        smoke_mask = cv2.inRange(hsv, smoke_lower, smoke_upper)

        kernel = np.ones((10, 10), np.uint8)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:
                continue

            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)
                area_percent = (area / total_area) * 100

                zones.append({
                    "type": "active_fire",
                    "name": "Aktif Yangın Bölgesi",
                    "center": (cx, cy),
                    "bounds": (x, y, w, h),
                    "area": area,
                    "area_percent": area_percent,
                    "severity": "extreme",
                    "risk_level": 0.98,
                    "spread_direction": self._estimate_fire_spread(fire_mask, cx, cy)
                })

        # Yanmış alan tespiti
        burn_lower = np.array([0, 30, 20])
        burn_upper = np.array([30, 120, 80])
        burn_mask = cv2.inRange(hsv, burn_lower, burn_upper)
        burn_contours, _ = cv2.findContours(burn_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in burn_contours:
            area = cv2.contourArea(contour)
            if area < 200:
                continue
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)
                zones.append({
                    "type": "burned_area",
                    "name": "Yanmış Alan",
                    "center": (cx, cy),
                    "bounds": (x, y, w, h),
                    "area": area,
                    "area_percent": (area / total_area) * 100,
                    "severity": "medium",
                    "risk_level": 0.6
                })

        # Orman yakınında yayılma uyarısı
        forest_mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
        if np.sum(forest_mask > 0) > total_area * 0.05:
            warnings.append({
                "type": "fire_spread_risk",
                "message": "🌲🔥 Orman alanı tespit edildi - Yangın yayılma riski ÇOK YÜKSEK!",
                "risk": 0.9
            })

        return zones, warnings

    def _detect_flood(self, img, hsv, gray, width, height):
        """Sel tespiti"""
        zones = []
        warnings = []
        total_area = width * height

        # Su baskını alanları (geniş mavi-koyu alanlar)
        water_lower = np.array([85, 30, 30])
        water_upper = np.array([135, 255, 255])
        water_mask = cv2.inRange(hsv, water_lower, water_upper)

        # Bulanık su (kahverengi-mavi karışımı)
        muddy_lower = np.array([10, 50, 40])
        muddy_upper = np.array([30, 200, 180])
        muddy_mask = cv2.inRange(hsv, muddy_lower, muddy_upper)

        flood_mask = cv2.bitwise_or(water_mask, muddy_mask)
        kernel = np.ones((15, 15), np.uint8)
        flood_mask = cv2.morphologyEx(flood_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(flood_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:
                continue

            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)
                area_percent = (area / total_area) * 100

                zones.append({
                    "type": "flooded_area",
                    "name": "Su Baskını Bölgesi",
                    "center": (cx, cy),
                    "bounds": (x, y, w, h),
                    "area": area,
                    "area_percent": area_percent,
                    "severity": "high" if area_percent > 10 else "medium",
                    "risk_level": 0.9 if area_percent > 10 else 0.7
                })

        # Alçak alan uyarısı
        warnings.append({
            "type": "low_area_risk",
            "message": "⚠️ Alçak bölgelerde su birikmesi riski - Yüksek rotaları tercih edin!",
            "risk": 0.7
        })

        return zones, warnings

    def _detect_landslide(self, img, hsv, gray, width, height):
        """Heyelan tespiti"""
        zones = []
        warnings = []
        total_area = width * height

        # Toprak kayması (kahverengi düzensiz alanlar)
        soil_lower = np.array([5, 50, 50])
        soil_upper = np.array([25, 200, 200])
        soil_mask = cv2.inRange(hsv, soil_lower, soil_upper)

        # Kenar analizi ile düzensiz toprak hareketleri
        edges = cv2.Canny(gray, 30, 100)
        combined = cv2.bitwise_and(soil_mask, edges)
        kernel = np.ones((20, 20), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 300:
                continue

            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)

                zones.append({
                    "type": "landslide_area",
                    "name": "Heyelan Bölgesi",
                    "center": (cx, cy),
                    "bounds": (x, y, w, h),
                    "area": area,
                    "area_percent": (area / total_area) * 100,
                    "severity": "high",
                    "risk_level": 0.85
                })

        warnings.append({
            "type": "slope_risk",
            "message": "⛰️ Eğimli arazilerde ek heyelan riski - Düz rotaları tercih edin!",
            "risk": 0.7
        })

        return zones, warnings

    def _estimate_fire_spread(self, fire_mask, cx, cy):
        """Yangın yayılma yönünü tahmin et"""
        h, w = fire_mask.shape
        directions = {}

        # 4 yöne bak
        margin = 50
        directions["north"] = np.sum(fire_mask[max(0, cy - margin):cy, max(0, cx - margin):min(w, cx + margin)])
        directions["south"] = np.sum(fire_mask[cy:min(h, cy + margin), max(0, cx - margin):min(w, cx + margin)])
        directions["east"] = np.sum(fire_mask[max(0, cy - margin):min(h, cy + margin), cx:min(w, cx + margin)])
        directions["west"] = np.sum(fire_mask[max(0, cy - margin):min(h, cy + margin), max(0, cx - margin):cx])

        if not any(directions.values()):
            return "belirsiz"

        # En az yangın olan yön = yayılma yönü (yangın oraya doğru ilerliyor)
        spread_dir = min(directions, key=directions.get)
        dir_names = {"north": "Kuzey", "south": "Güney", "east": "Doğu", "west": "Batı"}
        return dir_names.get(spread_dir, "belirsiz")

    def _calculate_severity(self, zones):
        """Genel afet şiddetini hesapla"""
        if not zones:
            return {"level": "low", "score": 0.1, "label": "Düşük"}

        avg_risk = np.mean([z.get("risk_level", 0.5) for z in zones])
        total_area = sum(z.get("area_percent", 0) for z in zones)

        score = min(avg_risk * 0.6 + (total_area / 100) * 0.4, 1.0)

        if score > 0.8:
            return {"level": "extreme", "score": score, "label": "Aşırı Tehlikeli"}
        elif score > 0.6:
            return {"level": "high", "score": score, "label": "Yüksek"}
        elif score > 0.4:
            return {"level": "medium", "score": score, "label": "Orta"}
        else:
            return {"level": "low", "score": score, "label": "Düşük"}

    def _calculate_statistics(self, terrain_map, width, height):
        """Arazi istatistiklerini hesapla"""
        total = width * height
        stats = {}
        unique_terrains = np.unique(terrain_map)

        for terrain in unique_terrains:
            count = np.sum(terrain_map == terrain)
            terrain_info = TERRAIN_TYPES.get(terrain, {})
            stats[terrain] = {
                "name": terrain_info.get("name", terrain),
                "pixel_count": int(count),
                "percentage": round((count / total) * 100, 2),
                "risk_multiplier": terrain_info.get("risk_multiplier", 1.0)
            }

        return stats
