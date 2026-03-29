# SafeRoute AI - Sunum Metni
## Afet Yonetiminde Yerli Uydu Verisi Entegrasyonu
### TUA Astro Hackathon 2026

---

## ACILIS (1 dakika)

Sayın jüri üyeleri, merhaba. Biz SafeRoute AI ekibi olarak, afet anında hayat kurtaracak bir sistem geliştirdik.

6 Şubat 2023'ü hepimiz hatırlıyoruz. Kahramanmaraş'ta 7.8 büyüklüğünde bir deprem meydana geldi. 50.000'den fazla insanımızı kaybettik. Kurtarma ekipleri saatlerce hangi yoldan gideceğini bilemedi. Hangi binalar çökmüş, hangi yollar kapanmış, nerede yangın çıkmış — bilgi yoktu.

**Peki ya uydu yukarıdan her şeyi görüyorsa?**

İşte SafeRoute AI tam olarak bunu yapıyor: Uydu görüntülerini yapay zeka ile analiz edip, kurtarma ekiplerine en güvenli rotayı çizen bir sistem.

---

## PROBLEM (1 dakika)

Afet anında 3 kritik sorun var:

1. **Bilgi eksikliği**: Hangi binalar çökmüş? Hangi yollar kullanılabilir? Nerede ikincil tehlike var?
2. **Zaman kaybı**: Kurtarma ekipleri yanlış yollardan gidiyor, kapalı yollarla karşılaşıyor, geri dönmek zorunda kalıyor.
3. **İkincil riskler**: Depremden sonra yangın çıkabilir, sel olabilir, bina çökebilir. Bunlar önceden tahmin edilemiyor.

Altın saatler diyoruz — ilk 72 saat. Bu sürede her dakika bir hayat demek. Ama mevcut sistemlerde uydu verisini analiz edip sahaya aktarmak **saatler hatta günler** alıyor.

---

## COZUM: SafeRoute AI (3 dakika)

SafeRoute AI, bu sorunu 5 katmanlı bir yapay zeka sistemiyle çözüyor:

### 1. Uydu Görüntüsü Analizi
- Sentinel-2 uydusundan **13 farklı spektral bantta** veri alıyoruz
- Sadece fotoğraf değil — kızılötesi, yakın kızılötesi, kısa dalga kızılötesi bantları
- Her piksel bir sayısal değer: bu değerlerden arazi türünü, hasarı, yangını, su baskınını tespit ediyoruz

### 2. Spektral İndeks Hesaplama
- **NDVI** (Bitki İndeksi): Deprem öncesi ve sonrasını karşılaştırıyoruz. NDVI düşen yerler = bina çökmüş, enkaz oluşmuş
- **NBR / dNBR** (Yangın İndeksi): Kızılötesi bantlardan yangın tespiti ve şiddet sınıflandırması
- **NDWI** (Su İndeksi): Sel baskın alanlarının tespiti
- **NDBI** (Bina İndeksi): Yapılaşma alanlarının ve hasarın belirlenmesi

### 3. Çok Katmanlı Risk Haritası
Tek bir risk değeri yetmez. Biz 5 katmanlı analiz yapıyoruz:
- Arazi riski (bina, orman, su, endüstriyel alan)
- Afet bölgesi riski (çökme, yangın, sel alanları)
- İkincil risk (depremden sonra benzin istasyonu patlama riski, orman yangın riski)
- Yakınlık riski (tehlikeli nesnelere mesafe)
- Erişilebilirlik (geçiş zorluğu)

### 4. Akıllı Rota Planlama
- **A* algoritması** ile en güvenli rotayı hesaplıyoruz
- Risk ağırlıklı maliyet fonksiyonu: sadece en kısa yol değil, en güvenli yol
- **OSRM** ile gerçek yol ağı üzerinden rota
- Alternatif rotalar sunuyoruz
- Adım adım navigasyon talimatları: "Dikkat! Sağınızda çökmüş bina, soldan devam edin"

### 5. Acil Durum Entegrasyonu
- En yakın hastaneler (kapasite, helipad bilgisi)
- AFAD toplanma alanları
- Artçı sarsıntı risk bölgeleri
- Hava durumu ve kurtarma etkisi
- Bina hasar değerlendirmesi
- Kurtarma kaynakları durumu (ambulans, helikopter, ekip sayısı)

---

## DEMO (2 dakika)

*(Ekranda sistemi gösterin)*

Şu an ekranda Kahramanmaraş'ın gerçek haritasını görüyorsunuz.

1. "Tam Analiz Başlat" butonuna basıyorum...
2. Sistem Sentinel-2 uydu verisini analiz ediyor...
3. Spektral indeksler hesaplanıyor — NDVI değişimi bina çökmelerini gösteriyor...
4. Risk haritası oluşturuldu — kırmızı alanlar yüksek tehlike...
5. En güvenli rota hesaplandı — mavi çizgi gerçek yolları takip ediyor...

