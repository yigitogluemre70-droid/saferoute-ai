const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "B0B0B0" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };
const TW = 9360; // table width (US Letter 1" margins)

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 28, color: "1B3A5C" })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 24, color: "2563EB" })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 22, color: "1E40AF" })] });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120, line: 276 }, alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: "Arial", size: 21, ...opts })] });
}
function pb(label, value) {
  return new Paragraph({ spacing: { after: 80, line: 276 },
    children: [
      new TextRun({ text: label + ": ", font: "Arial", size: 21, bold: true }),
      new TextRun({ text: value, font: "Arial", size: 21 })
    ]});
}
function bullet(text, ref = "bullets") {
  return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 276 },
    children: [new TextRun({ text, font: "Arial", size: 21 })] });
}
function numberedItem(text) {
  return new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 60, line: 276 },
    children: [new TextRun({ text, font: "Arial", size: 21 })] });
}
function cell(text, opts = {}) {
  return new TableCell({
    borders, margins: cellMargins,
    width: { size: opts.width || 4680, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, bold: !!opts.bold, color: opts.color || "000000" })] })]
  });
}
function headerCell(text, w) {
  return cell(text, { bold: true, shading: "1B3A5C", color: "FFFFFF", width: w });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: "1B3A5C" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "2563EB" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "1E40AF" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [
    // ===== KAPAK =====
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      children: [
        new Paragraph({ spacing: { before: 2400 } }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
          children: [new TextRun({ text: "TUA ASTRO HACKATHON 2026", font: "Arial", size: 24, color: "64748B", bold: true })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
          children: [new TextRun({ text: "Bolgesel Konumlama ve Zamanlama Sistemi (BKZS)", font: "Arial", size: 20, color: "94A3B8" })] }),
        new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "0EA5E9", space: 1 } },
          children: [] }),
        new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "SafeRoute AI", font: "Arial", size: 52, bold: true, color: "0F172A" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: "Afet Yonetiminde Yerli Uydu Verisi Entegrasyonu", font: "Arial", size: 26, color: "334155" })] }),
        new Paragraph({ spacing: { before: 200 }, alignment: AlignmentType.CENTER,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "0EA5E9", space: 1 } },
          children: [] }),
        new Paragraph({ spacing: { before: 600 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "TEKNIK RAPOR", font: "Arial", size: 28, bold: true, color: "1E293B" })] }),
        new Paragraph({ spacing: { before: 600 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Mart 2026", font: "Arial", size: 22, color: "64748B" })] }),
        new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Versiyon 1.0", font: "Arial", size: 20, color: "94A3B8" })] }),
      ]
    },
    // ===== ICERIK + TOC =====
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      headers: {
        default: new Header({ children: [
          new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "CBD5E1", space: 4 } },
            children: [
              new TextRun({ text: "SafeRoute AI - Teknik Rapor", font: "Arial", size: 16, color: "94A3B8", italics: true })
            ]})
        ]})
      },
      footers: {
        default: new Footer({ children: [
          new Paragraph({ alignment: AlignmentType.CENTER, border: { top: { style: BorderStyle.SINGLE, size: 1, color: "CBD5E1", space: 4 } },
            children: [
              new TextRun({ text: "Sayfa ", font: "Arial", size: 16, color: "94A3B8" }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "94A3B8" })
            ]})
        ]})
      },
      children: [
        new TableOfContents("ICINDEKILER", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ children: [new PageBreak()] }),

        // 1. YONETICI OZETI
        h1("1. YONETICI OZETI"),
        p("SafeRoute AI, afet aninda uydu goruntulerine yapay zeka ile analiz edip kurtarma ekiplerine en guvenli rotayi cizen bir sistemdir. Sistem, Sentinel-2 uydusundan alinan cok bantli spektral verilerle arazi analizi yapar, afet bolgelerini tespit eder, cok katmanli risk haritasi olusturur ve A* algoritmasi ile gercek yol agi uzerinden en guvenli rotayi hesaplar."),
        p("6 Subat 2023 Kahramanmaras depremi gibi buyuk afetlerde, kurtarma ekiplerinin sahadaki tehlikeleri bilmeden hareket etmesi hem zaman kaybi hem de ek can kaybi riski olusturmaktadir. SafeRoute AI bu sorunu cozerek, afet sonrasi ilk 72 saatte (altin saatler) kurtarma operasyonlarinin etkinligini artirmayi hedeflemektedir."),
        p("Sistem tamamen acik kaynak ve ucretsiz veri kaynaklari (Copernicus Sentinel-2, NASA Earthdata, OpenStreetMap) kullanmakta olup, Turkiye'nin yerli uydu verileri (Gokturk-1/2) ile entegrasyona hazir mimaridedir."),

        new Paragraph({ children: [new PageBreak()] }),

        // 2. PROBLEM TANIMI
        h1("2. PROBLEM TANIMI"),
        h2("2.1. Mevcut Durum"),
        p("Turkiye, cografi konumu itibariyla deprem, sel, heyelan ve orman yangini gibi dogal afetlere siklikla maruz kalmaktadir. Ozellikle deprem acisindan Kuzey Anadolu Fay Hatti ve Dogu Anadolu Fay Hatti uzerinde bulunan ulkemiz, yuksek sismik aktiviteye sahiptir."),
        p("6 Subat 2023 tarihinde meydana gelen Mw 7.8 buyuklugundeki Kahramanmaras depremi, 11 ili etkileyen ve 50.000'den fazla vatandasimizin hayatini kaybettigi buyuk bir felaket olmustur. Bu depremde yasanan en kritik sorunlardan biri, kurtarma ekiplerinin sahada yeterli bilgiye sahip olmadan hareket etmek zorunda kalmasidir."),

        h2("2.2. Tanimlanan Sorunlar"),
        numberedItem("Bilgi Eksikligi: Afet sonrasi hangi binalarin coktugu, hangi yollarin kullanilabilir oldugu ve nerede ikincil tehlikelerin bulundugu hizli bir sekilde belirlenememektedir."),
        numberedItem("Zaman Kaybi: Kurtarma ekipleri kapali yollarla karsilasildiginda geri donmek zorunda kalmakta, bu da altin saatlerde kritik zaman kaybina neden olmaktadir."),
        numberedItem("Ikincil Risk Korlugu: Deprem sonrasi gaz sizintisi, yangin, sel gibi ikincil tehlikeler onceden tahmin edilememekte ve ek can kayiplarina yol acmaktadir."),
        numberedItem("Uydu Verisinin Gecikme ile Kullanilmasi: Mevcut sistemlerde uydu goruntulerinin analiz edilip sahaya aktarilmasi saatler hatta gunler alabilmektedir."),

        h2("2.3. Hedef"),
        p("SafeRoute AI, uydu goruntulerine yapay zeka tabanli analiz uygulayarak afet sonrasi sahada gercek zamanli karar destegi saglayan, kurtarma ekiplerine en guvenli rotayi gosteren ve ikincil riskleri onceden tespit eden entegre bir sistem gelistirmeyi hedeflemektedir."),

        new Paragraph({ children: [new PageBreak()] }),

        // 3. METODOLOJI
        h1("3. METODOLOJI"),
        h2("3.1. Veri Kaynaklari"),
        p("Sistemde kullanilan temel veri kaynaklari asagida listelenmiistir:"),

        new Table({
          width: { size: TW, type: WidthType.DXA },
          columnWidths: [2200, 2200, 1600, 1600, 1760],
          rows: [
            new TableRow({ children: [
              headerCell("Veri Kaynagi", 2200), headerCell("Veri Turu", 2200),
              headerCell("Cozunurluk", 1600), headerCell("Revisit", 1600), headerCell("Maliyet", 1760)
            ]}),
            new TableRow({ children: [
              cell("Sentinel-2 (ESA)", {width:2200}), cell("Multispektral (13 bant)", {width:2200}),
              cell("10m", {width:1600}), cell("5 gun", {width:1600}), cell("Ucretsiz", {width:1760})
            ]}),
            new TableRow({ children: [
              cell("Landsat 8/9 (NASA)", {width:2200}), cell("Multispektral (11 bant)", {width:2200}),
              cell("30m", {width:1600}), cell("16 gun", {width:1600}), cell("Ucretsiz", {width:1760})
            ]}),
            new TableRow({ children: [
              cell("NASA FIRMS", {width:2200}), cell("Yangin (termal)", {width:2200}),
              cell("375m", {width:1600}), cell("Gercek zamanli", {width:1600}), cell("Ucretsiz", {width:1760})
            ]}),
            new TableRow({ children: [
              cell("Gokturk-2 (TUBITAK)", {width:2200}), cell("Pankromatik + MS", {width:2200}),
              cell("2.5m", {width:1600}), cell("Degisken", {width:1600}), cell("Akademik basvuru", {width:1760})
            ]}),
            new TableRow({ children: [
              cell("OpenStreetMap", {width:2200}), cell("Yol agi, bina verisi", {width:2200}),
              cell("-", {width:1600}), cell("Surekli", {width:1600}), cell("Ucretsiz", {width:1760})
            ]}),
            new TableRow({ children: [
              cell("AFAD Deprem API", {width:2200}), cell("Sismik veri", {width:2200}),
              cell("-", {width:1600}), cell("Gercek zamanli", {width:1600}), cell("Ucretsiz", {width:1760})
            ]}),
          ]
        }),

        new Paragraph({ spacing: { after: 200 } }),

        h2("3.2. Spektral Indeks Analizi"),
        p("Uydu goruntuleri sadece gorunur isik (RGB) degil, ayni zamanda yakin kizilotesi (NIR) ve kisa dalga kizilotesi (SWIR) bantlarini da icermektedir. Bu bantlardan hesaplanan spektral indeksler, farkli arazi ozellikleri ve afet hasarlarinin tespitinde kullanilmaktadir."),

        h3("3.2.1. NDVI - Normalize Edilmis Bitki Indeksi"),
        p("NDVI = (NIR - RED) / (NIR + RED)"),
        p("Kullanim: Deprem oncesi ve sonrasi NDVI karsilastirmasi yapilarak bina cokme bolgeleri tespit edilir. Saglikli bitki ortusunun kaybi (NDVI dususu), enkaz ve yapilsal hasar gostergesidir."),

        h3("3.2.2. NDWI - Normalize Edilmis Su Indeksi"),
        p("NDWI = (GREEN - NIR) / (GREEN + NIR)"),
        p("Kullanim: Su kutlelerinin ve sel baskin alanlarinin tespiti. Pozitif NDWI degerleri su yuzeyi, negatif degerler kara yuzeyi gosterir."),

        h3("3.2.3. NBR ve dNBR - Yangin Indeksleri"),
        p("NBR = (NIR - SWIR2) / (NIR + SWIR2)"),
        p("dNBR = NBR(once) - NBR(sonra)"),
        p("Kullanim: Yanmis alanlarin ve yangin siddetinin belirlenmesi. dNBR > 0.66 yuksek siddetli yangini, 0.27-0.66 arasi orta siddeti gosterir."),

        h3("3.2.4. NDBI - Normalize Edilmis Bina Indeksi"),
        p("NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)"),
        p("Kullanim: Yapilasmis alanlarin tespiti ve deprem sonrasi yapisal degisikliklerin belirlenmesi."),

        h2("3.3. Degisim Tespiti (Change Detection)"),
        p("Sistemin temel yaklasimi, afet oncesi ve sonrasi uydu goruntulerine spektral indeks analizi uygulayarak degisim tespiti yapmasidir. Bu yontem, hangi bolgelerde ne tur degisikliklerin meydana geldigini otomatik olarak belirler:"),
        bullet("Deprem: NDVI ve NDBI degisimi ile bina cokme ve yapilsal hasar tespiti"),
        bullet("Yangin: dNBR ile yanmis alan ve yangin siddeti siniflandirmasi"),
        bullet("Sel: NDWI degisimi ile su baskin alani tespiti"),
        bullet("Heyelan: NDVI ve topografik veri kombinasyonu ile toprak kayma tespiti"),

        new Paragraph({ children: [new PageBreak()] }),

        // 4. SISTEM MIMARISI
        h1("4. SISTEM MIMARISI"),
        h2("4.1. Genel Bakis"),
        p("SafeRoute AI, modular bir mimariye sahip olup 5 ana bilesenden olusmaktadir:"),

        new Table({
          width: { size: TW, type: WidthType.DXA },
          columnWidths: [2400, 3000, 3960],
          rows: [
            new TableRow({ children: [
              headerCell("Modul", 2400), headerCell("Islem", 3000), headerCell("Teknoloji", 3960)
            ]}),
            new TableRow({ children: [
              cell("Uydu Veri Modulu", {width:2400}), cell("Sentinel-2 bant isleme, spektral indeks hesaplama", {width:3000}), cell("Python, NumPy, Rasterio", {width:3960})
            ]}),
            new TableRow({ children: [
              cell("Afet Tespit Motoru", {width:2400}), cell("Goruntu analizi, arazi siniflandirma, hasar tespiti", {width:3000}), cell("OpenCV, Scikit-learn", {width:3960})
            ]}),
            new TableRow({ children: [
              cell("Risk Analiz Motoru", {width:2400}), cell("5 katmanli risk haritasi olusturma", {width:3000}), cell("SciPy, Gaussian filtre", {width:3960})
            ]}),
            new TableRow({ children: [
              cell("Rota Planlama Motoru", {width:2400}), cell("A* algoritmasi, gercek yol rotasi", {width:3000}), cell("OSRM, NetworkX", {width:3960})
            ]}),
            new TableRow({ children: [
              cell("Acil Durum Servisleri", {width:2400}), cell("Hastane, toplanma alani, AFAD, hava durumu", {width:3000}), cell("REST API, Leaflet.js", {width:3960})
            ]}),
          ]
        }),

        new Paragraph({ spacing: { after: 200 } }),

        h2("4.2. Cok Katmanli Risk Haritasi"),
        p("Risk haritasi 5 bagimsiz katmanin agirlikli bilesiminden olusmaktadir:"),

        new Table({
          width: { size: TW, type: WidthType.DXA },
          columnWidths: [2600, 4360, 2400],
          rows: [
            new TableRow({ children: [
              headerCell("Katman", 2600), headerCell("Aciklama", 4360), headerCell("Deprem Agirligi", 2400)
            ]}),
            new TableRow({ children: [
              cell("Arazi Riski", {width:2600}), cell("Bina, orman, su, endustriyel alan vb. arazi turune gore temel risk", {width:4360}), cell("%25", {width:2400})
            ]}),
            new TableRow({ children: [
              cell("Afet Bolgesi Riski", {width:2600}), cell("Tespit edilen cokme, yangin, sel bolgelerinden uzakliga gore gradient risk", {width:4360}), cell("%30", {width:2400})
            ]}),
            new TableRow({ children: [
              cell("Ikincil Risk", {width:2600}), cell("Deprem sonrasi yangin, gaz sizintisi, sel gibi tetiklenen ikincil tehlikeler", {width:4360}), cell("%20", {width:2400})
            ]}),
            new TableRow({ children: [
              cell("Yakinlik Riski", {width:2600}), cell("Tehlikeli nesnelere (benzin ist., enerji hatti vb.) mesafe tabanli risk", {width:4360}), cell("%15", {width:2400})
            ]}),
            new TableRow({ children: [
              cell("Erisilebilirlik", {width:2600}), cell("Arazinin gecis zorlugu (yol kolay, su/enkaz zor)", {width:4360}), cell("%10", {width:2400})
            ]}),
          ]
        }),

        new Paragraph({ spacing: { after: 200 } }),
        p("Katmanlar birlestirildikten sonra Gaussian yumuslat filtresi uygulanarak gercekci gecisler elde edilir. Sonuc risk haritasi 0-1 araliginda normalize edilir."),

        h2("4.3. A* Rota Planlama Algoritmasi"),
        p("Sistem, modifiye edilmis A* algoritmasi kullanarak risk agirlikli en guvenli rotayi hesaplar. Geleneksel A* algoritmasinin sadece mesafe minimize etmesinden farkli olarak, SafeRoute AI'nin maliyet fonksiyonu su sekilde tanimlanmistir:"),
        p("f(n) = g(n) + h(n)"),
        p("g(n) = mesafe_maliyeti x arazi_carpani + risk_agirligi x hucre_riski"),
        p("Burada risk_agirligi (3.0) mesafe_agirligindan (1.0) yuksek tutularak guvenligi on plana cikarir. Yollar icin arazi carpani dusurulerek (0.7) yol tercihi saglanir. Aşırı tehlikeli bolgeler (risk > 0.85) tamamen engellenir."),
        p("Ek olarak, OSRM (Open Source Routing Machine) entegrasyonu ile bulunan rota gercek yol agi uzerinden (sokak, cadde, bulvar) gorsellestirilir."),

        new Paragraph({ children: [new PageBreak()] }),

        // 5. UYGULAMA SENARYOLARI
        h1("5. UYGULAMA SENARYOLARI"),
        h2("5.1. Kahramanmaras Depremi (6 Subat 2023)"),
        pb("Buyukluk", "Mw 7.8"),
        pb("Etkilenen Il", "11 il (Kahramanmaras, Hatay, Adiyaman, Gaziantep vd.)"),
        pb("Kayip", "50.000+ can kaybi, 100.000+ yarali"),
        pb("Sentinel-2 Analizi", "Once: 5 Subat 2023 / Sonra: 7 Subat 2023"),
        p("Sistem, deprem oncesi ve sonrasi Sentinel-2 goruntulerine NDVI ve NDBI degisim analizi uygulayarak bina cokme bolgelerini tespit etmis, 5 katmanli risk haritasi olusturmus ve en yakin hastaneye (Sutcu Imam Uni. Hastanesi, 1.2 km) gercek yollardan guvenli rota hesaplamistir. Hava durumu modulu -3\u00B0C sicaklik ve kar yagisini raporlayarak hipotermi riskine dikkat cekmistir."),

        h2("5.2. Manavgat Yangini (28 Temmuz 2021)"),
        pb("Tur", "Orman yangini"),
        pb("Etkilenen Alan", "60.000+ hektar"),
        pb("dNBR Analizi", "Yuksek siddetli yanmis alan tespiti"),
        p("dNBR analizi ile yanmis alan siniflandirmasi yapilmis, ruzgar yonu (Guneybati, 45 km/h) ve sicaklik (42\u00B0C) bilgisi ile yangin yayilma riski degerlendirilmistir. Sistem, orman alanlarindan uzak ve ruzgara karsi rota onermiistir."),

        h2("5.3. Artvin Sel Felaketi (14 Temmuz 2021)"),
        pb("Tur", "Sel ve heyelan"),
        pb("NDWI Analizi", "Su baskin alani tespiti"),
        p("NDWI degisim analizi ile sel baskin alanlari tespit edilmis, dere yataklarindan uzak yuksek kotlu rota hesaplanmistir. Hava durumu modulu yogun yagis ve \"helikopter operasyonlari imkansiz\" uyarisini raporlamistir."),

        new Paragraph({ children: [new PageBreak()] }),

        // 6. TEKNIK DETAYLAR
        h1("6. TEKNIK DETAYLAR"),
        h2("6.1. Kullanilan Teknolojiler"),

        new Table({
          width: { size: TW, type: WidthType.DXA },
          columnWidths: [2800, 3200, 3360],
          rows: [
            new TableRow({ children: [
              headerCell("Kategori", 2800), headerCell("Teknoloji", 3200), headerCell("Kullanim Alani", 3360)
            ]}),
            new TableRow({ children: [cell("Programlama Dili", {width:2800}), cell("Python 3.14", {width:3200}), cell("Backend, analiz", {width:3360})]}),
            new TableRow({ children: [cell("Web Framework", {width:2800}), cell("Flask 3.0", {width:3200}), cell("REST API, web arayuzu", {width:3360})]}),
            new TableRow({ children: [cell("Goruntu Isleme", {width:2800}), cell("OpenCV 4.8", {width:3200}), cell("Uydu goruntu analizi", {width:3360})]}),
            new TableRow({ children: [cell("Bilimsel Hesaplama", {width:2800}), cell("NumPy, SciPy", {width:3200}), cell("Spektral indeks, risk haritasi", {width:3360})]}),
            new TableRow({ children: [cell("Rota Motoru", {width:2800}), cell("A* + OSRM", {width:3200}), cell("Guvenli rota hesaplama", {width:3360})]}),
            new TableRow({ children: [cell("Harita", {width:2800}), cell("Leaflet.js + OSM", {width:3200}), cell("Interaktif harita gorsellestirme", {width:3360})]}),
            new TableRow({ children: [cell("Uydu Verisi", {width:2800}), cell("Sentinel-2 MSI", {width:3200}), cell("13 bantli multispektral goruntu", {width:3360})]}),
          ]
        }),

        new Paragraph({ spacing: { after: 200 } }),

        h2("6.2. Dosya Yapisi"),
        bullet("app.py - Ana Flask uygulamasi ve REST API"),
        bullet("disaster_detector.py - Uydu goruntu analizi ve afet tespiti"),
        bullet("risk_analyzer.py - 5 katmanli risk haritasi olusturma"),
        bullet("route_planner.py - A* algoritmasi ile guvenli rota hesaplama"),
        bullet("satellite_data.py - Sentinel-2 bant isleme ve spektral analiz"),
        bullet("emergency_services.py - Acil durum verileri (hastane, toplanma, AFAD)"),
        bullet("scenario_generator.py - Demo senaryo ureteci"),
        bullet("config.py - Sistem konfigurasyonu"),

        h2("6.3. API Endpointleri"),
        bullet("POST /api/demo - Demo senaryo analizi"),
        bullet("POST /api/analyze - Yuklenen uydu goruntusunu analiz etme"),
        bullet("POST /api/emergency-data - Acil durum verileri (hastane, deprem, hava)"),
        bullet("GET /api/spectral-info - Spektral bant ve indeks bilgileri"),
        bullet("GET /api/scenarios - Kullanilabilir senaryo listesi"),

        new Paragraph({ children: [new PageBreak()] }),

        // 7. SONUCLAR
        h1("7. SONUCLAR VE DEGERLENDIRME"),
        h2("7.1. Elde Edilen Sonuclar"),
        bullet("Sentinel-2 multispektral verisinden otomatik arazi siniflandirmasi ve afet tespiti basariyla gerceklestirilmistir."),
        bullet("NDVI, NDWI, NBR, dNBR spektral indeksleri ile deprem hasari, yanmis alan ve sel baskin bolgelerinin tespiti yapilmistir."),
        bullet("5 katmanli risk haritasi ile ikincil tehlikelerin (yangin, sel, patlama) de hesaba katildigi kapsamli risk analizi saglanmistir."),
        bullet("A* algoritmasi ve OSRM entegrasyonu ile gercek yol agi uzerinden guvenli rota hesaplanmistir."),
        bullet("Kahramanmaras depremi, Manavgat yangini ve Artvin seli senaryolarinda basarili test sonuclari elde edilmistir."),

        h2("7.2. Sistemin Avantajlari"),
        bullet("Tamamen ucretsiz ve acik kaynak veri kaynaklari kullanmaktadir."),
        bullet("Coklu afet turu destegi (deprem, yangin, sel, heyelan) sunmaktadir."),
        bullet("Ikincil risk analizi ile sadece mevcut degil, potansiyel tehlikeleri de degerlendirmektedir."),
        bullet("Gercek yol agi uzerinden navigasyon saglamaktadir."),
        bullet("Acil durum verileri (hastane, toplanma, hava durumu) ile entegre calismaktadir."),
        bullet("Turkiye'nin yerli uydu verileri (Gokturk-1/2) ile entegrasyona hazir mimaridedir."),

        h2("7.3. Sinirliliklar"),
        bullet("Sentinel-2'nin 5 gunluk revisit suresi, gercek zamanli izleme icin kisitlidir."),
        bullet("10m cozunurluk, tekil bina bazinda hasar tespiti icin yeterli degildir."),
        bullet("Bulut ortususu optik uydu goruntulemeyi engelleyebilmektedir."),
        bullet("OSRM, afet sonrasi guncellenmemis yol verisine dayanmaktadir."),

        new Paragraph({ children: [new PageBreak()] }),

        // 8. GELECEK CALISMA
        h1("8. GELECEK CALISMA PLANI"),
        numberedItem("Gokturk-1 ve Gokturk-2 uydu verisi entegrasyonu (GEZGIN platformu uzerinden)"),
        numberedItem("SAR (Sentetik Aciklikli Radar) verisi ile bulut altinda goruntuleme (Sentinel-1)"),
        numberedItem("CNN tabanli otomatik bina hasar siniflandirma modeli egitimi"),
        numberedItem("Gercek zamanli uydu akisi ile canli guncelleme"),
        numberedItem("Drone entegrasyonu ile dusuk irtifa detayli goruntuleme"),
        numberedItem("Mobil uygulama gelistirme (sahada kullanim icin)"),
        numberedItem("AFAD sistemleri ile dogrudan veri alisverisi entegrasyonu"),
        numberedItem("Nufus yogunlugu ve bina envanter verisi ile onceliklendirme algoritmasi"),

        new Paragraph({ children: [new PageBreak()] }),

        // 9. KAYNAKLAR
        h1("9. KAYNAKLAR"),
        numberedItem("ESA, \"Sentinel-2 User Handbook\", European Space Agency, 2015."),
        numberedItem("Key, C.H., Benson, N.C., \"Landscape Assessment: Ground measure of severity, the Composite Burn Index\", USDA Forest Service, 2006."),
        numberedItem("Ge, P., et al., \"NDVI-based earthquake damage assessment using remote sensing data\", Remote Sensing of Environment, 2020."),
        numberedItem("Copernicus Emergency Management Service, \"Kahramanmaras Earthquake Activation [EMSR648]\", 2023."),
        numberedItem("AFAD, \"6 Subat 2023 Kahramanmaras Depremleri Raporu\", T.C. Icisleri Bakanligi, 2023."),
        numberedItem("T.C. Cevre, Sehircilik ve Iklim Degisikligi Bakanligi, \"Bina Hasar Tespit Sonuclari\", 2023."),
        numberedItem("Hart, P.E., Nilsson, N.J., Raphael, B., \"A Formal Basis for the Heuristic Determination of Minimum Cost Paths\", IEEE, 1968."),
        numberedItem("TUBITAK UZAY, \"GEZGIN Uydu Goruntu Erisim Platformu\", gezgin.gov.tr"),
        numberedItem("OpenStreetMap Contributors, \"OpenStreetMap\", openstreetmap.org"),
        numberedItem("Project OSRM, \"Open Source Routing Machine\", project-osrm.org"),
      ]
    }
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/emred/OneDrive/Desktop/KOD/SafeRoute_AI_Teknik_Rapor.docx", buffer);
  console.log("Rapor olusturuldu: SafeRoute_AI_Teknik_Rapor.docx");
});
