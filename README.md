# meme-reels

Dikey Instagram Reels, TikTok ve Shorts videosu üreten Claude skill'i. Videoda herkesin bildiği Türk dizi ve
film anları kendi sesleriyle oynar. Aralarda Türkçe TTS anlatım, kelime kelime altyazı ve verinden çizilen
animasyon sahneleri yer alır. Çıktı 1080x1920, 30 fps, -14 LUFS bir MP4.

Claude'a "şu özelliği anlatan meme'li bir reels yap" demen yeterli. Skill senaryoyu kurar, klipleri bulup
keser, seslendirir, kareleri render eder ve videoyu sana dosya olarak verir. Hiçbir platformda kendisi
paylaşım yapmaz.

## Gerekenler

Python 3.10+, ffmpeg, Node ve Playwright Chromium. `skills/meme-reel/scripts/setup.sh` Python paketlerini
kurar, diğerlerini kontrol eder.

## İçerik

- `skills/meme-reel/SKILL.md`: akış, plan formatı, sahne yazımı, ses
- `skills/meme-reel/scripts/`: `reel.py` (komut satırı), kare motoru, ses sentezi, kare çekimi
- `skills/meme-reel/references/`: doğrulanmış Türk meme kataloğu, kanca kuralları, ortam sorunları
- `skills/meme-reel/examples/ardupilot-mcp/`: tam çalışan örnek (36 sn)

## Bilinmesi gerekenler

- Meme klipleri telifli dizi ve filmlerden gelir. Kullanmadan önce riski değerlendir.
- `edge-tts` ücretsiz Edge sesli okuma servisini kullanır, ticari kullanımı gri alandadır. Ticari yayın için
  Azure Speech ya da kendi ses kaydın (`reel.py voice`) daha güvenli.
- Dailymotion kaynakları çoğunlukla 288p'dir. Motor yüzü kırpıp büyütür, yine de HD kaynak daha iyi sonuç verir.