Sağ panelde görüyorsunuz:
- **Güvenlik skoru: %57** — rota orta düzey risk içeriyor
- **Hava durumu: -3°C, kar yağışlı** — hipotermi riski var
- **218.000 bina incelenmiş** — 14.014'ü yıkılmış
- **Ebrar Sitesi'nde 200 kişi mahsur** — öncelik 1

Şimdi Artvin Sel Felaketi'ni seçiyorum... Bakın, sistem otomatik olarak:
- Artvin'in kendi hastanelerine rota çiziyor
- Hava durumu "Yoğun Yağmurlu, 22°C" olarak güncellendi
- "Helikopter operasyonları imkansız" uyarısı veriyor
- Dere yataklarından uzak rota öneriyor

---

## TEKNIK ALTYAPI (1 dakika)

- **Backend**: Python, Flask, OpenCV, NumPy, SciPy
- **Uydu Verisi**: Sentinel-2 MSI (10m çözünürlük, 13 bant)
- **Rota Motoru**: A* algoritması + OSRM gerçek yol ağı
- **Harita**: Leaflet.js + OpenStreetMap
- **Risk Analizi**: 5 katmanlı Gaussian ağırlıklı risk modeli
- **Veri Kaynakları**: Copernicus, NASA Earthdata, AFAD, Kandilli

Sistem tamamen **açık kaynak** ve **ücretsiz** veri kaynakları kullanıyor. Herhangi bir ücretli API'ye bağımlılık yok.

---

## FARK YARATAN OZELLIKLER (1 dakika)

Rakiplerimizden farkımız:

1. **Sadece harita değil, akıllı analiz**: Uydu verisinden otomatik tehlike tespiti
2. **İkincil risk analizi**: Depremden sonra yangın, sel, patlama risklerini de hesaplıyor
3. **Gerçek yollar**: Kuş uçuşu değil, sokak sokak rota
4. **Çoklu senaryo**: Deprem, yangın, sel, heyelan — her afete uyum sağlıyor
5. **Türk uydu entegrasyonu**: Göktürk-1/2 verileriyle entegrasyona hazır
6. **Anlık karar desteği**: Hava durumu, hipotermi süresi, helikopter durumu gibi kritik bilgiler

---

## GELECEK VIZYONU (30 saniye)

- Göktürk-1 ve Göktürk-2 uydu verisiyle entegrasyon (GEZGIN platformu)
- Gerçek zamanlı uydu akışı ile canlı güncelleme
- Drone entegrasyonu ile düşük irtifa görüntüleme
- Mobil uygulama ile sahada kullanım
- AFAD sistemleriyle doğrudan entegrasyon
- Yapay zeka modeli eğitimi ile otomatik bina hasar sınıflandırması

---

## KAPANI (30 saniye)

6 Şubat depreminde 50.000 canımızı kaybettik. SafeRoute AI, bir sonraki afette **her dakikayı** değerli kılmak için tasarlandı.

Uydu yukarıdan görüyor. Yapay zeka analiz ediyor. Sistem en güvenli yolu çiziyor.

**Çünkü afette kaybedilen her dakika, kaybedilen bir hayat demek.**

Teşekkür ederiz.

---

## OLASI JURI SORULARI VE CEVAPLARI

**S: Gerçek zamanlı uydu verisi nasıl alacaksınız?**
C: Sentinel-2 her 5 günde bir geçiyor. Acil durumlarda Copernicus EMS aktivasyonu ile saatler içinde görüntü alınabiliyor. Göktürk-2 ile bu süre daha da kısalabilir.

**S: OSRM routing afet sonrası yıkılmış yolları nasıl bilecek?**
C: Uydu analizi ile tespit edilen hasarlı yollar, rota hesaplamasında yüksek risk bölgesi olarak işaretleniyor. Sistem bu yollardan kaçınıyor.

**S: Neden Sentinel-2, neden Göktürk değil?**
C: Sentinel-2 ücretsiz ve açık erişimli, 13 spektral bant sunuyor. Göktürk daha yüksek çözünürlüklü ama erişimi kısıtlı. Sistemimiz her ikisiyle de çalışabilecek şekilde tasarlandı.

**S: Bu sistemin AFAD ile entegrasyonu nasıl olur?**
C: AFAD'ın deprem API'si zaten açık. Toplanma alanları ve acil durum verileri entegre edildi. İleri aşamada AFAD'ın iç sistemleriyle doğrudan veri alışverişi yapılabilir.

**S: Makine öğrenimi modeli var mı?**
C: Şu an spektral indeks tabanlı eşikleme yöntemi kullanıyoruz. Bu, şeffaf ve açıklanabilir bir yöntem. İleri aşamada CNN tabanlı hasar sınıflandırma modeli eğitmeyi planlıyoruz.

**S: Nüfus verisi nereden?**
C: TÜİK açık veri portalından ilçe bazlı nüfus verileri. Kurtarma önceliği için nüfus yoğunluğu kritik bir parametre.
