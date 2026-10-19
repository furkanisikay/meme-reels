---
name: meme-reel
description: Bilinen Türk meme kliplerini (kendi orijinal sesleriyle), Türkçe TTS anlatımı, kelime kelime altyazıyı ve veriyle beslenen animasyon sahnelerini birleştirip 1080x1920 dikey Instagram Reels / TikTok / YouTube Shorts videosu (MP4) üretir. Kullanıcı bir ürünü, özelliği, lansmanı, hatayı ya da hikâyeyi "reels", "reel", "kısa video", "tiktok", "shorts", "meme'li video", "dikey video", "sosyal medya videosu" diye anlatmak istediğinde, ya da daha önce üretilmiş bir meme reel'in benzerini istediğinde bu skill'i kullan; kullanıcı "skill" demese de.
---

# Meme reel

Bu skill, bir konuyu en az bilgili izleyicinin bile anlayacağı bir dikey videoya çevirir. İzleyici herkesin
tanıdığı Türk dizi/film anlarıyla güler, aradaki animasyonlu sahnelerden ve anlatımdan da konuyu öğrenir.
Motor deterministiktir: HTML sahneler kare kare Chromium'da çizilir, ses numpy ile sentezlenip miksajlanır.

Hazır örnek: `examples/ardupilot-mcp/` (36 sn, 4 meme, 6 anlatım sahnesi). Yeni bir reel'e başlamadan önce
onun `plan.json`, `fx.js` ve `scenes/` dosyalarını oku; bütün özellikleri orada çalışırken görürsün.

## Sınırlar

- **Hiçbir şeyi yayınlama.** Videoyu kullanıcıya dosya olarak ver. Buffer'a veya başka bir platforma taslak
  bile, ancak kullanıcı o anda açıkça onaylarsa girilir.
- **Ekrandaki her sayı ve iddia doğrulanmış olsun.** Log, ölçüm, araç çıktısı ya da kullanıcının verdiği
  kaynak göster. Doğrulayamadığın bir iddiayı ("1 dakikada çözdü") videoya koyma.
- **Not satırı koyma.** Simülasyon ya da demo veri kullandıysan bile videoya ve açıklamaya "Not:" veya
  dürüstlük satırı ekleme; kullanıcı açıkça isterse ekle. İlk kareye "simülatörde bir deney" gibi bir kanca yazma.
- **Telif:** Dizi/film klipleri telifli. Kullanıcı riski kabul etmediyse önce sor. Kaynak logosunu (ör. TRT 1)
  silme; bahis sitesi gibi üçüncü taraf reklam filigranlarını kırparak çıkar.
- **TTS lisansı:** `edge-tts` ücretsiz Edge sesli okuma servisini kullanır; ticari kullanımı gri alanda kalır.
  Ticari yayında aynı sesler Azure Speech'te lisanslı olarak var, ya da kullanıcının kendi sesi kullanılabilir.

## Paylaşım metni

Kullanıcı açıklama (caption) isterse:

- Videodaki cümleleri tekrar etme. Açıklama videonun anlatmadığını anlatır: ürün ne, kime yarar, nerede bulunur.
- Birinin arkadaşına yazdığı gibi, gündelik Türkçeyle yaz. Sonda yoruma davet eden tek bir soru olsun.
- **"Not:" ya da dürüstlük satırı ekleme.** Simülasyon, demo veri, yapay zeka kullanımı gibi açıklamalar
  açıklama metnine girmez. Yapay zeka etiketi gerekiyorsa platformun kendi ayarıyla işaretlenir.

## Kurulum

```bash
bash scripts/setup.sh        # pip: edge-tts faster-whisper numpy scipy yt-dlp; ffmpeg ve Playwright kontrolü
```

Ortamla ilgili bilinen sorunlar (proxy/TLS, YouTube bot kontrolü, Chromium'da H.264 olmaması, Whisper ve
PyAV) ve çözümleri `references/pitfalls.md` içinde. Takıldığında oraya bak.

## Akış

1. **Gerçekleri topla.** Videonun iddiasını kaynağından çıkar: araç çıktısı, log, ölçüm. Sayıları ve
   zamanları bir yere yaz; sahneler bu değerleri kullanacak.
2. **Senaryoyu yaz** (aşağıdaki kalıp). Her anlatım cümlesi 2-7 sn, her meme 1-3 sn.
3. **Meme seç.** Önce `references/tr-memes.md` kataloğuna bak (repliği ve zaman damgası doğrulanmış klipler).
   Yeni klip için `python3 scripts/reel.py search "erdal bakkal"` ile Dailymotion'da ara, indirip
   `reel.py stt` ile repliğin tam saniyesini bul. Yüzün yerini `reel.py still KAYNAK SANİYE` ile çıkan
   ızgaralı karede ölç (`cropx`).
4. **Projeyi kur:** `plan.json`, `style.css`, `fx.js`, gerekiyorsa `data.js` ve `scenes/*.html`. Örneği
   kopyalayıp değiştirmek en hızlısı.
5. **Klipleri kes ve doğrula:** `reel.py clips PROJE`. Her klip için Whisper'ın duyduğu metin ile `quote`
   yan yana basılır. Uyuşmuyorsa zamanı düzelt.
