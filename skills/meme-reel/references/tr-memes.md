# Türk meme klipleri (sesli)

Kaynakların hepsi Dailymotion'da, en fazla 512x288. Zamanlar Whisper "small" ile çıkarıldı; kullanmadan
önce `reel.py clips` çıktısındaki "heard" satırıyla yeniden doğrula. Klip başlıkları ve sahipleri
Dailymotion API'sinden alındı.

**Kullanıldı ve doğrulandı:** başlangıç, süre ve `cropx` değerleri hazır, doğrudan `plan.json`'a yaz.

| Ad | Replik | dm id | start | dur | cropx | Not |
|---|---|---|---|---|---|---|
| neoldu | "Ne oldu?" (Behzat Ç.) | x587xuk | 37.80 | 1.06 | 135 | 38.92'den sonra küfür var, `dur`'u uzatma. Şaşkınlık tepkisi. |
| bekle | "Neyi bekliyorsun Behzat?" | x587xuk | 25.85 | 1.55 | 115 | İzleyiciyi dürtme, CTA öncesi. |
| say | "Yüz, yüz, iki yüz, yüz…" (Erdal Bakkal para sayıyor) | x14lok5 | 0.00 | 2.50 | 155 | "Büyük sayı / uzun iş" tepkisi. |
| denmedi | "Bana böyle bir şey söylenmedi. Söyleseydi ben gelmezdim." (Erdal) | x4ifbbo | 16.40 | 2.85 | 245 | Sağ altta "Yeni Bölüm Leyla ile Mecnun" bandı ve TRT 1 logosu var. |

**Aday:** replik zamanları doğrulandı, `cropx`'i `reel.py still` ile sen belirle.

| Replik | dm id | Aralık (sn) | Kullanım |
|---|---|---|---|
| "Dişlerini sıkma Behzat." | x587xuk | 32.28-34.24 | sabır / sinir |
| "Allah Allah. Neyse o zaman." | x587xuk | 20.40-23.12 | boşvermişlik |
| "Anlıyorum." | x587xuk | 34.32-35.32 | kuru tepki |
| "Erdal kimsede parasını bırakmaz." | x14lohm | 9.52-14.12 (3.64-6.16 kısa hali) | ücretsiz / kazanç esprisi |
| "Biz hepimiz dünyaya fatura ödemeye gelmişiz." | x4ifbbo | 10.92-14.60 | abonelik / maliyet esprisi |
| "Allah Allah." (Erdal) | x4ifbbo | 4.18-5.48 | şaşkınlık |
| "Böyle olmaz!" (Erdal masaya vurur) | x4v7cx9 | 29.0-31.0 | geniş plan: `"mode": "fit"` kullan, Erdal küçük kalıyor |
| "Böyle olmaz Nurten, …" | x4v7cx9 | 48.0-51.0 | eski yöntem kötü |
| "Seviyor, sevmiyor…" (Kemal Sunal) | x1mz42x | 0-12 | kararsızlık; Whisper replikleri tek tek ayıramıyor |

**Elendi:**

- Recep İvedik (x5ni7k, xdp4sf): uygun replik ve ses kalitesi yok.
- "Hocam buldum" (Tenor): görüntüde bahis sitesi filigranı vardı, sesli kaynağı bulunamadı.
- Tenor/Imgflip GIF'leri: ses yok. Yalnız sessiz tepki karesi gerekiyorsa kullanılabilir.
- myinstants.com mp3'leri: ses var ama görüntü yok. Görüntülü klibin yanına ses katmanı olarak
  eklenebilir, tek başına kullanılmaz.

## Yeni klip bulmak

```bash
python3 scripts/reel.py search "behzat ç" --limit 30
yt-dlp -f "bv*+ba/b" --merge-output-format mp4 -o src.mp4 https://www.dailymotion.com/video/<id>
python3 scripts/reel.py stt src.mp4            # replik zamanlarını bul
python3 scripts/reel.py still src.mp4 37.9      # ızgaralı kare: yüzün x konumundan cropx'i oku
```

Haber ve siyaset içerikli sonuçları kullanma. Çocuk içeriği ve kişilerin özel görüntülerini kullanma.
Tanınmış dizi, film ve reklam anlarıyla sınırlı kal.
