"""
SafeRoute AI - Acil Durum Servisleri
Hastane, eczane, toplanma alani, AFAD, deprem verisi, hava durumu
"""

import requests
import json
import os
import math
from datetime import datetime


class EmergencyServices:
    """Acil durum servisleri ve veri entegrasyonu"""

    # Kahramanmaras bolgesindeki gercek hastaneler
    HOSPITALS_DB = {
        "kahramanmaras": [
            {"name": "Kahramanmaras Sutcu Imam Uni. Hastanesi", "lat": 37.5745, "lon": 36.9180,
             "type": "Universite", "capacity": 800, "emergency": True, "helipad": True},
            {"name": "Kahramanmaras Devlet Hastanesi", "lat": 37.5890, "lon": 36.9350,
             "type": "Devlet", "capacity": 500, "emergency": True, "helipad": False},
            {"name": "Kahramanmaras Necip Fazil Sehir Hastanesi", "lat": 37.5920, "lon": 36.9520,
             "type": "Sehir", "capacity": 1200, "emergency": True, "helipad": True},
            {"name": "Ozel Kahramanmaras Hastanesi", "lat": 37.5830, "lon": 36.9280,
             "type": "Ozel", "capacity": 200, "emergency": True, "helipad": False},
            {"name": "Memorial Kahramanmaras", "lat": 37.5780, "lon": 36.9450,
             "type": "Ozel", "capacity": 150, "emergency": True, "helipad": False}
        ],
        "manavgat": [
            {"name": "Manavgat Devlet Hastanesi", "lat": 36.7870, "lon": 31.4430,
             "type": "Devlet", "capacity": 300, "emergency": True, "helipad": False},
            {"name": "Antalya Egitim ve Arastirma Hastanesi", "lat": 36.8850, "lon": 30.7050,
             "type": "Egitim", "capacity": 900, "emergency": True, "helipad": True}
        ],
        "artvin": [
            {"name": "Artvin Devlet Hastanesi", "lat": 41.1830, "lon": 41.8180,
             "type": "Devlet", "capacity": 200, "emergency": True, "helipad": False},
            {"name": "Artvin Coruh Uni. Hastanesi", "lat": 41.1900, "lon": 41.8100,
             "type": "Universite", "capacity": 250, "emergency": True, "helipad": False}
        ]
    }

    # Toplanma alanlari
    ASSEMBLY_POINTS_DB = {
        "kahramanmaras": [
            {"name": "Kahramanmaras Stadyumu Alani", "lat": 37.5800, "lon": 36.9250, "capacity": 5000,
             "facilities": ["cadi̇r", "su", "jenerator", "tuvalet"]},
            {"name": "12 Subat Stadyumu", "lat": 37.5950, "lon": 36.9400, "capacity": 15000,
             "facilities": ["cadır", "su", "jenerator", "tuvalet", "saglik"]},
            {"name": "Eski Sanayi Acik Alani", "lat": 37.5750, "lon": 36.9500, "capacity": 3000,
             "facilities": ["cadır", "su"]},
            {"name": "Kurtulus Parki", "lat": 37.5870, "lon": 36.9320, "capacity": 2000,
             "facilities": ["su", "tuvalet"]},
            {"name": "Sehir Mezarligi Yani Acik Alan", "lat": 37.5700, "lon": 36.9100, "capacity": 4000,
             "facilities": ["cadır", "su", "jenerator"]},
            {"name": "Havalimani Cevresi Acik Alan", "lat": 37.5400, "lon": 36.9600, "capacity": 10000,
             "facilities": ["cadır", "su", "jenerator", "tuvalet", "saglik", "helipad"]},
            {"name": "Universite Kampusu Acik Alani", "lat": 37.5740, "lon": 36.9170, "capacity": 8000,
             "facilities": ["cadır", "su", "jenerator", "tuvalet", "saglik"]}
        ],
        "manavgat": [
            {"name": "Manavgat Stadyumu", "lat": 36.7880, "lon": 31.4380, "capacity": 5000,
             "facilities": ["cadır", "su", "jenerator"]},
            {"name": "Sahil Acik Alani", "lat": 36.7650, "lon": 31.4500, "capacity": 3000,
             "facilities": ["su"]}
        ],
        "artvin": [
            {"name": "Artvin Stadyumu", "lat": 41.1850, "lon": 41.8200, "capacity": 3000,
             "facilities": ["cadır", "su", "jenerator"]},
            {"name": "Sehir Meydani", "lat": 41.1830, "lon": 41.8170, "capacity": 1500,
             "facilities": ["su"]}
        ]
    }

    # AFAD Birimleri
    AFAD_UNITS_DB = {
        "kahramanmaras": [
            {"name": "Kahramanmaras AFAD Il Mudurlugu", "lat": 37.5880, "lon": 36.9280,
             "type": "Il Mudurlugu", "resources": ["arama_kurtarma", "saglik", "lojistik"]},
            {"name": "AFAD Lojistik Deposu", "lat": 37.5600, "lon": 36.9500,
             "type": "Depo", "resources": ["cadır", "battaniye", "gida", "su"]},
            {"name": "UMKE Ekibi Karargahi", "lat": 37.5850, "lon": 36.9300,
             "type": "Saglik", "resources": ["ambulans", "saglik_ekibi", "ilac"]}
        ]
    }

    def __init__(self):
        self.cache_dir = "data/emergency_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_nearest_hospitals(self, lat, lon, scenario="kahramanmaras", max_results=5):
        """En yakin hastaneleri bul"""
        hospitals = self.HOSPITALS_DB.get(scenario, self.HOSPITALS_DB["kahramanmaras"])
        for h in hospitals:
            h["distance_km"] = self._haversine(lat, lon, h["lat"], h["lon"])
        hospitals.sort(key=lambda x: x["distance_km"])
        return hospitals[:max_results]

    def get_assembly_points(self, lat, lon, scenario="kahramanmaras", max_results=5):
        """En yakin toplanma alanlarini bul"""
        points = self.ASSEMBLY_POINTS_DB.get(scenario, self.ASSEMBLY_POINTS_DB["kahramanmaras"])
        for p in points:
            p["distance_km"] = self._haversine(lat, lon, p["lat"], p["lon"])
        points.sort(key=lambda x: x["distance_km"])
        return points[:max_results]

    def get_afad_units(self, scenario="kahramanmaras"):
        """AFAD birimlerini getir"""
        return self.AFAD_UNITS_DB.get(scenario, [])

    def get_recent_earthquakes(self, lat, lon, radius_km=100):
        """
        Kandilli Rasathanesi / AFAD'dan son deprem verilerini cek
        (Demo icin simule edilmis veri)
        """
        # Gercek API: https://deprem.afad.gov.tr/apiv2/event/filter
        # Demo veri - Kahramanmaras artci sarsintilar benzeri
        earthquakes = [
            {"date": "2023-02-06 04:17:00", "lat": 37.5858, "lon": 36.9371, "depth": 10,
             "magnitude": 7.8, "type": "Mw", "location": "Pazarcik (Kahramanmaras)", "main": True},
            {"date": "2023-02-06 13:24:00", "lat": 38.0240, "lon": 37.2030, "depth": 7,
             "magnitude": 7.6, "type": "Mw", "location": "Elbistan (Kahramanmaras)", "main": True},
            {"date": "2023-02-06 04:26:00", "lat": 37.6100, "lon": 36.9500, "depth": 12,
             "magnitude": 5.6, "type": "ML", "location": "Kahramanmaras Merkez"},
            {"date": "2023-02-06 05:01:00", "lat": 37.5500, "lon": 37.0200, "depth": 8,
             "magnitude": 5.1, "type": "ML", "location": "Turkoglu (Kahramanmaras)"},
            {"date": "2023-02-06 06:15:00", "lat": 37.6800, "lon": 36.8700, "depth": 15,
             "magnitude": 4.8, "type": "ML", "location": "Dulkadiroglu (Kahramanmaras)"},
            {"date": "2023-02-06 07:30:00", "lat": 37.4900, "lon": 37.1000, "depth": 10,
             "magnitude": 4.5, "type": "ML", "location": "Nurhak (Kahramanmaras)"},
            {"date": "2023-02-06 08:45:00", "lat": 37.7200, "lon": 36.7500, "depth": 18,
             "magnitude": 4.2, "type": "ML", "location": "Andirin (Kahramanmaras)"},
            {"date": "2023-02-06 10:12:00", "lat": 37.5200, "lon": 36.8800, "depth": 11,
             "magnitude": 4.0, "type": "ML", "location": "Onikisubat (Kahramanmaras)"},
            {"date": "2023-02-06 12:00:00", "lat": 37.6500, "lon": 37.0500, "depth": 9,
             "magnitude": 5.3, "type": "ML", "location": "Goksun (Kahramanmaras)"},
            {"date": "2023-02-06 15:30:00", "lat": 37.4500, "lon": 36.9800, "depth": 14,
             "magnitude": 3.8, "type": "ML", "location": "Pazarcik (Kahramanmaras)"},
            {"date": "2023-02-07 02:20:00", "lat": 37.5600, "lon": 36.9100, "depth": 10,
             "magnitude": 4.7, "type": "ML", "location": "Kahramanmaras Merkez"},
            {"date": "2023-02-07 08:00:00", "lat": 37.6300, "lon": 37.1200, "depth": 12,
             "magnitude": 4.3, "type": "ML", "location": "Elbistan (Kahramanmaras)"}
        ]

        # Mesafe filtresi
        filtered = []
        for eq in earthquakes:
            dist = self._haversine(lat, lon, eq["lat"], eq["lon"])
            if dist <= radius_km:
                eq["distance_km"] = round(dist, 1)
                filtered.append(eq)

        return filtered

    def get_aftershock_risk_zones(self, main_lat, main_lon, magnitude):
        """Artci sarsintilar icin risk bolgeleri hesapla"""
        zones = []

        # Ana fay hatti boyunca yuksek risk
        # Bath yasasina gore en buyuk artci ~ ana sok - 1.2
        expected_max_aftershock = magnitude - 1.2

        # Yuksek risk bolgesi (merkez yakinlari)
        zones.append({
            "name": "Cok Yuksek Artci Risk",
            "center": [main_lat, main_lon],
            "radius_km": 20,
            "risk_level": 0.9,
            "expected_magnitude": f"M{expected_max_aftershock:.1f}+",
            "color": "#ff0000",
            "description": "Guclu artci sarsintilar bekleniyor. Hasarli binalara kesinlikle girmeyin!"
        })

        # Orta risk bolgesi
        zones.append({
            "name": "Yuksek Artci Risk",
            "center": [main_lat, main_lon],
            "radius_km": 50,
            "risk_level": 0.7,
            "expected_magnitude": f"M{expected_max_aftershock - 1:.1f}-{expected_max_aftershock:.1f}",
            "color": "#ff8c00",
            "description": "Artci sarsintilar devam edecek. Dikkatli olun."
        })

        # Genis etki alani
        zones.append({
            "name": "Orta Artci Risk",
            "center": [main_lat, main_lon],
            "radius_km": 100,
            "risk_level": 0.4,
            "expected_magnitude": f"M3.0-{expected_max_aftershock - 1:.1f}",
            "color": "#ffd700",
            "description": "Hafif-orta artci sarsintilar hissedilebilir."
        })

        return zones

    def get_population_density(self, lat, lon, scenario="kahramanmaras"):
        """Nufus yogunlugu bilgisi (kurtarma onceligi icin)"""
        density_data = {
            "kahramanmaras": {
                "city_name": "Kahramanmaras",
                "total_population": 1177436,
                "urban_population": 607544,
                "districts": [
                    {"name": "Dulkadiroglu", "population": 292678, "lat": 37.5750, "lon": 36.9300,
                     "priority": "critical", "density": "yuksek"},
                    {"name": "Onikisubat", "population": 487235, "lat": 37.5950, "lon": 36.9450,
                     "priority": "critical", "density": "cok_yuksek"},
                    {"name": "Pazarcik", "population": 73789, "lat": 37.4850, "lon": 37.2900,
                     "priority": "high", "density": "orta"},
                    {"name": "Turkoglu", "population": 79832, "lat": 37.3700, "lon": 36.8530,
                     "priority": "high", "density": "orta"},
                    {"name": "Elbistan", "population": 141061, "lat": 38.2040, "lon": 37.1980,
                     "priority": "critical", "density": "yuksek"},
                    {"name": "Goksun", "population": 52835, "lat": 38.0200, "lon": 36.4900,
                     "priority": "medium", "density": "dusuk"},
                    {"name": "Afsin", "population": 80024, "lat": 38.2500, "lon": 36.9200,
                     "priority": "high", "density": "orta"},
                    {"name": "Andirin", "population": 34803, "lat": 37.5700, "lon": 36.3500,
                     "priority": "medium", "density": "dusuk"}
                ]
            }
        }
        return density_data.get(scenario, density_data["kahramanmaras"])

    def get_weather_conditions(self, lat, lon, scenario="kahramanmaras"):
        """Hava durumu bilgisi (kurtarma operasyonunu etkiler)"""
        weather_db = {
            "kahramanmaras": {
                "date": "2023-02-06", "temperature": -3, "feels_like": -8,
                "humidity": 75, "wind_speed": 25, "wind_direction": "Kuzeybati",
                "condition": "Hafif Kar Yagisli", "visibility_km": 3, "snow_depth_cm": 5,
                "alerts": [
                    "Soguk hava: Hipotermi riski yuksek! Enkaz altindakiler icin kritik.",
                    "Kar yagisi: Kurtarma operasyonlarini yavaslatabilir.",
                    "Dusuk gorunurluk: Helikopter operasyonlari sinirli.",
                    "Ruzgar: Cadır kurulumu etkilenebilir."
                ],
                "rescue_impact": {
                    "helicopter_ops": "sinirli", "ground_ops": "yavas",
                    "survivor_risk": "yuksek", "hypothermia_hours": 6,
                    "recommendation": "Isitma ekipmani oncelikli. Soguk hava nedeniyle enkaz altinda hayatta kalma suresi kisaliyor."
                }
            },
            "manavgat": {
                "date": "2021-07-28", "temperature": 42, "feels_like": 46,
                "humidity": 15, "wind_speed": 45, "wind_direction": "Guneybati",
                "condition": "Sicak ve Kuru - Ruzgarli", "visibility_km": 2, "snow_depth_cm": 0,
                "alerts": [
                    "Asiri sicak: Itfaiye ekipleri icin isicarpma riski!",
                    "Kuvvetli ruzgar: Yangin yayilma hizi artabilir!",
                    "Dusuk nem: Yangin sondurme zorlasir.",
                    "Dusuk gorunurluk: Duman nedeniyle hava operasyonlari riskli."
                ],
                "rescue_impact": {
                    "helicopter_ops": "duman_sinirli", "ground_ops": "ruzgar_riski",
                    "survivor_risk": "orta", "hypothermia_hours": 0,
                    "recommendation": "Ruzgar yonunu surekli takip edin. Sogutma ekipmani oncelikli. Tahliye rotalarini ruzgar yonune gore belirleyin."
                }
            },
            "artvin": {
                "date": "2021-07-14", "temperature": 22, "feels_like": 24,
                "humidity": 95, "wind_speed": 15, "wind_direction": "Kuzey",
                "condition": "Yogun Yagmurlu", "visibility_km": 1, "snow_depth_cm": 0,
                "alerts": [
                    "Yogun yagis devam ediyor: Ek sel riski!",
                    "Zemin doymus: Heyelan tehlikesi cok yuksek!",
                    "Cok dusuk gorunurluk: Hava operasyonlari imkansiz.",
                    "Yollar kaygan ve hasar gormus: Kara ulasimi zor."
                ],
                "rescue_impact": {
                    "helicopter_ops": "imkansiz", "ground_ops": "cok_zor",
                    "survivor_risk": "yuksek", "hypothermia_hours": 0,
                    "recommendation": "Yagis durmasini bekleyin. Dere yataklarina yaklasmaktan kacinin. Yuksek noktalara tahliye oncelikli."
                }
            }
        }
        return weather_db.get(scenario, weather_db["kahramanmaras"])

    def get_building_risk_assessment(self, scenario="kahramanmaras"):
        """Bina hasar degerlendirmesi"""
        assessments = {
            "kahramanmaras": {
                "total_buildings_inspected": 218000,
                "damage_categories": {
                    "collapsed": {"count": 14014, "percentage": 6.4, "color": "#000000",
                                  "label": "Yikilmis", "action": "Arama kurtarma oncelikli"},
                    "heavily_damaged": {"count": 18786, "percentage": 8.6, "color": "#ff0000",
                                        "label": "Agir Hasarli", "action": "Girilmez - yikim karari"},
                    "moderately_damaged": {"count": 31212, "percentage": 14.3, "color": "#ff8c00",
                                           "label": "Orta Hasarli", "action": "Muhendis incelemesi gerekli"},
                    "slightly_damaged": {"count": 48651, "percentage": 22.3, "color": "#ffd700",
                                         "label": "Az Hasarli", "action": "Onarimla kullanilabilir"},
                    "undamaged": {"count": 105337, "percentage": 48.3, "color": "#28a745",
                                  "label": "Hasarsiz", "action": "Kullanima uygun"}
                },
                "urgent_rescue_sites": [
                    {"name": "Ebrar Sitesi", "lat": 37.5820, "lon": 36.9260,
                     "status": "cokmus", "estimated_trapped": 200, "priority": 1},
                    {"name": "Galeria Is Merkezi", "lat": 37.5870, "lon": 36.9350,
                     "status": "cokmus", "estimated_trapped": 50, "priority": 2},
                    {"name": "Reyhanoglu Apartmani", "lat": 37.5840, "lon": 36.9310,
                     "status": "cokmus", "estimated_trapped": 80, "priority": 1},
                    {"name": "Ismet Pasa Mah. Bloklar", "lat": 37.5900, "lon": 36.9400,
                     "status": "agir_hasar", "estimated_trapped": 30, "priority": 3}
                ],
                "source": "T.C. Cevre, Sehircilik ve Iklim Degisikligi Bakanligi"
            },
            "manavgat": {
                "total_buildings_inspected": 8500,
                "damage_categories": {
                    "collapsed": {"count": 58, "percentage": 0.7, "color": "#000000",
                                  "label": "Tamamen Yanmis", "action": "Girilmez"},
                    "heavily_damaged": {"count": 640, "percentage": 7.5, "color": "#ff0000",
                                        "label": "Agir Yangin Hasari", "action": "Yapisal kontrol gerekli"},
                    "moderately_damaged": {"count": 1200, "percentage": 14.1, "color": "#ff8c00",
                                           "label": "Kismi Hasar", "action": "Onarim gerekli"},
                    "slightly_damaged": {"count": 2100, "percentage": 24.7, "color": "#ffd700",
                                         "label": "Az Hasarli", "action": "Temizlik sonrasi kullanilabilir"},
                    "undamaged": {"count": 4502, "percentage": 53.0, "color": "#28a745",
                                  "label": "Hasarsiz", "action": "Kullanima uygun"}
                },
                "urgent_rescue_sites": [
                    {"name": "Manavgat Ovabasli Koyu", "lat": 36.8050, "lon": 31.4200,
                     "status": "yanmis", "estimated_trapped": 15, "priority": 1},
                    {"name": "Kalemler Koyu", "lat": 36.8200, "lon": 31.3800,
                     "status": "yanmis", "estimated_trapped": 8, "priority": 2},
                    {"name": "Sarilar Mahallesi", "lat": 36.7950, "lon": 31.4500,
                     "status": "tahliye", "estimated_trapped": 25, "priority": 1}
                ],
                "source": "Antalya Valiligi Afet Raporu"
            },
            "artvin": {
                "total_buildings_inspected": 3200,
                "damage_categories": {
                    "collapsed": {"count": 45, "percentage": 1.4, "color": "#000000",
                                  "label": "Yikilmis/Selde Yikilmis", "action": "Arama kurtarma"},
                    "heavily_damaged": {"count": 180, "percentage": 5.6, "color": "#ff0000",
                                        "label": "Agir Hasar (Sel/Heyelan)", "action": "Girilmez"},
                    "moderately_damaged": {"count": 420, "percentage": 13.1, "color": "#ff8c00",
                                           "label": "Orta Hasar", "action": "Muhendis incelemesi"},
                    "slightly_damaged": {"count": 680, "percentage": 21.3, "color": "#ffd700",
                                         "label": "Az Hasarli", "action": "Temizlik gerekli"},
                    "undamaged": {"count": 1875, "percentage": 58.6, "color": "#28a745",
                                  "label": "Hasarsiz", "action": "Kullanima uygun"}
                },
                "urgent_rescue_sites": [
                    {"name": "Arhavi Ilce Merkezi", "lat": 41.1750, "lon": 41.7900,
                     "status": "sel_baskini", "estimated_trapped": 30, "priority": 1},
                    {"name": "Findikli Sahil Yolu", "lat": 41.2500, "lon": 41.0200,
                     "status": "heyelan", "estimated_trapped": 12, "priority": 2},
                    {"name": "Artvin Merkez Dere Kenari", "lat": 41.1830, "lon": 41.8200,
                     "status": "sel_baskini", "estimated_trapped": 20, "priority": 1}
                ],
                "source": "Artvin Valiligi Afet Raporu"
            }
        }
        return assessments.get(scenario, assessments["kahramanmaras"])

    def get_rescue_resources(self, scenario="kahramanmaras"):
        """Kurtarma kaynaklari durumu"""
        return {
            "search_rescue_teams": [
                {"name": "AFAD Ulusal Tim", "personnel": 500, "status": "aktif", "location": "Sehir merkezi"},
                {"name": "AKUT", "personnel": 200, "status": "aktif", "location": "Dulkadiroglu"},
                {"name": "UMKE", "personnel": 150, "status": "aktif", "location": "Hastane cevresi"},
                {"name": "Jandarma JAK", "personnel": 300, "status": "aktif", "location": "Cevre ilceler"},
                {"name": "TSK Birlik", "personnel": 1000, "status": "aktif", "location": "Genis bolge"},
                {"name": "Uluslararasi Ekipler", "personnel": 8000, "status": "yolda",
                 "location": "Farkli ulkelerden geliyor"}
            ],
            "vehicles": {
                "ambulance": {"total": 85, "active": 60, "status": "yetersiz"},
                "fire_truck": {"total": 25, "active": 20, "status": "yeterli"},
                "crane": {"total": 40, "active": 30, "status": "yetersiz"},
                "excavator": {"total": 120, "active": 90, "status": "aktif"},
                "helicopter": {"total": 15, "active": 8, "status": "hava_durumu_sinirli"}
            },
            "supplies": {
                "tents": {"total": 50000, "distributed": 35000, "status": "ek_gerekli"},
                "blankets": {"total": 200000, "distributed": 150000, "status": "yeterli"},
                "food_packages": {"total": 500000, "distributed": 300000, "status": "aktif"},
                "water_liters": {"total": 2000000, "distributed": 1200000, "status": "ek_gerekli"},
                "medicine_kits": {"total": 10000, "distributed": 7000, "status": "kritik"}
            }
        }

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Iki koordinat arasi mesafe (km)"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
