"""
SafeRoute AI - Risk Analiz Motoru
Çok katmanlı risk haritası oluşturma ve analiz
"""

import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt
from config import TERRAIN_TYPES, DISASTER_TYPES, RISK_LEVELS, ROUTING_CONFIG


class RiskAnalyzer:
    """Çok katmanlı risk analizi ve tehlike haritası oluşturma"""

    def __init__(self):
        self.risk_layers = {}

    def generate_risk_map(self, terrain_map, disaster_result, grid_size=None):
        """
        Çok katmanlı risk haritası oluştur

        Katmanlar:
        1. Arazi riski (terrain risk)
        2. Afet riski (disaster risk)
        3. İkincil risk (secondary risk - yangın, sel, çökme)
        4. Yakınlık riski (proximity risk - tehlikeli nesnelere yakınlık)
        5. Erişilebilirlik riski (accessibility - geçiş zorluğu)

        Returns:
            dict: Katmanlı risk haritası ve analiz sonuçları
        """
        height, width = terrain_map.shape
        disaster_type = disaster_result.get("disaster_type", "earthquake")

        # Katman 1: Arazi Risk Haritası
        terrain_risk = self._calculate_terrain_risk(terrain_map, disaster_type)

        # Katman 2: Afet Bölgesi Risk Haritası
        disaster_risk = self._calculate_disaster_risk(
            disaster_result.get("zones", []), width, height
        )

        # Katman 3: İkincil Risk Haritası
        secondary_risk = self._calculate_secondary_risk(
            terrain_map, disaster_type, disaster_result.get("warnings", [])
        )

        # Katman 4: Yakınlık Risk Haritası
        proximity_risk = self._calculate_proximity_risk(terrain_map, disaster_type)

        # Katman 5: Erişilebilirlik Haritası
        accessibility = self._calculate_accessibility(terrain_map)

        # Ağırlıklı birleştirme
        weights = self._get_layer_weights(disaster_type)
        combined_risk = (
            terrain_risk * weights["terrain"] +
            disaster_risk * weights["disaster"] +
            secondary_risk * weights["secondary"] +
            proximity_risk * weights["proximity"] +
            accessibility * weights["accessibility"]
        )

        # Normalize (0-1 arası)
        combined_risk = np.clip(combined_risk, 0, 1)

        # Gaussian yumuşatma (gerçekçi geçişler için)
        combined_risk = gaussian_filter(combined_risk, sigma=3)
        combined_risk = np.clip(combined_risk, 0, 1)

        # Risk seviyesi haritası
        risk_level_map = self._classify_risk_levels(combined_risk)

        # Tehlike analizi
        hazard_analysis = self._analyze_hazards(
            terrain_map, combined_risk, disaster_result, disaster_type
        )

        self.risk_layers = {
            "terrain": terrain_risk,
            "disaster": disaster_risk,
            "secondary": secondary_risk,
            "proximity": proximity_risk,
            "accessibility": accessibility
        }

        return {
            "combined_risk": combined_risk,
            "risk_level_map": risk_level_map,
            "risk_layers": self.risk_layers,
            "hazard_analysis": hazard_analysis,
            "layer_weights": weights,
            "statistics": self._risk_statistics(combined_risk)
        }

    def _calculate_terrain_risk(self, terrain_map, disaster_type):
        """Arazi türüne göre risk hesapla"""
        height, width = terrain_map.shape
        risk = np.zeros((height, width))

        risk_key = f"{disaster_type}_risk"

        for terrain_type, info in TERRAIN_TYPES.items():
            mask = terrain_map == terrain_type
            base_risk = info.get(risk_key, info.get("risk_multiplier", 0.5) / 2.5)
            risk[mask] = base_risk

        return risk

    def _calculate_disaster_risk(self, zones, width, height):
        """Afet bölgelerinden uzaklığa göre risk hesapla"""
        risk = np.zeros((height, width))

        for zone in zones:
            cx, cy = zone.get("center", (0, 0))
            risk_level = zone.get("risk_level", 0.5)
            bounds = zone.get("bounds", (cx - 50, cy - 50, 100, 100))

            x, y, w, h = bounds

            # Afet merkezi etrafında gradient risk
            Y, X = np.ogrid[:height, :width]
            dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
            max_dist = max(w, h) * 2

            zone_risk = np.where(
                dist < max_dist,
                risk_level * np.exp(-dist / (max_dist * 0.5)),
                0
            )
            risk = np.maximum(risk, zone_risk)

        return np.clip(risk, 0, 1)

    def _calculate_secondary_risk(self, terrain_map, disaster_type, warnings):
        """İkincil riskleri hesapla"""
        height, width = terrain_map.shape
        risk = np.zeros((height, width))

        disaster_info = DISASTER_TYPES.get(disaster_type, {})
        secondary_risks = disaster_info.get("secondary_risks", [])

        if "fire" in secondary_risks:
            # Orman ve endüstriyel alanlar yakınında yangın riski
            forest_mask = (terrain_map == "forest").astype(np.float32)
            industrial_mask = (terrain_map == "industrial").astype(np.float32)
            gas_mask = (terrain_map == "gas_station").astype(np.float32)

            fire_source = forest_mask * 0.6 + industrial_mask * 0.8 + gas_mask * 0.95
            if np.any(fire_source > 0):
                fire_risk = gaussian_filter(fire_source, sigma=20)
                risk = np.maximum(risk, fire_risk)

        if "flood" in secondary_risks or "tsunami" in secondary_risks:
            # Su kütleleri yakınında sel riski
            water_mask = (terrain_map == "water_body").astype(np.float32)
            wetland_mask = (terrain_map == "wetland").astype(np.float32)

            flood_source = water_mask * 0.9 + wetland_mask * 0.7
            if np.any(flood_source > 0):
                flood_risk = gaussian_filter(flood_source, sigma=25)
                risk = np.maximum(risk, flood_risk)

        if "building_collapse" in secondary_risks:
            # Bina yakınlarında çökme riski
            building_mask = (terrain_map == "building").astype(np.float32)
            if np.any(building_mask > 0):
                collapse_risk = gaussian_filter(building_mask * 0.85, sigma=10)
                risk = np.maximum(risk, collapse_risk)

        if "landslide" in secondary_risks:
            # Yamaç ve sulak alan yakınında heyelan riski
            slope_mask = (terrain_map == "slope").astype(np.float32)
            if np.any(slope_mask > 0):
                slide_risk = gaussian_filter(slope_mask * 0.8, sigma=15)
                risk = np.maximum(risk, slide_risk)

        if "gas_leak" in secondary_risks:
            # Endüstriyel alan ve benzin istasyonu yakınında gaz sızıntısı
            gas_source = ((terrain_map == "gas_station").astype(np.float32) * 0.95 +
                         (terrain_map == "industrial").astype(np.float32) * 0.7)
            if np.any(gas_source > 0):
                gas_risk = gaussian_filter(gas_source, sigma=15)
                risk = np.maximum(risk, gas_risk)

        return np.clip(risk, 0, 1)

    def _calculate_proximity_risk(self, terrain_map, disaster_type):
        """Tehlikeli nesnelere yakınlık riski"""
        height, width = terrain_map.shape
        risk = np.zeros((height, width))

        # Tehlikeli bölgeleri belirle
        dangerous_types = ["gas_station", "industrial", "power_line", "rubble"]
        if disaster_type == "earthquake":
            dangerous_types.extend(["building", "bridge"])
        elif disaster_type == "fire":
            dangerous_types.extend(["forest", "gas_station"])
        elif disaster_type == "flood":
            dangerous_types.extend(["water_body", "wetland", "bridge"])

        for dtype in dangerous_types:
            mask = (terrain_map == dtype).astype(np.float32)
            if np.any(mask > 0):
                # Mesafe dönüşümü
                dist = distance_transform_edt(1 - mask)
                terrain_info = TERRAIN_TYPES.get(dtype, {})
                base_risk = terrain_info.get("risk_multiplier", 1.0) / 2.5

                # Yakınlık riski (mesafe arttıkça azalır)
                prox_risk = base_risk * np.exp(-dist / 30)
                risk = np.maximum(risk, prox_risk)

        return np.clip(risk, 0, 1)

    def _calculate_accessibility(self, terrain_map):
        """Geçiş zorluğu / erişilebilirlik haritası"""
        height, width = terrain_map.shape
        accessibility = np.full((height, width), 0.3)

        # Yollar kolay geçilebilir
        accessibility[terrain_map == "road"] = 0.1
        accessibility[terrain_map == "open_field"] = 0.15
        accessibility[terrain_map == "park"] = 0.2

        # Zor geçilen alanlar
        accessibility[terrain_map == "water_body"] = 0.95
        accessibility[terrain_map == "rubble"] = 0.8
        accessibility[terrain_map == "forest"] = 0.5
        accessibility[terrain_map == "wetland"] = 0.7
        accessibility[terrain_map == "building"] = 0.85
        accessibility[terrain_map == "slope"] = 0.6

        return accessibility

    def _get_layer_weights(self, disaster_type):
        """Afet türüne göre katman ağırlıklarını belirle"""
        weights = {
            "earthquake": {
                "terrain": 0.25, "disaster": 0.30, "secondary": 0.20,
                "proximity": 0.15, "accessibility": 0.10
            },
            "fire": {
                "terrain": 0.20, "disaster": 0.35, "secondary": 0.25,
                "proximity": 0.10, "accessibility": 0.10
            },
            "flood": {
                "terrain": 0.30, "disaster": 0.25, "secondary": 0.20,
                "proximity": 0.15, "accessibility": 0.10
            },
            "landslide": {
                "terrain": 0.30, "disaster": 0.25, "secondary": 0.15,
                "proximity": 0.15, "accessibility": 0.15
            }
        }
        return weights.get(disaster_type, weights["earthquake"])

    def _classify_risk_levels(self, risk_map):
        """Risk haritasını seviyelere ayır"""
        level_map = np.full(risk_map.shape, "very_low", dtype=object)

        for level_name, level_info in RISK_LEVELS.items():
            mask = (risk_map >= level_info["min"]) & (risk_map < level_info["max"])
            level_map[mask] = level_name

        return level_map

    def _analyze_hazards(self, terrain_map, risk_map, disaster_result, disaster_type):
        """Detaylı tehlike analizi ve uyarılar"""
        hazards = []
        height, width = terrain_map.shape

        # Yüksek riskli bölgeleri tespit et
        high_risk_mask = risk_map > 0.7
        if np.any(high_risk_mask):
            high_risk_percent = (np.sum(high_risk_mask) / (width * height)) * 100
            hazards.append({
                "type": "high_risk_area",
                "severity": "critical",
                "message": f"🚨 Toplam alanın %{high_risk_percent:.1f}'i YÜKSEK RİSKLİ bölge!",
                "recommendation": "Bu bölgelerden kesinlikle uzak durun. Alternatif rota kullanın."
            })

        # Arazi bazlı tehlikeler
        terrain_hazards = self._terrain_specific_hazards(terrain_map, disaster_type)
        hazards.extend(terrain_hazards)

        # Afet bazlı tehlikeler
        for zone in disaster_result.get("zones", []):
            hazards.append({
                "type": zone.get("type", "unknown"),
                "severity": zone.get("severity", "medium"),
                "message": f"⚠️ {zone.get('name', 'Bilinmeyen')}: Merkez ({zone['center'][0]}, {zone['center'][1]})",
                "recommendation": self._get_recommendation(zone.get("type"), disaster_type)
            })

        # Uyarıları ekle
        for warning in disaster_result.get("warnings", []):
            hazards.append({
                "type": warning.get("type", "warning"),
                "severity": "warning",
                "message": warning.get("message", ""),
                "recommendation": self._get_warning_recommendation(warning.get("type"))
            })

        return hazards

    def _terrain_specific_hazards(self, terrain_map, disaster_type):
        """Arazi türüne özel tehlikeler"""
        hazards = []

        terrain_checks = {
            "earthquake": [
                ("building", "🏚️ Bina bölgeleri tespit edildi - Deprem sonrası çökme riski!",
                 "Binalardan en az 50m uzak durun. Açık alanlara yönelin."),
                ("bridge", "🌉 Köprü tespit edildi - Yapısal hasar riski!",
                 "Köprülerden geçmekten kaçının. Alternatif geçiş noktası arayın."),
                ("gas_station", "⛽ Benzin istasyonu tespit edildi - PATLAMA RİSKİ!",
                 "En az 200m güvenli mesafe koruyun!"),
                ("industrial", "🏭 Endüstriyel alan - Kimyasal sızıntı riski!",
                 "Endüstriyel tesislerden uzak durun. Rüzgar yönünü kontrol edin."),
                ("water_body", "🌊 Su kütlesi yakınında - Sel/Tsunami riski!",
                 "Yüksek noktalara çıkın. Kıyıdan uzak durun."),
                ("power_line", "⚡ Enerji hattı - Elektrik çarpma riski!",
                 "Devrilmiş direklere ve kopmuş kablolara dikkat! 10m mesafe koruyun.")
            ],
            "fire": [
                ("forest", "🌲 Orman alanı - Yangın yayılma riski ÇOK YÜKSEK!",
                 "Orman alanlarından uzak durun. Rüzgar yönünün tersine ilerleyin."),
                ("gas_station", "⛽ Benzin istasyonu - PATLAMA TEHLİKESİ!",
                 "ACİL: En az 300m mesafe koruyun!"),
                ("industrial", "🏭 Endüstriyel alan - Yangın + Kimyasal patlama!",
                 "Tesis yakınından geçmeyin! Zehirli duman riski."),
                ("building", "🏢 Bina bölgesi - İç yangın ve yapısal çökme riski!",
                 "Binaların alt rüzgar tarafında kalmayın.")
            ],
            "flood": [
                ("water_body", "🌊 Su kütlesi - Taşkın riski!",
                 "Nehir ve göl kenarlarından uzak durun. Yüksek zemine çıkın."),
                ("wetland", "🏞️ Sulak alan - Batma ve akıntı riski!",
                 "Sulak alanlardan kesinlikle geçmeyin!"),
                ("bridge", "🌉 Köprü - Sel suları altında kalma riski!",
                 "Köprü durumunu kontrol edin. Sular yüksekse geçmeyin."),
                ("slope", "⛰️ Eğimli arazi - Heyelan riski!",
                 "Sel + eğim = heyelan. Düz araziden ilerleyin.")
            ]
        }

        for terrain_type, message, recommendation in terrain_checks.get(disaster_type, []):
            if np.any(terrain_map == terrain_type):
                count = np.sum(terrain_map == terrain_type)
                percentage = (count / terrain_map.size) * 100
                if percentage > 0.5:  # En az %0.5 alan kaplıyorsa
                    hazards.append({
                        "type": f"{terrain_type}_hazard",
                        "severity": "high" if TERRAIN_TYPES.get(terrain_type, {}).get("risk_multiplier", 1) > 1.5 else "medium",
                        "message": f"{message} (Alan: %{percentage:.1f})",
                        "recommendation": recommendation
                    })

        return hazards

    def _get_recommendation(self, zone_type, disaster_type):
        """Bölge türüne göre öneri"""
        recommendations = {
            "structural_damage": "Hasar görmüş yapılardan uzak durun. Artçı sarsıntı riski var.",
            "active_fire": "ACİL! Yangın bölgesinden derhal uzaklaşın. Rüzgar yönünün tersine gidin.",
            "burned_area": "Yanmış alan - zemin kararsız olabilir. Dikkatli geçin.",
            "flooded_area": "Sular çekilene kadar bu bölgeden geçmeyin. Akıntı tehlikesi!",
            "landslide_area": "Heyelan bölgesi - ek kaymalar olabilir. Tamamen kaçının.",
        }
        return recommendations.get(zone_type, "Bu bölgeden uzak durun ve alternatif rota kullanın.")

    def _get_warning_recommendation(self, warning_type):
        """Uyarı türüne göre öneri"""
        recommendations = {
            "building_collapse_risk": "Binaların en az 50m uzağından geçin. Açık alanları tercih edin.",
            "secondary_flood_risk": "Yüksek zemine çıkın. Kıyı şeridinden uzak durun.",
            "secondary_fire_risk": "Gaz vanalarını kapattırın. Kıvılcım kaynağından uzak durun.",
            "fire_spread_risk": "Rüzgar yönünü kontrol edin. Yangına karşı rüzgar tarafında kalın.",
            "low_area_risk": "Tepe ve yükseltilere yönelin. Çukur bölgelerden kaçının.",
            "slope_risk": "Düz arazi üzerinden ilerleyin. Yamaçlardan uzak durun."
        }
        return recommendations.get(warning_type, "Dikkatli olun ve güvenli rotayı takip edin.")

    def _risk_statistics(self, risk_map):
        """Risk haritası istatistikleri"""
        total = risk_map.size
        return {
            "mean_risk": float(np.mean(risk_map)),
            "max_risk": float(np.max(risk_map)),
            "min_risk": float(np.min(risk_map)),
            "std_risk": float(np.std(risk_map)),
            "very_low_percent": float(np.sum(risk_map < 0.2) / total * 100),
            "low_percent": float(np.sum((risk_map >= 0.2) & (risk_map < 0.4)) / total * 100),
            "medium_percent": float(np.sum((risk_map >= 0.4) & (risk_map < 0.6)) / total * 100),
            "high_percent": float(np.sum((risk_map >= 0.6) & (risk_map < 0.8)) / total * 100),
            "very_high_percent": float(np.sum((risk_map >= 0.8) & (risk_map < 0.9)) / total * 100),
            "extreme_percent": float(np.sum(risk_map >= 0.9) / total * 100),
            "safe_area_percent": float(np.sum(risk_map < 0.4) / total * 100),
            "dangerous_area_percent": float(np.sum(risk_map >= 0.7) / total * 100)
        }
