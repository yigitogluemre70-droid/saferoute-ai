"""
SafeRoute AI - Senaryo Üreteci
Demo ve test için gerçekçi afet senaryoları oluşturur
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class ScenarioGenerator:
    """Gerçekçi afet senaryoları ve simülasyon verileri üretir"""

    # Renk paletleri
    COLORS = {
        "road": (128, 128, 128),
        "building": (200, 200, 200),
        "forest": (34, 139, 34),
        "water_body": (30, 100, 200),
        "open_field": (180, 220, 120),
        "park": (60, 180, 75),
        "wetland": (70, 130, 100),
        "industrial": (160, 140, 130),
        "gas_station": (255, 200, 50),
        "hospital": (255, 255, 255),
        "bridge": (150, 150, 160),
        "rubble": (120, 90, 60),
        "fire": (255, 80, 20),
        "smoke": (180, 180, 190),
        "flood_water": (60, 120, 180),
        "slope": (160, 140, 100)
    }

    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height

    def generate_city_scenario(self, disaster_type="earthquake", severity="high"):
        """
        Şehir ortamında afet senaryosu oluştur

        Returns:
            tuple: (image_path, scenario_info)
        """
        img = Image.new('RGB', (self.width, self.height), self.COLORS["open_field"])
        draw = ImageDraw.Draw(img)
        terrain_map = np.full((self.height, self.width), "open_field", dtype=object)

        # Şehir altyapısı oluştur
        self._draw_roads(draw, terrain_map)
        self._draw_buildings(draw, terrain_map)
        self._draw_parks(draw, terrain_map)
        self._draw_water_features(draw, terrain_map)
        self._draw_infrastructure(draw, terrain_map)
        self._draw_forest(draw, terrain_map)

        # Afet etkilerini ekle
        disaster_info = {}
        if disaster_type == "earthquake":
            disaster_info = self._apply_earthquake(draw, terrain_map, severity)
        elif disaster_type == "fire":
            disaster_info = self._apply_fire(draw, terrain_map, severity)
        elif disaster_type == "flood":
            disaster_info = self._apply_flood(draw, terrain_map, severity)
        elif disaster_type == "landslide":
            disaster_info = self._apply_landslide(draw, terrain_map, severity)

        # Kaydet
        os.makedirs("data", exist_ok=True)
        image_path = f"data/scenario_{disaster_type}_{severity}.png"
        img.save(image_path)

        scenario_info = {
            "disaster_type": disaster_type,
            "severity": severity,
            "image_path": image_path,
            "image_size": (self.width, self.height),
            "terrain_map": terrain_map,
            "disaster_details": disaster_info,
            "safe_zones": self._find_safe_zones(terrain_map),
            "danger_zones": self._find_danger_zones(terrain_map)
        }

        return image_path, scenario_info

    def _draw_roads(self, draw, terrain_map):
        """Yol ağı çiz"""
        road_color = self.COLORS["road"]

        # Ana yollar (yatay)
        main_roads_h = [150, 300, 450]
        for y in main_roads_h:
            draw.rectangle([0, y - 6, self.width, y + 6], fill=road_color)
            terrain_map[y - 6:y + 7, :] = "road"

        # Ana yollar (dikey)
        main_roads_v = [200, 400, 600]
        for x in main_roads_v:
            draw.rectangle([x - 6, 0, x + 6, self.height], fill=road_color)
            terrain_map[:, x - 6:x + 7] = "road"

        # Ara yollar
        for y in [75, 225, 375, 525]:
            draw.rectangle([0, y - 3, self.width, y + 3], fill=road_color)
            terrain_map[y - 3:y + 4, :] = "road"

        for x in [100, 300, 500, 700]:
            draw.rectangle([x - 3, 0, x + 3, self.height], fill=road_color)
            terrain_map[:, x - 3:x + 4] = "road"

    def _draw_buildings(self, draw, terrain_map):
        """Binalar çiz"""
        building_color = self.COLORS["building"]
        np.random.seed(42)

        building_positions = [
            (30, 30, 90, 70), (110, 30, 170, 70),
            (30, 80, 80, 140), (110, 80, 180, 130),
            (210, 30, 280, 80), (310, 30, 380, 90),
            (210, 160, 280, 220), (310, 160, 390, 220),
            (420, 30, 490, 90), (510, 30, 580, 80),
            (420, 160, 500, 230), (510, 160, 590, 210),
            (620, 30, 690, 90), (620, 160, 700, 220),
            (30, 310, 90, 370), (110, 310, 180, 380),
            (210, 310, 290, 390), (310, 310, 380, 370),
            (420, 310, 490, 380), (510, 310, 590, 370),
            (620, 310, 700, 380),
            (30, 460, 90, 530), (110, 460, 190, 520),
            (210, 460, 280, 540), (310, 460, 380, 520),
            (420, 460, 500, 530), (510, 460, 590, 520),
            (620, 460, 700, 540),
            (710, 30, 780, 90), (710, 160, 790, 230),
            (710, 310, 780, 380), (710, 460, 790, 540)
        ]

        for x1, y1, x2, y2 in building_positions:
            # Yol üzerinde olmadığından emin ol
            draw.rectangle([x1, y1, x2, y2], fill=building_color, outline=(150, 150, 150))
            terrain_map[y1:y2 + 1, x1:x2 + 1] = "building"

    def _draw_parks(self, draw, terrain_map):
        """Parklar ve yeşil alanlar"""
        park_color = self.COLORS["park"]

        parks = [
            (240, 100, 350, 150),
            (450, 240, 560, 290),
            (50, 400, 150, 440),
            (650, 400, 780, 450)
        ]

        for x1, y1, x2, y2 in parks:
            draw.rectangle([x1, y1, x2, y2], fill=park_color)
            terrain_map[y1:y2 + 1, x1:x2 + 1] = "park"
            # Park içine ağaçlar
            for tx in range(x1 + 10, x2 - 10, 20):
                for ty in range(y1 + 10, y2 - 10, 20):
                    draw.ellipse([tx - 5, ty - 5, tx + 5, ty + 5], fill=(40, 160, 60))

    def _draw_water_features(self, draw, terrain_map):
        """Su kütleleri (nehir, göl)"""
        water_color = self.COLORS["water_body"]

        # Nehir (çapraz akan)
        for y in range(0, self.height):
            x_center = int(680 + 30 * np.sin(y / 60))
            draw.rectangle([x_center - 15, y, x_center + 15, y + 1], fill=water_color)
            terrain_map[y, max(0, x_center - 15):min(self.width, x_center + 16)] = "water_body"

        # Küçük göl
        draw.ellipse([550, 100, 640, 150], fill=water_color)
        for y in range(100, 151):
            for x in range(550, 641):
                cx, cy = 595, 125
                if ((x - cx) / 45) ** 2 + ((y - cy) / 25) ** 2 <= 1:
                    terrain_map[y, x] = "water_body"

        # Sulak alan
        wetland_color = self.COLORS["wetland"]
        draw.rectangle([540, 150, 650, 180], fill=wetland_color)
        terrain_map[150:181, 540:651] = "wetland"

    def _draw_infrastructure(self, draw, terrain_map):
        """Altyapı (hastane, benzin istasyonu, endüstriyel alan)"""
        # Hastane
        hospital_pos = (350, 240, 420, 290)
        draw.rectangle(hospital_pos, fill=self.COLORS["hospital"], outline=(255, 0, 0), width=3)
        # Kırmızı haç
        cx, cy = 385, 265
        draw.rectangle([cx - 15, cy - 5, cx + 15, cy + 5], fill=(255, 0, 0))
        draw.rectangle([cx - 5, cy - 15, cx + 5, cy + 15], fill=(255, 0, 0))
        terrain_map[240:291, 350:421] = "hospital"

        # Benzin istasyonu
        gas_positions = [(150, 160, 190, 190), (500, 400, 540, 430)]
        for x1, y1, x2, y2 in gas_positions:
            draw.rectangle([x1, y1, x2, y2], fill=self.COLORS["gas_station"], outline=(200, 100, 0))
            terrain_map[y1:y2 + 1, x1:x2 + 1] = "gas_station"

        # Endüstriyel alan
        ind_pos = (30, 540, 180, 590)
        draw.rectangle(ind_pos, fill=self.COLORS["industrial"], outline=(100, 80, 60))
        terrain_map[540:591, 30:181] = "industrial"

        # Köprü (nehir üzerinde)
        bridge_y = 300
        x_center = int(680 + 30 * np.sin(bridge_y / 60))
        draw.rectangle([x_center - 25, bridge_y - 8, x_center + 25, bridge_y + 8],
                       fill=self.COLORS["bridge"], outline=(100, 100, 110))
        terrain_map[bridge_y - 8:bridge_y + 9, x_center - 25:x_center + 26] = "bridge"

        # Enerji hattı
        for x in range(0, self.width, 80):
            draw.line([(x, 0), (x + 40, self.height)], fill=(80, 80, 80), width=1)

    def _draw_forest(self, draw, terrain_map):
        """Orman alanları"""
        forest_color = self.COLORS["forest"]

        # Büyük orman (sağ üst)
        forest_area = (720, 0, self.width, 120)
        draw.rectangle(forest_area, fill=forest_color)
        terrain_map[0:121, 720:self.width] = "forest"

        # Küçük orman parçaları
        small_forests = [
            (0, 0, 25, 60),
            (730, 550, self.width, self.height)
        ]
        for x1, y1, x2, y2 in small_forests:
            draw.rectangle([x1, y1, x2, y2], fill=forest_color)
            terrain_map[y1:min(y2 + 1, self.height), x1:min(x2 + 1, self.width)] = "forest"

    def _apply_earthquake(self, draw, terrain_map, severity):
        """Deprem etkilerini uygula"""
        np.random.seed(123)
        info = {"collapsed_buildings": [], "damaged_roads": [], "rubble_zones": []}

        # Deprem merkezi
        epicenter = (350, 280)
        radius = 200 if severity == "high" else 120

        # Binaları yık
        collapse_prob = 0.6 if severity == "high" else 0.3
        building_mask = terrain_map == "building"
        building_coords = np.argwhere(building_mask)

        rubble_color = self.COLORS["rubble"]

        for coord in building_coords:
            y, x = coord
            dist = np.sqrt((x - epicenter[0]) ** 2 + (y - epicenter[1]) ** 2)
            prob = collapse_prob * max(0, 1 - dist / radius)

            if np.random.random() < prob:
                # Binayı enkaza çevir
                draw.point((x, y), fill=rubble_color)
                terrain_map[y, x] = "rubble"

        # Yol hasarı
        road_mask = terrain_map == "road"
        road_coords = np.argwhere(road_mask)

        for coord in road_coords[::5]:
            y, x = coord
            dist = np.sqrt((x - epicenter[0]) ** 2 + (y - epicenter[1]) ** 2)
            if dist < radius and np.random.random() < 0.15:
                crack_len = np.random.randint(3, 10)
                for i in range(crack_len):
                    nx, ny = x + np.random.randint(-2, 3), y + np.random.randint(-2, 3)
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        draw.point((nx, ny), fill=(80, 60, 40))

        info["epicenter"] = epicenter
        info["radius"] = radius

        return info

    def _apply_fire(self, draw, terrain_map, severity):
        """Yangın etkilerini uygula"""
        info = {"fire_centers": [], "burn_area": 0}

        fire_color = self.COLORS["fire"]
        smoke_color = self.COLORS["smoke"]

        # Yangın merkezleri
        if severity == "high":
            fire_centers = [(730, 50), (750, 80), (100, 560)]
        else:
            fire_centers = [(740, 60)]

        for cx, cy in fire_centers:
            radius = 50 if severity == "high" else 30

            # Aktif yangın
            for y in range(max(0, cy - radius), min(self.height, cy + radius)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius)):
                    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    if dist < radius * 0.6:
                        intensity = int(255 * (1 - dist / (radius * 0.6)))
                        draw.point((x, y), fill=(255, max(0, 100 - intensity), 0))
                        terrain_map[y, x] = "rubble"  # Yanmış alan
                    elif dist < radius:
                        # Duman
                        draw.point((x, y), fill=smoke_color)

            info["fire_centers"].append((cx, cy))

        return info

    def _apply_flood(self, draw, terrain_map, severity):
        """Sel etkilerini uygula"""
        info = {"flooded_areas": [], "water_level": "high" if severity == "high" else "medium"}

        flood_color = self.COLORS["flood_water"]

        # Nehir taşması
        for y in range(0, self.height):
            x_center = int(680 + 30 * np.sin(y / 60))
            flood_width = 60 if severity == "high" else 35

            for x in range(max(0, x_center - flood_width), min(self.width, x_center + flood_width)):
                if terrain_map[y, x] != "water_body":
                    alpha = 0.7 - 0.3 * abs(x - x_center) / flood_width
                    draw.point((x, y), fill=flood_color)
                    terrain_map[y, x] = "water_body"

        # Alçak bölgelerde su birikintisi
        if severity == "high":
            low_areas = [(400, 500, 550, 580), (200, 400, 350, 440)]
            for x1, y1, x2, y2 in low_areas:
                for y in range(y1, min(y2, self.height)):
                    for x in range(x1, min(x2, self.width)):
                        if terrain_map[y, x] in ["open_field", "road", "park"]:
                            draw.point((x, y), fill=(80, 140, 200))
                            terrain_map[y, x] = "water_body"

        return info

    def _apply_landslide(self, draw, terrain_map, severity):
        """Heyelan etkilerini uygula"""
        info = {"slide_zones": []}
        slide_color = (140, 100, 60)

        # Yamaç bölgeleri oluştur ve heyelan uygula
        slide_zones = [(700, 0, 800, 200)] if severity == "high" else [(720, 0, 780, 100)]

        for x1, y1, x2, y2 in slide_zones:
            for y in range(y1, min(y2, self.height)):
                for x in range(x1, min(x2, self.width)):
                    if np.random.random() < 0.7:
                        draw.point((x, y), fill=slide_color)
                        terrain_map[y, x] = "slope"

            info["slide_zones"].append((x1, y1, x2, y2))

        return info

    def _find_safe_zones(self, terrain_map):
        """Güvenli bölgeleri bul"""
        safe_types = ["open_field", "park", "hospital"]
        zones = []

        for safe_type in safe_types:
            mask = terrain_map == safe_type
            if np.any(mask):
                coords = np.argwhere(mask)
                center_y = int(np.mean(coords[:, 0]))
                center_x = int(np.mean(coords[:, 1]))
                zones.append({
                    "type": safe_type,
                    "name": {"open_field": "Açık Alan", "park": "Park", "hospital": "Hastane"}.get(safe_type),
                    "center": (center_y, center_x),
                    "area": int(np.sum(mask))
                })

        return zones

    def _find_danger_zones(self, terrain_map):
        """Tehlikeli bölgeleri bul"""
        danger_types = ["rubble", "gas_station", "industrial", "water_body"]
        zones = []

        for danger_type in danger_types:
            mask = terrain_map == danger_type
            if np.any(mask):
                coords = np.argwhere(mask)
                center_y = int(np.mean(coords[:, 0]))
                center_x = int(np.mean(coords[:, 1]))
                zones.append({
                    "type": danger_type,
                    "name": TERRAIN_TYPES_TR.get(danger_type, danger_type),
                    "center": (center_y, center_x),
                    "area": int(np.sum(mask))
                })

        return zones


# Türkçe arazi isimleri
TERRAIN_TYPES_TR = {
    "building": "Bina", "forest": "Orman", "water_body": "Su Kütlesi",
    "wetland": "Sulak Alan", "road": "Yol", "open_field": "Açık Alan",
    "park": "Park", "industrial": "Endüstriyel", "gas_station": "Benzin İstasyonu",
    "hospital": "Hastane", "bridge": "Köprü", "slope": "Yamaç",
    "rubble": "Enkaz", "power_line": "Enerji Hattı"
}