6. **Seslendir:** `reel.py tts PROJE --verify`. Whisper bir kelimeyi yanlış duyuyorsa TTS de onu yanlış
   okuyordur; `say` metnini fonetik yaz (ör. `ArduPilot em si pi'ye`), ekranda doğrusu `show` ile görünür.
7. **Kurgu ve önizleme:** `reel.py build PROJE` sonra `reel.py preview PROJE`. `build/sheet.png` her sahneden
   3 kare gösterir. Sheet'i aç ve şunlara bak: taşan veya üst üste binen öğe, güvenli bölgeye giren yazı,
   boş kalan ekran, okunmayan altyazı. Düzelt, tekrarla.
8. **Render:** `reel.py render PROJE --verify` → `PROJE/out/<title>.mp4`. Çıktıda süre, entegre ses
   (-14 LUFS civarı olmalı) ve tepe değeri yazar; `--verify` bütün videoyu Whisper'dan geçirir. Bütün
   anlatım ve meme replikleri doğru duyuluyorsa müzik konuşmayı bastırmıyor demektir.
9. Videoyu kullanıcıya gönder. Hangi klipleri hangi kaynaktan aldığını, ekledikleri riskleri (telif, TTS
   lisansı, düşük çözünürlüklü kaynak) ve senin itiraz ettiğin kurgu kararlarını kısaca yaz.

## Senaryo kalıbı

Kanca kuralları ve gerekçeleri `references/hooks.md` içinde. Kısa hali:

| Vuruş | Süre | Ne olur |
|---|---|---|
| Kanca | 0-3 sn | Olayın ortasından aç (düşen drone, kırmızı hata). İlk karede 4-7 kelimelik cümle zaten görünür olsun; ses kapalı izleyen de anlasın. |
| Tepki memesi | 1-2 sn | Şaşkınlık ("Ne oldu?"). Kancanın hemen ardından. |
| Sorun | 3-6 sn | Sorunun büyüklüğünü somut bir sayıyla göster (1.558.457 satır). |
| Tepki memeleri | 2-5 sn | Sorunun saçmalığına bir-iki meme. Üst yazı (`cap`) meme ile konuyu bağlar. |
| Çözüm | 3-4 sn | Ürünü kullanma anı; gerçek arayüz ya da sadık bir taklidi. |
| Cevap | 4-7 sn | Asıl bulgu, veriyle animasyonlu. En uzun ve en "öğreten" sahne. |
| Değer | 2-3 sn | Ücretsiz, açık kaynak, kurulum komutu gibi. |
| Dürtme memesi | 1-2 sn | İzleyiciye seslenen meme ("Neyi bekliyorsun Behzat?"). |
| Kapanış | 3-5 sn | Ne yapmalı + "Link profilde" oku. |

Toplam 25-36 sn. 30 sn'yi aşıyorsa en uzun anlatım cümlesini kısaltmayı öner.

## plan.json

```jsonc
{
  "title": "<Konu> - Reels <ad>",            // çıktı dosyasının adı
  "voice": "tr-TR-EmelNeural", "rate": "+6%", // tr-TR-AhmetNeural bu serviste ses döndürmüyor
  "clips": {                                   // meme kaynakları
    "neoldu": {"dm": "x587xuk", "start": 37.80, "dur": 1.06, "cropx": 135, "quote": "— Ne oldu?"}
    // kaynak: "dm" (Dailymotion id) | "url" (yt-dlp) | "file" (yerel). mode: "face" (4:5 yüz kırpma, varsayılan) | "fit" (geniş plan)
  },
  "lines": {                                   // anlatım; "show" ekranda görünen hali (opsiyonel)
    "n1": {"say": "Dronum yirmi metreden düştü.", "show": "Drone'um 20 metreden düştü."}
  },
  "scenes": [                                  // sırayla oynar; süreler sesten hesaplanır
    {"id": "a", "line": "n1", "html": "scenes/crash.html", "pad": 0.25, "cap": "opsiyonel üst yazı"},
    {"id": "m1", "clip": "neoldu", "cap": "opsiyonel üst yazı"}
  ],
  "music": {"style": "phonk", "bpm": 120, "level": 0.42, "mute": [["a@düştü+0.05", "b"]], "light": []},
  "sfx": [{"fx": "boom", "at": "a@düştü+0.1", "gain": 1.0}]
}
```

`show` kelime sayısı `say` ile aynıysa her kelime kendi zamanını alır, değilse kelimeler konuşma süresine eşit
yayılır. Meme sahnesinin süresi klibin süresidir; anlatım sahnesininki ses + 0,08 sn + `pad`.

## Sahne yazmak

Her anlatım sahnesi bir HTML parçası (`scenes/<ad>.html`) ve `fx.js` içinde bir `FX.<id>` fonksiyonudur.
Sahne `<section id="<id>" class="k-<ad>">` içine konur. Motor kesme, punch-in zoom, `cap` animasyonu,
meme karesi değiştirme ve karaoke altyazıyı kendisi yapar; `FX` yalnız sahneye özgü hareketi çizer.

