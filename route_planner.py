"""
SafeRoute AI - Güvenli Rota Planlama Motoru
A* algoritması ile en güvenli rotayı hesaplama
"""

import numpy as np
import heapq
from config import ROUTING_CONFIG, RISK_LEVELS, TERRAIN_TYPES


class RoutePlanner:
    """A* tabanlı güvenli rota planlama sistemi"""

    def __init__(self):
        self.config = ROUTING_CONFIG

    def find_safest_route(self, risk_map, terrain_map, start, end, num_alternatives=3):
        """
        En güvenli rotayı ve alternatiflerini bul

        Args:
            risk_map: 2D numpy array (0-1 risk değerleri)
            terrain_map: 2D numpy array (arazi türleri)
            start: (row, col) başlangıç noktası
            end: (row, col) hedef noktası
            num_alternatives: Alternatif rota sayısı

        Returns:
            dict: Ana rota + alternatifler + detaylı analiz
        """
        height, width = risk_map.shape

        # Başlangıç ve bitiş noktalarını kontrol et
        start = self._validate_point(start, height, width)
        end = self._validate_point(end, height, width)

        # Ana (en güvenli) rota
        primary_route = self._astar_safe_route(risk_map, terrain_map, start, end)

        if primary_route is None:
            return {
                "success": False,
                "message": "Güvenli rota bulunamadı! Tüm yollar çok tehlikeli.",
                "recommendation": "Helikopter veya deniz tahliyesi düşünülmeli."
            }

        # Rota analizi
        primary_analysis = self._analyze_route(primary_route, risk_map, terrain_map)

        # Alternatif rotalar
        alternatives = []
        for i in range(num_alternatives - 1):
            # Önceki rotalardan uzak alternatif bul
            penalty_map = self._create_penalty_map(
                risk_map, [primary_route] + [a["path"] for a in alternatives]
            )
            alt_route = self._astar_safe_route(penalty_map, terrain_map, start, end)
            if alt_route and alt_route != primary_route:
                alt_analysis = self._analyze_route(alt_route, risk_map, terrain_map)
                alternatives.append({
                    "path": alt_route,
                    "analysis": alt_analysis
                })

        # Geçilen tehlikeli bölgelerin detaylı uyarıları
        route_warnings = self._generate_route_warnings(
            primary_route, risk_map, terrain_map
        )

        # Adım adım navigasyon talimatları
        navigation = self._generate_navigation(primary_route, terrain_map, risk_map)

        return {
            "success": True,
            "primary_route": {
                "path": primary_route,
                "analysis": primary_analysis,
                "warnings": route_warnings,
                "navigation": navigation
            },
            "alternatives": alternatives,
            "summary": self._route_summary(primary_analysis, alternatives)
        }

    def _astar_safe_route(self, risk_map, terrain_map, start, end):
        """Modifiye A* algoritması - risk ağırlıklı"""
        height, width = risk_map.shape
        risk_weight = self.config["risk_weight"]
        distance_weight = self.config["distance_weight"]
        max_risk = self.config["max_risk_threshold"]

        # 8 yönlü hareket (diagonal dahil)
        directions = [
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)
        ]

        # A* başlatma
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}

        visited = set()

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == end:
                return self._reconstruct_path(came_from, current)

            if current in visited:
                continue
            visited.add(current)

            for dr, dc, move_cost in directions:
                neighbor = (current[0] + dr, current[1] + dc)

                # Sınır kontrolü
                if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                    continue

                if neighbor in visited:
                    continue

                # Risk kontrolü - aşırı tehlikeli bölgelerden geçme
                cell_risk = risk_map[neighbor[0], neighbor[1]]
                if cell_risk >= max_risk:
                    continue

                # Maliyet hesaplama: mesafe + risk penalty
                terrain = terrain_map[neighbor[0], neighbor[1]]
                terrain_info = TERRAIN_TYPES.get(terrain, {})

                # Geçiş maliyeti
                terrain_cost = terrain_info.get("risk_multiplier", 1.0)

                # Yol tercih bonusu
                if terrain == "road":
                    terrain_cost *= self.config["road_preference"]
                elif terrain == "open_field" or terrain == "park":
                    terrain_cost *= 0.8

                # Su üzerinden geçiş engeli
                if terrain == "water_body" and self.config["avoid_water"]:
                    terrain_cost *= 10.0

                # Toplam maliyet
                move_penalty = (
                    distance_weight * move_cost * terrain_cost +
                    risk_weight * cell_risk * move_cost
                )

                tentative_g = g_score[current] + move_penalty

                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None  # Rota bulunamadı

    def _heuristic(self, a, b):
        """Öklid mesafesi heuristic"""
        return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _reconstruct_path(self, came_from, current):
        """Yolu geri izle"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _create_penalty_map(self, risk_map, existing_routes, penalty_radius=30):
        """Önceki rotalardan uzak alternatif bulmak için ceza haritası"""
        penalty_map = risk_map.copy()

        for route in existing_routes:
            for point in route[::3]:  # Her 3. noktayı al (performans)
                r, c = point
                r_min = max(0, r - penalty_radius)
                r_max = min(risk_map.shape[0], r + penalty_radius)
                c_min = max(0, c - penalty_radius)
                c_max = min(risk_map.shape[1], c + penalty_radius)

                penalty_map[r_min:r_max, c_min:c_max] += 0.2

        return np.clip(penalty_map, 0, 0.95)

    def _validate_point(self, point, height, width):
        """Noktanın harita sınırları içinde olduğunu kontrol et"""
        r = max(0, min(point[0], height - 1))
        c = max(0, min(point[1], width - 1))
        return (r, c)

    def _analyze_route(self, path, risk_map, terrain_map):
        """Rota detaylı analizi"""
        if not path:
            return None

        risks = [risk_map[p[0], p[1]] for p in path]
        terrains = [terrain_map[p[0], p[1]] for p in path]

        # Geçilen arazi türleri
        terrain_segments = []
        current_terrain = terrains[0]
        segment_start = 0

        for i, terrain in enumerate(terrains):
            if terrain != current_terrain:
                terrain_segments.append({
                    "terrain": current_terrain,
                    "name": TERRAIN_TYPES.get(current_terrain, {}).get("name", current_terrain),
                    "start_index": segment_start,
                    "end_index": i - 1,
                    "length": i - segment_start,
                    "avg_risk": float(np.mean(risks[segment_start:i]))
                })
                current_terrain = terrain
                segment_start = i

        terrain_segments.append({
            "terrain": current_terrain,
            "name": TERRAIN_TYPES.get(current_terrain, {}).get("name", current_terrain),
            "start_index": segment_start,
            "end_index": len(terrains) - 1,
            "length": len(terrains) - segment_start,
            "avg_risk": float(np.mean(risks[segment_start:]))
        })

        # Toplam mesafe hesapla
        total_distance = 0
        for i in range(1, len(path)):
            dr = path[i][0] - path[i - 1][0]
            dc = path[i][1] - path[i - 1][1]
            total_distance += np.sqrt(dr ** 2 + dc ** 2)

        # Tehlikeli bölümleri belirle
        danger_segments = []
        in_danger = False
        danger_start = 0

        for i, risk in enumerate(risks):
            if risk > 0.6 and not in_danger:
                in_danger = True
                danger_start = i
            elif risk <= 0.6 and in_danger:
                in_danger = False
                danger_segments.append({
                    "start_index": danger_start,
                    "end_index": i,
                    "max_risk": float(max(risks[danger_start:i])),
                    "terrain": terrains[danger_start]
                })

        if in_danger:
            danger_segments.append({
                "start_index": danger_start,
                "end_index": len(risks) - 1,
                "max_risk": float(max(risks[danger_start:])),
                "terrain": terrains[danger_start]
            })

        return {
            "path_length": len(path),
            "total_distance_pixels": float(total_distance),
            "avg_risk": float(np.mean(risks)),
            "max_risk": float(np.max(risks)),
            "min_risk": float(np.min(risks)),
            "risk_std": float(np.std(risks)),
            "safety_score": float(1 - np.mean(risks)) * 100,
            "terrain_segments": terrain_segments,
            "danger_segments": danger_segments,
            "danger_segment_count": len(danger_segments),
            "risk_profile": [float(r) for r in risks[::max(1, len(risks) // 50)]]  # 50 nokta örnekle
        }

    def _generate_route_warnings(self, path, risk_map, terrain_map):
        """Rota üzerindeki tehlike uyarıları"""
        warnings = []
        prev_terrain = None

        for i, point in enumerate(path):
            r, c = point
            risk = risk_map[r, c]
            terrain = terrain_map[r, c]

            # Yeni arazi türüne girişte uyarı
            if terrain != prev_terrain:
                terrain_info = TERRAIN_TYPES.get(terrain, {})
                if terrain_info.get("risk_multiplier", 0) > 1.0:
                    warnings.append({
                        "step": i,
                        "location": point,
                        "type": "terrain_change",
                        "terrain": terrain,
                        "risk": float(risk),
                        "message": f"⚠️ {terrain_info.get('name', terrain)} bölgesine giriyorsunuz! {terrain_info.get('description', '')}",
                        "severity": "high" if terrain_info.get("risk_multiplier", 0) > 1.5 else "medium"
                    })

            # Yüksek risk uyarısı
            if risk > 0.7 and (not warnings or warnings[-1].get("type") != "high_risk" or
                               i - warnings[-1].get("step", 0) > 20):
                warnings.append({
                    "step": i,
                    "location": point,
                    "type": "high_risk",
                    "risk": float(risk),
                    "message": f"🚨 YÜKSEK RİSK BÖLGESİ! Risk: %{risk * 100:.0f} - Dikkatli ilerleyin!",
                    "severity": "critical" if risk > 0.85 else "high"
                })

            prev_terrain = terrain

        return warnings

    def _generate_navigation(self, path, terrain_map, risk_map):
        """Adım adım navigasyon talimatları"""
        if len(path) < 2:
            return []

        navigation = []
        step_size = max(1, len(path) // 20)  # ~20 navigasyon noktası

        prev_direction = None

        for i in range(0, len(path) - 1, step_size):
            current = path[i]
            next_point = path[min(i + step_size, len(path) - 1)]

            dr = next_point[0] - current[0]
            dc = next_point[1] - current[1]

            # Yön belirleme
            direction = self._get_direction(dr, dc)

            terrain = terrain_map[current[0], current[1]]
            terrain_info = TERRAIN_TYPES.get(terrain, {})
            risk = risk_map[current[0], current[1]]

            nav_step = {
                "step": len(navigation) + 1,
                "location": current,
                "direction": direction,
                "terrain": terrain_info.get("name", terrain),
                "risk_level": float(risk),
                "instruction": ""
            }

            # Talimat oluştur
            if direction != prev_direction:
                nav_step["instruction"] = f"{direction} yönüne dönün. "

            if risk > 0.7:
                nav_step["instruction"] += f"DİKKAT: Yüksek risk bölgesi (%{risk * 100:.0f})! "

            if terrain in ["water_body", "rubble", "industrial", "gas_station"]:
                nav_step["instruction"] += f"TEHLİKE: {terrain_info.get('description', '')} "
            elif terrain in ["road", "open_field"]:
                nav_step["instruction"] += f"Güvenli alan - {terrain_info.get('name', '')} üzerinde ilerliyorsunuz. "
            else:
                nav_step["instruction"] += f"{terrain_info.get('name', '')} bölgesinden geçiyorsunuz. "

            navigation.append(nav_step)
            prev_direction = direction

        # Son nokta
        navigation.append({
            "step": len(navigation) + 1,
            "location": path[-1],
            "direction": "Varış",
            "terrain": TERRAIN_TYPES.get(terrain_map[path[-1][0], path[-1][1]], {}).get("name", ""),
            "risk_level": float(risk_map[path[-1][0], path[-1][1]]),
            "instruction": "✅ HEDEFE ULAŞTINIZ! Güvenli bölgedesiniz."
        })

        return navigation

    def _get_direction(self, dr, dc):
        """Yön ismi belirle"""
        if abs(dr) < 2 and abs(dc) < 2:
            return "Düz"

        if dr < -2 and abs(dc) < abs(dr) * 0.5:
            return "Kuzey"
        elif dr > 2 and abs(dc) < abs(dr) * 0.5:
            return "Güney"
        elif dc > 2 and abs(dr) < abs(dc) * 0.5:
            return "Doğu"
        elif dc < -2 and abs(dr) < abs(dc) * 0.5:
            return "Batı"
        elif dr < 0 and dc > 0:
            return "Kuzeydoğu"
        elif dr < 0 and dc < 0:
            return "Kuzeybatı"
        elif dr > 0 and dc > 0:
            return "Güneydoğu"
        elif dr > 0 and dc < 0:
            return "Güneybatı"

        return "Düz"

    def _route_summary(self, primary_analysis, alternatives):
        """Rota özeti"""
        summary = {
            "primary_safety_score": primary_analysis["safety_score"],
            "primary_distance": primary_analysis["total_distance_pixels"],
            "primary_max_risk": primary_analysis["max_risk"],
            "primary_danger_zones": primary_analysis["danger_segment_count"],
            "alternative_count": len(alternatives),
            "recommendation": ""
        }

        if primary_analysis["safety_score"] > 80:
            summary["recommendation"] = "✅ Ana rota güvenli. Bu rotayı takip edin."
        elif primary_analysis["safety_score"] > 60:
            summary["recommendation"] = "⚠️ Ana rota orta düzey risk içeriyor. Dikkatli ilerleyin."
        elif primary_analysis["safety_score"] > 40:
            summary["recommendation"] = "🚨 Ana rota riskli! Mümkünse alternatif rotayı kullanın."
        else:
            summary["recommendation"] = "❌ TÜM ROTALAR TEHLİKELİ! Hava tahliyesi önerilir."

        if alternatives:
            best_alt = max(alternatives, key=lambda a: a["analysis"]["safety_score"])
            if best_alt["analysis"]["safety_score"] > primary_analysis["safety_score"] + 10:
                summary["recommendation"] += f"\n📍 Alternatif rota daha güvenli (Güvenlik: %{best_alt['analysis']['safety_score']:.0f})"

        return summary
