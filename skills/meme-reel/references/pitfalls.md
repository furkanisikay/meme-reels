# Ortam sorunları

| Belirti | Sebep | Çözüm |
|---|---|---|
| `edge-tts` TLS / sertifika hatası | Kurumsal ya da bulut proxy'si kendi CA'sını kullanıyor; edge-tts sertifikayı `certifi`'den alıyor | `reel.py` `SSL_CERT_FILE`'ı (yoksa `/root/.ccr/ca-bundle.crt`) `certifi.where`'e bağlar ve `HTTPS_PROXY`'yi edge-tts'e verir. Başka ortamda `SSL_CERT_FILE`'ı ayarla. |
| `NoAudioReceived` | Ses o serviste kapalı (tr-TR-AhmetNeural) ya da anlık kopma | `reel.py` 5 kez dener. Ses hep boş dönüyorsa başka ses seç. |
| TTS bir kelimeyi yanlış okuyor | Marka adı, İngilizce kelime, kesme işareti | `say` alanına fonetik yaz (`ArduPilot em si pi'ye`, `Dronum`), ekrandaki hali `show`'da kalsın. `tts --verify` ile kontrol et. |
| yt-dlp YouTube'da "Sign in to confirm you're not a bot" | Bulut IP'leri bot kontrolüne takılıyor | Dailymotion kullan, ya da kullanıcıdan klibi dosya olarak iste (`"file"`). |
| Pixabay, Freesound 403; Instagram erişilemiyor | Ağ politikası / bot koruması | Müzik ve efekti `synth.py` üretir. Instagram örneklerini kullanıcıdan ekran görüntüsü olarak iste. |
| Chromium `<video>` MP4 oynatmıyor | Playwright Chromium'da H.264 yok | Klipler JPG kare dizisine çevrilir (`clips`), sayfa kareleri `img.src` ile değiştirir. |
| Kare boş ya da eski görüntü | Görsel henüz yüklenmeden ekran görüntüsü alındı | `capture.js` her karede bütün `img`'lerin yüklenmesini bekler. Yeni bir görsel türü eklersen bekleme koşuluna ekle. |
| faster-whisper `metadata_errors` hatası | PyAV sürüm uyumsuzluğu | Ses ffmpeg ile float32'ye çözülüp verilir (`transcribe`). |
| Whisper modeli inmiyor | Hugging Face XET aktarımı proxy'den geçmiyor | `HF_HUB_DISABLE_XET=1` (reel.py ayarlar) ve `SSL_CERT_FILE`. |
| `rm` engelleniyor | Güvenlik kancası toplu silmeyi reddediyor | Yeni klasör adıyla çalış (`frames2`); `reel.py` kendi `build/` klasörlerini `shutil.rmtree` ile temizler. |
| Kaynak 288p, büyütünce bulanık | Dailymotion'daki eski yüklemeler | `face` modu yüzü 4:5 kırpıp 1080x1350'ye çıkarır, `unsharp` uygular, arkaya aynı sahnenin bulanığını koyar. Daha iyisi için kullanıcıdan HD kaynak iste. |
| Meme replikten sonra küfür / alakasız söz | Klip kesimi uzun | `dur`'u Whisper zamanına göre kısalt, `clips` çıktısındaki "heard" satırını oku. |
| Terminal kartında komut taşıyor ya da alt satıra kayıyor | Komut uzadı (`pip install ...`), 52 px mono yazı 860 px karta sığmıyor | `.tbody` için `font-size: 44px; white-space: nowrap;` ver ve `preview --at` ile kareye bak. |
| `render --from` sonrası sahne kayık | Anlatım değişti, sahne süreleri kaydı | `--from` yalnız süreler aynıyken kullanılır; anlatım değiştiyse tam `render` çalıştır. |