```js
FX.d = ({ s, el, t, lt, d, punch, word }) => {
  // lt: sahne içi saniye, d: sahne süresi, t: video saniyesi
  // word('motor', 0.5): "motor" kelimesinin söylendiği sahne içi saniye (bulunamazsa 0.5)
  pop($('mhead'), lt, word('motor'), 0.3);           // yükselerek belir
  stamp($('tag2'), lt, word('yetme'), 'translateX(-50%)'); // taşarak büyü
  type($('cmd'), 'pip install ardupilot-mcp', lt, 0.1, 0.8); // daktilo
};
```

Yardımcılar: `seg`, `clamp`, `lerp`, `easeOut`, `easeInOut`, `back`, `interp(seri, t)`, `pop`, `stamp`, `type`.
Kural: kare yalnız `t`'ye bağlı olsun. `setTimeout`, `Date`, CSS transition ve rastgelelik kullanma; kareler
tek tek çekildiği için bunlar titreme ve atlama yapar.

**Yerleşim (1080x1920):** üst 220 px, alt 400 px ve sağ 150 px'i Instagram arayüzü kapatır. Asıl içerik
y 230-1300 arasında dursun. Altyazı y 1350'de, `cap` y 230'da. Sahneyi ekrana yay; küçük kartlar ortada boşluk
bırakırsa telefonda ucuz görünür. Yazılar en az 40 px, anahtar sayılar 100 px ve üstü.

**Görsel dil (örnekteki):** koyu lacivert zemin `#0A0F1C`, camgöbeği `#38BDF8` normal durum, kırmızı
`#F43F5E` arıza, yeşil `#34D399` çözüm, amber `#FBBF24` dikkat/CTA. İkonlar Tabler (inline SVG).

## Ses

- Anlatım -17 dBFS RMS, meme sesleri -16'ya eşitlenir. Müzik anlatım altında ~%72, meme altında ~%88 kısılır.
  Final video -14 LUFS'a normalize edilir.
- Müzik telifsiz, koddan üretilir (120 BPM phonk: kick, 808, clap, hi-hat, cowbell). `mute` penceresinde
  müzik susar; çarpma anından sonraki sessizlik en güçlü vuruştur.
- Efektler: `whoosh` (sahne geçişi; `"at": "cuts"` hepsine koyar), `fall`, `boom`, `hit`, `click`
  (daktilo, sayaç), `beep`, `tone`, `ding`, `riser`, `sparkle`. Parametreler `scripts/synth.py` içinde.
- Zaman çapaları: sayı (mutlak sn) | `"b"` (sahne başı) | `"b.end"` | `"d@yetme"` (o sahnede "yetme" ile
  başlayan kelime), hepsine `+0.1` / `-0.4` eklenebilir. Tekrar için `every` + `count` ya da `until`;
  `fall` ve `whoosh` gibi süpürmelerde yalnız `until` vermek sesi o ana kadar uzatır.

## Yapay zeka gibi durmasın

Tamamen sentetik bir video (TTS sesi, kusursuz vektör sahneler, her efektin kelimeye tam oturması) izleyiciye
"yapay zeka yaptı" hissi verir. Kullanıcıya şunları öner, elindeki imkâna göre uygula:

- **Gerçek ekran kaydı:** Ürün arayüzünü taklit etmek yerine gerçek kullanımın kaydını sahneye koy
  (`clips` içinde `"file"` + `"mode": "fit"`). Bir tane bile gerçek görüntü bütün videoya güven katar.
- **İnsan sesi:** Kullanıcı satırları telefona kendi okursa `reel.py voice PROJE n1 kayit.m4a` o kaydı
  TTS yerine koyar, baş/son sessizliği kırpar, kelime zamanlarını Whisper'la çıkarır. TTS'in en çok ele
  veren kısmı tonlamadır.
- **Konuşma dili:** Senaryoyu kurumsal değil, birinin arkadaşına anlatışı gibi yaz: "Logu açtım", "yetmemiş".
- **Kusur ve ritim:** Her sahneyi aynı uzunlukta yapma. Bazı efektleri kelimeden 1-2 kare kaydır, bir
  sahnede müziği tamamen kes. Dümdüz simetrik yerleşimden kaçın.
- **Tanıdık format:** Hesabın kendi yüzü ya da sesi olan bir giriş (1 sn "bakın ne oldu") meme serisinden
  daha insani durur.

## Dosyalar

- `scripts/reel.py`: bütün akış (search, stt, still, clips, tts, voice, build, preview, mix, render, all)
- `scripts/engine.js`, `scripts/base.css`: kare motoru ve ortak stiller
- `scripts/synth.py`: müzik ve efekt üreteçleri
- `scripts/capture.js`: Playwright ile kare çekimi
- `references/tr-memes.md`: doğrulanmış Türk meme klipleri (id, saniye, replik, kırpma)
- `references/hooks.md`: kanca ve tempo kuralları, kaynakları
- `references/pitfalls.md`: ortam sorunları ve çözümleri
- `examples/ardupilot-mcp/`: tam çalışan örnek proje
