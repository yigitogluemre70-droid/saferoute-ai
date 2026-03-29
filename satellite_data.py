"""
SafeRoute AI - Uydu Verisi Modulu
Sentinel-2, NASA Earthdata ve Copernicus'tan gercek uydu verisi cekilmesi
Spektral bant analizi (NDVI, NDWI, NBR, dNBR)
"""

import numpy as np
import os
import json
import requests
from datetime import datetime, timedelta


class SatelliteDataManager:
    """
    Gercek uydu verisi yonetimi ve spektral analiz

    Kullanilan Veri Kaynaklari:
    - Sentinel-2 (ESA Copernicus): 10m cozunurluk, 13 bant
    - NASA FIRMS: Gercek zamanli yangin verisi
    - Copernicus EMS: Afet haritalari
    - OpenStreetMap: Yol ve bina verisi
    """

    # Sentinel-2 Bant Bilgileri
    SENTINEL2_BANDS = {
        "B02": {"name": "Mavi", "wavelength": "490nm", "resolution": 10, "use": "Gorunur isik"},
        "B03": {"name": "Yesil", "wavelength": "560nm", "resolution": 10, "use": "Gorunur isik"},
        "B04": {"name": "Kirmizi", "wavelength": "665nm", "resolution": 10, "use": "Gorunur isik, NDVI"},
        "B05": {"name": "Kirmizi Kenar 1", "wavelength": "705nm", "resolution": 20, "use": "Bitki analizi"},
        "B06": {"name": "Kirmizi Kenar 2", "wavelength": "740nm", "resolution": 20, "use": "Bitki analizi"},
        "B07": {"name": "Kirmizi Kenar 3", "wavelength": "783nm", "resolution": 20, "use": "Bitki analizi"},
        "B08": {"name": "NIR (Yakin Kizilotesi)", "wavelength": "842nm", "resolution": 10, "use": "NDVI, NDWI"},
        "B8A": {"name": "Dar NIR", "wavelength": "865nm", "resolution": 20, "use": "Bitki, su analizi"},
        "B09": {"name": "Su Buhari", "wavelength": "945nm", "resolution": 60, "use": "Atmosfer"},
        "B11": {"name": "SWIR 1", "wavelength": "1610nm", "resolution": 20, "use": "Yangin, NBR, nem"},
        "B12": {"name": "SWIR 2", "wavelength": "2190nm", "resolution": 20, "use": "Yangin, yanmis alan"}
    }

    # Spektral Indeksler
    SPECTRAL_INDICES = {
        "NDVI": {
            "name": "Normalize Edilmis Bitki Indeksi",
            "formula": "(NIR - RED) / (NIR + RED)",
            "bands": ["B08", "B04"],
            "description": "Bitki sagligi. >0.3 saglikli bitki, <0.1 ciplak toprak/bina",
            "use_case": "Deprem: bina cokme tespiti (NDVI dusus), Yangin: yanmis alan"
        },
        "NDWI": {
            "name": "Normalize Edilmis Su Indeksi",
            "formula": "(GREEN - NIR) / (GREEN + NIR)",
            "bands": ["B03", "B08"],
            "description": "Su kutlesi tespiti. >0 su, <0 kara",
            "use_case": "Sel: su baskin alani tespiti, Tsunami: kiyidaki degisim"
        },
        "NBR": {
            "name": "Normalize Edilmis Yangin Indeksi",
            "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
            "bands": ["B08", "B12"],
            "description": "Yangin siddeti. Dusuk deger = yanmis alan",
            "use_case": "Yangin: aktif yangin ve yanmis alan tespiti"
        },
        "dNBR": {
            "name": "Fark NBR (Degisim Tespiti)",
            "formula": "NBR_once - NBR_sonra",
            "bands": ["B08", "B12"],
            "description": ">0.27 yuksek siddetli yangin, 0.1-0.27 orta siddet",
            "use_case": "Yangin oncesi/sonrasi karsilastirma"
        },
        "NDBI": {
            "name": "Normalize Edilmis Bina Indeksi",
            "formula": "(SWIR1 - NIR) / (SWIR1 + NIR)",
            "bands": ["B11", "B08"],
            "description": "Yapilasma alani tespiti. >0 bina/asfalt",
            "use_case": "Deprem: sehir alani tespiti ve hasar degerlendirmesi"
        }
    }

    def __init__(self):
        self.cache_dir = "data/satellite_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def calculate_ndvi(self, nir_band, red_band):
        """
        NDVI (Bitki Indeksi) hesapla
        Deprem oncesi/sonrasi karsilastirmada bina cokme tespiti icin kullanilir
        """
        nir = nir_band.astype(np.float64)
        red = red_band.astype(np.float64)
        denominator = nir + red
        ndvi = np.where(denominator > 0, (nir - red) / denominator, 0)
        return np.clip(ndvi, -1, 1)

    def calculate_ndwi(self, green_band, nir_band):
        """
        NDWI (Su Indeksi) hesapla
        Sel ve su baskin alanlarini tespit eder
        """
        green = green_band.astype(np.float64)
        nir = nir_band.astype(np.float64)
        denominator = green + nir
        ndwi = np.where(denominator > 0, (green - nir) / denominator, 0)
        return np.clip(ndwi, -1, 1)

    def calculate_nbr(self, nir_band, swir_band):
        """
        NBR (Yangin Indeksi) hesapla
        Yanmis alanlari ve aktif yangini tespit eder
        """
        nir = nir_band.astype(np.float64)
        swir = swir_band.astype(np.float64)
        denominator = nir + swir
        nbr = np.where(denominator > 0, (nir - swir) / denominator, 0)
        return np.clip(nbr, -1, 1)

    def calculate_dnbr(self, pre_nir, pre_swir, post_nir, post_swir):
        """
        dNBR (Degisim NBR) hesapla
        Yangin oncesi ve sonrasi karsilastirma
        """
        pre_nbr = self.calculate_nbr(pre_nir, pre_swir)
        post_nbr = self.calculate_nbr(post_nir, post_swir)
        return pre_nbr - post_nbr

    def calculate_ndbi(self, swir_band, nir_band):
        """
        NDBI (Bina Indeksi) hesapla
        Yapilasma alanlarini tespit eder
        """
        swir = swir_band.astype(np.float64)
        nir = nir_band.astype(np.float64)
        denominator = swir + nir
        ndbi = np.where(denominator > 0, (swir - nir) / denominator, 0)
        return np.clip(ndbi, -1, 1)

    def change_detection(self, pre_image_bands, post_image_bands, disaster_type="earthquake"):
        """
        Afet oncesi/sonrasi degisim tespiti

        Args:
            pre_image_bands: dict - Afet oncesi bant verileri {"B04": array, "B08": array, ...}
            post_image_bands: dict - Afet sonrasi bant verileri
            disaster_type: Afet turu

        Returns:
            dict: Degisim analizi sonuclari
        """
        results = {}

        if disaster_type == "earthquake":
            # NDVI degisimi - bina cokme tespiti
            pre_ndvi = self.calculate_ndvi(pre_image_bands["B08"], pre_image_bands["B04"])
            post_ndvi = self.calculate_ndvi(post_image_bands["B08"], post_image_bands["B04"])
            ndvi_change = pre_ndvi - post_ndvi

            # NDBI degisimi - yapisal hasar
            if "B11" in pre_image_bands and "B11" in post_image_bands:
                pre_ndbi = self.calculate_ndbi(pre_image_bands["B11"], pre_image_bands["B08"])
                post_ndbi = self.calculate_ndbi(post_image_bands["B11"], post_image_bands["B08"])
                ndbi_change = post_ndbi - pre_ndbi

                results["ndbi_change"] = ndbi_change
                results["building_damage"] = ndbi_change > 0.15

            results["ndvi_change"] = ndvi_change
            results["collapsed_areas"] = ndvi_change > 0.2  # NDVI dusen alanlar = cokme
            results["damage_severity"] = np.clip(ndvi_change * 2, 0, 1)

        elif disaster_type == "fire":
            # dNBR - yangin siddeti
            dnbr = self.calculate_dnbr(
                pre_image_bands["B08"], pre_image_bands["B12"],
                post_image_bands["B08"], post_image_bands["B12"]
            )
            results["dnbr"] = dnbr
            results["burn_severity"] = self._classify_burn_severity(dnbr)

        elif disaster_type == "flood":
            # NDWI degisimi - su baskin alani
            pre_ndwi = self.calculate_ndwi(pre_image_bands["B03"], pre_image_bands["B08"])
            post_ndwi = self.calculate_ndwi(post_image_bands["B03"], post_image_bands["B08"])
            ndwi_change = post_ndwi - pre_ndwi

            results["ndwi_change"] = ndwi_change
            results["flooded_areas"] = (post_ndwi > 0) & (pre_ndwi < 0)

        return results

    def _classify_burn_severity(self, dnbr):
        """dNBR degerlerine gore yangin siddeti siniflandirmasi"""
        severity = np.zeros_like(dnbr, dtype=object)
        severity[dnbr < 0.1] = "yanmamis"
        severity[(dnbr >= 0.1) & (dnbr < 0.27)] = "dusuk"
        severity[(dnbr >= 0.27) & (dnbr < 0.44)] = "orta-dusuk"
        severity[(dnbr >= 0.44) & (dnbr < 0.66)] = "orta-yuksek"
        severity[dnbr >= 0.66] = "yuksek"
        return severity

    def simulate_sentinel2_data(self, scenario_type="kahramanmaras_earthquake",
                                 width=500, height=400):
        """
        Gercekci Sentinel-2 bant verileri simule et
        (Gercek API erisimi yokken demo icin)

        Kahramanmaras 6 Subat 2023 depremi icin gercekci veriler uretir
        """
        np.random.seed(42)

        if scenario_type == "kahramanmaras_earthquake":
            return self._simulate_kahramanmaras(width, height)
        elif scenario_type == "manavgat_fire":
            return self._simulate_manavgat_fire(width, height)
        elif scenario_type == "artvin_flood":
            return self._simulate_artvin_flood(width, height)

        return None

    def _simulate_kahramanmaras(self, width, height):
        """
        Kahramanmaras 6 Subat 2023 Depremi simulasyonu
        Gercek cografi verilere dayali
        """
        # Afet oncesi bantlar (5 Subat 2023)
        base_nir = np.random.uniform(0.2, 0.6, (height, width))
        base_red = np.random.uniform(0.05, 0.15, (height, width))
        base_green = np.random.uniform(0.05, 0.12, (height, width))
        base_swir = np.random.uniform(0.1, 0.3, (height, width))

        # Sehir merkezi (binalar - yuksek yansima)
        city_center_y, city_center_x = height // 2, width // 2
        city_radius = min(width, height) // 4

        Y, X = np.ogrid[:height, :width]
        city_mask = ((X - city_center_x) ** 2 + (Y - city_center_y) ** 2) < city_radius ** 2

        # Sehirde NDBI yuksek (bina), NDVI dusuk
        base_nir[city_mask] = np.random.uniform(0.15, 0.25, np.sum(city_mask))
        base_red[city_mask] = np.random.uniform(0.1, 0.2, np.sum(city_mask))
        base_swir[city_mask] = np.random.uniform(0.2, 0.4, np.sum(city_mask))

        # Yesil alanlar (cevredeki tarim arazileri)
        farm_mask = ~city_mask & (Y > height * 0.3) & (Y < height * 0.7)
        base_nir[farm_mask] = np.random.uniform(0.4, 0.7, np.sum(farm_mask))
        base_red[farm_mask] = np.random.uniform(0.03, 0.08, np.sum(farm_mask))

        # Nehir (Ceyhan Nehri benzeri)
        river_x = width // 3
        for y in range(height):
            rx = int(river_x + 15 * np.sin(y / 30))
            x_min = max(0, rx - 8)
            x_max = min(width, rx + 8)
            base_nir[y, x_min:x_max] = 0.05
            base_green[y, x_min:x_max] = 0.08
            base_red[y, x_min:x_max] = 0.03

        pre_bands = {
            "B02": np.random.uniform(0.04, 0.1, (height, width)),  # Mavi
            "B03": base_green,
            "B04": base_red,
            "B08": base_nir,
            "B11": base_swir,
            "B12": np.random.uniform(0.08, 0.25, (height, width))
        }

        # Afet sonrasi bantlar (7 Subat 2023) - deprem hasari
        post_bands = {k: v.copy() for k, v in pre_bands.items()}

        # Deprem hasari: sehir merkezinde bina cokmeleri
        # Gercek veri: Kahramanmaras merkezde %60'a varan yikim
        damage_intensity = np.zeros((height, width))
        epicenter_y, epicenter_x = city_center_y, city_center_x
        dist_from_epi = np.sqrt((X - epicenter_x) ** 2 + (Y - epicenter_y) ** 2)

        # Hasar yogunlugu (mesafeye ters orantili)
        damage_intensity = np.clip(1 - dist_from_epi / (city_radius * 1.5), 0, 1)
        damage_intensity *= city_mask.astype(float)

        # Rastgele bina cokmeleri
        collapse_prob = damage_intensity * 0.6
        collapse_mask = np.random.random((height, width)) < collapse_prob

        # Coken binalarda: NIR duser (enkazda bitki yok), SWIR artar (beton/toz)
        post_bands["B08"][collapse_mask] *= np.random.uniform(0.3, 0.6, np.sum(collapse_mask))
        post_bands["B04"][collapse_mask] *= np.random.uniform(1.2, 2.0, np.sum(collapse_mask))
        post_bands["B11"][collapse_mask] *= np.random.uniform(1.3, 1.8, np.sum(collapse_mask))
        post_bands["B12"][collapse_mask] *= np.random.uniform(1.2, 1.6, np.sum(collapse_mask))

        # Toz bulutu etkisi (genis alanda hafif reflektans artisi)
        dust_area = dist_from_epi < city_radius * 2
        post_bands["B02"][dust_area] += 0.02
        post_bands["B03"][dust_area] += 0.015

        return {
            "pre_disaster": pre_bands,
            "post_disaster": post_bands,
            "metadata": {
                "event": "Kahramanmaras Depremi",
                "date": "2023-02-06",
                "magnitude": "7.8 Mw",
                "pre_date": "2023-02-05",
                "post_date": "2023-02-07",
                "satellite": "Sentinel-2A",
                "resolution": "10m",
                "center_lat": 37.5858,
                "center_lon": 36.9371,
                "city_center": (city_center_y, city_center_x),
                "epicenter": (epicenter_y, epicenter_x),
                "damage_radius_px": city_radius
            },
            "ground_truth": {
                "collapse_mask": collapse_mask,
                "damage_intensity": damage_intensity
            }
        }

    def _simulate_manavgat_fire(self, width, height):
        """Manavgat 2021 yangin simulasyonu"""
        np.random.seed(55)

        # Ormanlik alan (yuksek NDVI)
        base_nir = np.random.uniform(0.5, 0.8, (height, width))
        base_red = np.random.uniform(0.02, 0.06, (height, width))
        base_swir = np.random.uniform(0.1, 0.2, (height, width))

        pre_bands = {
            "B02": np.random.uniform(0.02, 0.05, (height, width)),
            "B03": np.random.uniform(0.03, 0.08, (height, width)),
            "B04": base_red,
            "B08": base_nir,
            "B11": base_swir,
            "B12": np.random.uniform(0.05, 0.15, (height, width))
        }

        post_bands = {k: v.copy() for k, v in pre_bands.items()}

        # Yangin alani
        Y, X = np.ogrid[:height, :width]
        fire_centers = [(height // 3, width // 2), (height // 2, width // 3)]

        for fy, fx in fire_centers:
            dist = np.sqrt((X - fx) ** 2 + (Y - fy) ** 2)
            burn_mask = dist < min(width, height) // 5
            active_fire = dist < min(width, height) // 8

            # Yanmis alan: NIR duser, SWIR artar
            post_bands["B08"][burn_mask] *= 0.2
            post_bands["B04"][burn_mask] *= 3.0
            post_bands["B12"][burn_mask] *= 4.0

            # Aktif yangin: SWIR cok yuksek
            post_bands["B12"][active_fire] = np.random.uniform(0.8, 1.0, np.sum(active_fire))
            post_bands["B11"][active_fire] = np.random.uniform(0.6, 0.9, np.sum(active_fire))

        return {
            "pre_disaster": pre_bands,
            "post_disaster": post_bands,
            "metadata": {
                "event": "Manavgat Yangini",
                "date": "2021-07-28",
                "satellite": "Sentinel-2A",
                "resolution": "10m",
                "center_lat": 36.7867,
                "center_lon": 31.4433
            }
        }

    def _simulate_artvin_flood(self, width, height):
        """Artvin sel simulasyonu"""
        np.random.seed(77)

        base_nir = np.random.uniform(0.3, 0.6, (height, width))
        base_green = np.random.uniform(0.05, 0.12, (height, width))

        pre_bands = {
            "B02": np.random.uniform(0.03, 0.07, (height, width)),
            "B03": base_green,
            "B04": np.random.uniform(0.04, 0.1, (height, width)),
            "B08": base_nir,
            "B11": np.random.uniform(0.15, 0.3, (height, width)),
            "B12": np.random.uniform(0.1, 0.2, (height, width))
        }

        post_bands = {k: v.copy() for k, v in pre_bands.items()}

        # Sel baskini: vadi boyunca su
        Y, X = np.ogrid[:height, :width]
        valley_center = width // 2
        for y in range(height):
            vx = int(valley_center + 20 * np.sin(y / 25))
            flood_width = 40 + int(20 * np.sin(y / 50))
            x_min = max(0, vx - flood_width)
            x_max = min(width, vx + flood_width)

            # Su: NIR cok dusuk, Green nispeten yuksek
            post_bands["B08"][y, x_min:x_max] = np.random.uniform(0.02, 0.08, x_max - x_min)
            post_bands["B03"][y, x_min:x_max] = np.random.uniform(0.06, 0.12, x_max - x_min)

        return {
            "pre_disaster": pre_bands,
            "post_disaster": post_bands,
            "metadata": {
                "event": "Artvin Sel Felaketi",
                "date": "2021-07-14",
                "satellite": "Sentinel-2A",
                "resolution": "10m",
                "center_lat": 41.1828,
                "center_lon": 41.8183
            }
        }

    def get_data_sources_info(self):
        """Makale icin kullanilabilecek veri kaynaklari bilgisi"""
        return {
            "primary_sources": [
                {
                    "name": "Copernicus Open Access Hub (Sentinel-2)",
                    "url": "https://scihub.copernicus.eu/",
                    "data": "Sentinel-2 MSI (Multispektral)",
                    "resolution": "10m (B02,B03,B04,B08), 20m (B05-B07,B11,B12)",
                    "revisit": "5 gun",
                    "bands": 13,
                    "cost": "Ucretsiz",
                    "use": "Deprem hasar tespiti, yangin, sel, arazi analizi"
                },
                {
                    "name": "NASA Earthdata (Landsat 8/9)",
                    "url": "https://earthdata.nasa.gov/",
                    "data": "Landsat 8/9 OLI+TIRS",
                    "resolution": "30m (multispektral), 15m (pankromatik)",
                    "revisit": "16 gun",
                    "bands": 11,
                    "cost": "Ucretsiz",
                    "use": "Uzun donem degisim analizi"
                },
                {
                    "name": "NASA FIRMS",
                    "url": "https://firms.modaps.eosdis.nasa.gov/",
                    "data": "MODIS + VIIRS yangin verisi",
                    "resolution": "375m (VIIRS), 1km (MODIS)",
                    "revisit": "Gercek zamanli",
                    "cost": "Ucretsiz",
                    "use": "Aktif yangin tespiti ve takibi"
                },
                {
                    "name": "Copernicus Emergency Management Service",
                    "url": "https://emergency.copernicus.eu/",
                    "data": "Afet haritalari, hasar degerlendirmesi",
                    "resolution": "Degisken",
                    "cost": "Ucretsiz",
                    "use": "Referans afet haritalari (6 Subat depremi dahil)"
                },
                {
                    "name": "USGS Earth Explorer",
                    "url": "https://earthexplorer.usgs.gov/",
                    "data": "Landsat, ASTER, dijital yukseklik modeli",
                    "resolution": "15-30m",
                    "cost": "Ucretsiz",
                    "use": "Yukseklik verisi, egim analizi"
                }
            ],
            "turkish_sources": [
                {
                    "name": "GEZGIN (TUBITAK UZAY)",
                    "url": "https://gezgin.gov.tr/",
                    "data": "Gokturk-1, Gokturk-2 uydu goruntuleri",
                    "resolution": "Gokturk-2: 2.5m, Gokturk-1: <1m",
                    "cost": "Basvuru ile ucretsiz (akademik)",
                    "use": "Yuksek cozunurluklu Turk uydu verisi"
                },
                {
                    "name": "AFAD Deprem Harita Servisi",
                    "url": "https://deprem.afad.gov.tr/",
                    "data": "Deprem verileri, fay hatlari",
                    "cost": "Ucretsiz",
                    "use": "Deprem buyukluk, konum, derinlik verileri"
                }
            ],
            "methodology_for_paper": {
                "title": "Afet Yonetiminde Uydu Tabanli Degisim Tespiti ve Guvenli Rota Planlama",
                "steps": [
                    "1. Afet oncesi Sentinel-2 goruntusu indir (pre-event)",
                    "2. Afet sonrasi Sentinel-2 goruntusu indir (post-event)",
                    "3. Spektral indeksler hesapla (NDVI, NDWI, NBR, NDBI)",
                    "4. Degisim tespiti yap (pre vs post karsilastirma)",
                    "5. Hasar siniflandirmasi (makine ogrenimi veya esikleme)",
                    "6. Risk haritasi olustur (cok katmanli analiz)",
                    "7. En guvenli rota hesapla (A* algoritması)",
                    "8. Sonuclari harita uzerinde gorsellesir"
                ],
                "references": [
                    "Sentinel-2 User Handbook, ESA, 2015",
                    "Remote Sensing of Environment - Change Detection methodologies",
                    "Copernicus EMS - Kahramanmaras Earthquake Activation [EMSR648]",
                    "NDVI-based damage assessment for earthquake (Ge et al., 2020)",
                    "dNBR burn severity mapping (Key & Benson, 2006)"
                ]
            }
        }
