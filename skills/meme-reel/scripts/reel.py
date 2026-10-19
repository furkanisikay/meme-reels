#!/usr/bin/env python3
"""Meme reel pipeline: meme clips + TTS narration + HTML scenes -> 1080x1920 MP4.

    reel.py search "behzat ç ne oldu"      Dailymotion search (clips with sound)
    reel.py stt FILE...                    transcribe audio/video (Turkish) to verify lines
    reel.py still SRC SECONDS              gridded source frame, to read cropx for a face crop
    reel.py clips PROJECT                  download + cut meme clips, transcribe each cut
    reel.py tts PROJECT                    synthesize narration lines with word timings
    reel.py voice PROJECT KEY FILE         use a human recording for line KEY instead of TTS
    reel.py build PROJECT                  timeline.json + reel.html
    reel.py preview PROJECT [--at 1,2.5]   key frames -> build/sheet.png
    reel.py render PROJECT                 all frames + audio mix -> out/<title>.mp4
    reel.py render PROJECT --from 26.7     keep earlier frames, re-render from 26.7 s on
    reel.py all PROJECT                    clips (missing only), tts, build, preview, render

PROJECT holds plan.json, style.css, fx.js, optional data.js and scenes/*.html.
See SKILL.md for the plan format.
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CA = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").exists() else None)
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
FPS = 30
LEAD = 0.08  # silence before each narration line inside its scene


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, check=False, **kw)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def duration(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def load_plan(project):
    project = Path(project).resolve()
    plan = json.loads((project / "plan.json").read_text())
    return project, plan, project / "build"


# ---------------------------------------------------------------- search / stt
def cmd_search(args):
    q = urllib.parse.quote(args.query)
    url = f"https://api.dailymotion.com/videos?search={q}&fields=id,title,duration,owner.screenname&limit={args.limit}"
    data = json.load(urllib.request.urlopen(url, timeout=30))
    for v in data["list"]:
        print(f"{v['id']:10} {v['duration']:4}s  {v['owner.screenname'][:20]:20}  {v['title']}")


def whisper():
    if CA:
        os.environ.setdefault("SSL_CERT_FILE", CA)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", CA)
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel

    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe(model, f, lang="tr"):
    import numpy as np

    # decode with ffmpeg: PyAV inside faster-whisper chokes on some containers
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=False).stdout
    segs, _ = model.transcribe(np.frombuffer(raw, np.float32), language=lang)
    return [(s.start, s.end, s.text.strip()) for s in segs]


def cmd_stt(args):
    m = whisper()
    for f in args.files:
        print("==", f)
        for a, b, txt in transcribe(m, f, args.lang):
            print(f"  {a:6.2f}-{b:6.2f} {txt}")


def cmd_still(args):
    """One source frame at 2x with a grid: thin lines every 50 px, red every 100 px (source pixels)."""
    out = args.out or f"{Path(args.src).stem}_{args.at:.2f}.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(args.at), "-i", args.src, "-frames:v", "1", "-vf",
         "drawgrid=w=50:h=50:t=1:c=yellow@0.5,drawgrid=w=100:h=100:t=2:c=red@0.8,scale=iw*2:ih*2", out])
    print(out)


# ---------------------------------------------------------------- clips
def fetch(src, cache):
    """src: {"dm": id} | {"url": ...} | {"file": path}. Returns a local video path."""
    if "file" in src:
        return Path(src["file"]).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    url = src.get("url") or f"https://www.dailymotion.com/video/{src['dm']}"
    key = src.get("dm") or hashlib.sha1(url.encode()).hexdigest()[:10]
    out = cache / f"{key}.mp4"
    if not out.exists():
        run(["yt-dlp", "-q", "-f", "bv*+ba/b", "--merge-output-format", "mp4", "-o", str(out), url])
    return out


def cut(video, c, outdir):
    """Cut [start, start+dur) into full-frame 1080x1920 JPGs + a WAV.

    mode "face": 4:5 crop at cropx (source px) scaled to 1080x1350, over a blurred
    fill of the same shot. mode "fit": whole frame at 1080 wide over the blur.
    """
    w, h = map(int, run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)]).split(",")[:2])
    mode = c.get("mode", "face")
    if mode == "face":
        cw = min(w, round(h * 0.8) // 2 * 2)
        x = c.get("cropx", (w - cw) // 2)
        fg = f"crop={cw}:{h}:{x}:0,scale=1080:1350:flags=lanczos,unsharp=5:5:0.7"
        y = (1920 - 1350) // 2
    else:
        fg = "scale=1080:-2:flags=lanczos,unsharp=5:5:0.6"
        y = "(1920-overlay_h)/2"
    flt = (f"[0:v]fps={FPS},split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
           f"boxblur=28:4,eq=brightness=-0.18:saturation=0.8[bg];[b]{fg}[fg];[bg][fg]overlay=0:{y}")
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    ss, t = str(c["start"]), str(c["dur"])
    run(["ffmpeg", "-v", "error", "-ss", ss, "-t", t, "-i", str(video), "-filter_complex", flt, "-q:v", "2", str(outdir / "%04d.jpg")])
    run(["ffmpeg", "-v", "error", "-y", "-ss", ss, "-t", t, "-i", str(video), "-vn", "-ac", "2", "-ar", "48000", str(outdir.with_suffix(".wav"))])


def cmd_clips(args, only_missing=False):
    _project, plan, build = load_plan(args.project)
    model = None
    for name, c in plan.get("clips", {}).items():
        out = build / "mm" / name
        if only_missing and out.exists() and any(out.glob("*.jpg")):
            continue
        cut(fetch(c, build / "src"), c, out)
        model = model or whisper()
        heard = " ".join(x[2] for x in transcribe(model, out.with_suffix(".wav")))
        print(f"{name:12} {len(list(out.glob('*.jpg'))):3} frames | heard: {heard!r} | quote: {c.get('quote', '')!r}")


# ---------------------------------------------------------------- tts
async def _tts_line(text, voice, rate, out):
    import certifi

    if CA:
        certifi.where = lambda: CA  # edge-tts builds its TLS context from certifi
    import edge_tts

    for attempt in range(5):
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, proxy=PROXY, boundary="WordBoundary")
            words, audio = [], bytearray()
            async for ch in com.stream():
                if ch["type"] == "audio":
                    audio += ch["data"]
                elif ch["type"] == "WordBoundary":
                    words.append([ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]])
            if audio:
                out.write_bytes(bytes(audio))
                return words
        except Exception as e:  # noqa: BLE001  (service drops connections now and then)
            print(f"  retry {attempt}: {type(e).__name__}", file=sys.stderr)
        await asyncio.sleep(2 + attempt)
    sys.exit(f"TTS returned no audio for {text!r} with {voice} (try another voice)")


def cmd_tts(args):
    _project, plan, build = load_plan(args.project)
    d = build / "tts"
    d.mkdir(parents=True, exist_ok=True)
    voice, rate = plan.get("voice", "tr-TR-EmelNeural"), plan.get("rate", "+6%")
    idx_p = d / "lines.json"
    idx = json.loads(idx_p.read_text()) if idx_p.exists() else {}
    for key, ln in plan["lines"].items():
        sig = hashlib.sha1(f"{voice}|{rate}|{ln['say']}".encode()).hexdigest()
        if idx.get(key, {}).get("manual"):  # a human recording from `reel.py voice`
            continue
        if idx.get(key, {}).get("sig") == sig and (d / f"{key}.mp3").exists():
            continue
        words = asyncio.run(_tts_line(ln["say"], voice, rate, d / f"{key}.mp3"))
        idx[key] = {"sig": sig, "say": ln["say"], "words": words}
        print(f"{key}: {duration(d / f'{key}.mp3'):.2f}s  {ln['say']}")
    idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    if args.verify:
        m = whisper()
        for key in plan["lines"]:
            print(f"{key}: heard {' '.join(x[2] for x in transcribe(m, d / f'{key}.mp3'))!r}")


def cmd_voice(args):
    """Use a human recording for one narration line; word timings come from Whisper."""
    _project, plan, build = load_plan(args.project)
    d = build / "tts"
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{args.key}.mp3"
    run(["ffmpeg", "-v", "error", "-y", "-i", args.file, "-af", ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB,areverse"), "-ac", "1", "-ar", "48000", "-b:a", "192k", str(out)])
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=False).stdout
    segs, _ = whisper().transcribe(np.frombuffer(raw, np.float32), language=plan.get("lang", "tr"), word_timestamps=True)
    words = [[w.start, w.end, w.word.strip()] for sg in segs for w in sg.words]
    idx_p = d / "lines.json"
    idx = json.loads(idx_p.read_text()) if idx_p.exists() else {}
    idx[args.key] = {"manual": True, "say": " ".join(w[2] for w in words), "words": words}
    idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    print(f"{args.key}: {duration(out):.2f}s heard {idx[args.key]['say']!r}")


# ---------------------------------------------------------------- build
def timeline(project, plan, build):
    lines = json.loads((build / "tts" / "lines.json").read_text())
    t, scenes, audio = 0.0, [], []
    for sc in plan["scenes"]:
        s = {k: v for k, v in sc.items() if k not in ("html", "pad")}
        if "clip" in sc:
            frames = len(list((build / "mm" / sc["clip"]).glob("*.jpg")))
            if not frames:
                sys.exit(f"clip {sc['clip']} has no frames: run `reel.py clips`")
            d = frames / FPS
            s.update(frames=frames, quote=sc.get("quote", plan["clips"][sc["clip"]].get("quote", "")))
            audio.append({"file": str(build / "mm" / f"{sc['clip']}.wav"), "at": t, "kind": "meme"})
        else:
            key = sc["line"]
            mp3 = build / "tts" / f"{key}.mp3"
            d = duration(mp3) + LEAD + sc.get("pad", 0.2)
            words = lines[key]["words"]
            show = plan["lines"][key].get("show")
            if show:
                shown = show.split()
                if len(shown) == len(words):  # same count: keep each word's own timing
                    words = [[a, b, w] for (a, b, _), w in zip(words, shown)]
                else:  # spread the shown words evenly over the spoken span
                    s0, s1, n = words[0][0], words[-1][1], len(shown)
                    words = [[s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n, w] for i, w in enumerate(shown)]
            s["words"] = [[round(t + LEAD + a, 3), round(t + LEAD + b, 3), w] for a, b, w in words]
            audio.append({"file": str(mp3), "at": t + LEAD, "kind": "voice"})
        s.update(a=round(t, 3), b=round(t + d, 3))
        scenes.append(s)
        t += d
    return {"scenes": scenes, "audio": audio, "total": round(t + 0.02, 2), "fps": FPS}


def cmd_build(args):
    project, plan, build = load_plan(args.project)
    T = timeline(project, plan, build)
    (build / "timeline.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
    parts = []
    for sc, s in zip(plan["scenes"], T["scenes"]):
        cap = f'<div class="cap" id="{s["id"]}c">{s["cap"]}</div>' if s.get("cap") else ""
        if "clip" in sc:
            body = (f'<img class="full" id="{s["id"]}i" src="mm/{s["clip"]}/0001.jpg">'
                    f'<div class="quote" id="{s["id"]}q">{s["quote"]}</div>')
            cls = "meme"
        else:
            body = (project / sc["html"]).read_text() if sc.get("html") else ""
            cls = "k-" + (Path(sc["html"]).stem if sc.get("html") else "plain")
        parts.append(f'<section id="{s["id"]}" class="{cls}">{body}{cap}</section>')
    opt = lambda f: (project / f).read_text() if (project / f).exists() else ""
    html = f"""<!doctype html><html lang="{plan.get('lang', 'tr')}"><head><meta charset="utf-8">
<style>{(HERE / 'base.css').read_text()}{opt('style.css')}</style></head>
<body><div id="stage"><div class="grid"></div>
{''.join(parts)}
<div class="sub" id="sub"></div>
</div><script>
const SC = {json.dumps(T['scenes'], ensure_ascii=False)};
const FPS = {FPS};
{opt('data.js')}
{(HERE / 'engine.js').read_text()}
{opt('fx.js')}
render(0);
</script></body></html>"""
    (build / "reel.html").write_text(html)
    print(f"total {T['total']}s")
    for s in T["scenes"]:
        what = f"meme {s['clip']}" if "clip" in s else " ".join(w[2] for w in s["words"])
        print(f"  {s['id']:4} {s['a']:6.2f}-{s['b']:6.2f}  {what}")


# ---------------------------------------------------------------- capture
def capture(build, outdir, dur=None, times=None, start=0):
    env = dict(os.environ)
    if Path("/opt/node22/lib/node_modules").exists():
        env["NODE_PATH"] = "/opt/node22/lib/node_modules"
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["node", str(HERE / "capture.js"), str(build / "reel.html"), str(outdir), str(FPS), str(dur or 1)]
    if times:
        cmd.append(",".join(f"{x:.3f}" for x in times))
    elif start:
        cmd += ["", str(start)]
    run(cmd, env=env)


def cmd_preview(args):
    _project, _plan, build = load_plan(args.project)
    T = json.loads((build / "timeline.json").read_text())
    if getattr(args, "at", None):
        times = [float(x) for x in args.at.split(",")]
    else:
        times = [s["a"] + (s["b"] - s["a"]) * f for s in T["scenes"] for f in (0.1, 0.55, 0.95)]
    d = build / "preview"
    if d.exists():
        shutil.rmtree(d)
    capture(build, d, times=times)
    files = sorted(d.glob("t*.png"), key=lambda p: float(p.stem[1:]))
    cols = min(10, len(files))
    rows = -(-len(files) // cols)
    lst = build / "preview.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
         f"scale=270:480,tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1", str(build / "sheet.png")])
    print(build / "sheet.png")


# ---------------------------------------------------------------- audio
def anchor(spec, T):
    """number | "<scene>" | "<scene>.end" | "<scene>@<word prefix>", each with optional +/-offset."""
    if isinstance(spec, (int, float)):
        return float(spec)
    m = re.fullmatch(r"([\w-]+)(?:\.(end)|@([^+\-]+))?([+-][\d.]+)?", spec.strip())
    if not m:
        sys.exit(f"bad anchor {spec!r}")
    sid, end, word, off = m.groups()
    s = next((x for x in T["scenes"] if x["id"] == sid), None)
    if s is None:
        sys.exit(f"anchor {spec!r}: no scene {sid}")
    if word:
        w = next((x for x in s.get("words", []) if x[2].lower().startswith(word.lower())), None)
        if w is None:
            sys.exit(f"anchor {spec!r}: no word starting with {word!r} in scene {sid}")
        base = w[0]
    else:
        base = s["b"] if end else s["a"]
    return base + float(off or 0)


def cmd_mix(args):
    import numpy as np
    from scipy.io import wavfile

    sys.path.insert(0, str(HERE))
    import synth as S

    _project, plan, build = load_plan(args.project)
    T = json.loads((build / "timeline.json").read_text())
    SR, N = S.SR, int(S.SR * T["total"])

    def load(f):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=False).stdout
        return np.frombuffer(raw, np.float32).astype(np.float64)

    def rms_norm(x, db):
        r = np.sqrt(np.mean(x[np.abs(x) > 1e-3] ** 2)) + 1e-9
        return x * (10 ** (db / 20) / r)

    def put(buf, t, sig, g=1.0):
        i = int(t * SR)
        j = min(N, i + len(sig))
        if 0 <= i < N:
            buf[i:j] += g * sig[: j - i]

    voice, memes, vmask, mmask = (np.zeros(N) for _ in range(4))
    for a in T["audio"]:
        x = load(a["file"])
        i = int(a["at"] * SR)
        if a["kind"] == "voice":
            put(voice, a["at"], rms_norm(x, -17))
            vmask[i:i + len(x)] = 1
        else:
            n = int(0.012 * SR)  # de-click the hard cut edges
            x[:n] *= np.linspace(0, 1, n)
            x[-n:] *= np.linspace(1, 0, n)
            put(memes, a["at"], rms_norm(x, -16))
            mmask[i:i + len(x)] = 1

    mu = plan.get("music", {})
    windows = lambda key: [(anchor(a, T), anchor(b, T)) for a, b in mu.get(key, [])]
    mute, light = windows("mute"), windows("light")
    music = np.zeros(N)
    if mu.get("style", "phonk") != "none":
        music = S.phonk(N, mu.get("bpm", 120), muted=lambda t: any(a <= t < b for a, b in mute),
                        fade_out=mu.get("fade_out", 0.6), light=lambda t: any(a <= t < b for a, b in light))

    sfx = np.zeros(N)
    for e in plan.get("sfx", []):
        fn = S.EFFECTS[e["fx"]]
        g = e.get("gain", 0.5)
        if e.get("at") == "cuts":
            for s in T["scenes"][1:]:
                put(sfx, s["a"] - 0.16, fn(*e.get("args", [])), g)
            continue
        t0 = anchor(e["at"], T)
        if "every" in e:
            t1 = anchor(e["until"], T) if "until" in e else t0 + e["every"] * (e.get("count", 1) - 0.5)
            k = 0
            while t0 + k * e["every"] < t1:
                put(sfx, t0 + k * e["every"] + S.rng.uniform(0, e.get("jitter", 0)), fn(*e.get("args", [])), g)
                k += 1
        elif "until" in e:  # sweep effects stretched to land on an anchor
            put(sfx, t0, fn(anchor(e["until"], T) - t0, *e.get("args", [])), g)
        else:
            put(sfx, t0, fn(*e.get("args", [])), g)

    smooth = lambda m, ms: S.lp(m, 1000 / ms)
    vs, ms = np.clip(smooth(vmask, 60), 0, 1), np.clip(smooth(mmask, 40), 0, 1)
    duck = np.clip(1 - 0.72 * vs - 0.88 * ms, 0.1, 1)
    if np.abs(music).max() > 0:
        music = music / np.abs(music).max() * mu.get("level", 0.42)
    if np.abs(sfx).max() > 0:
        sfx = sfx / np.abs(sfx).max() * plan.get("sfx_level", 0.55)
    mix = np.tanh(1.05 * (voice + memes + music * duck + sfx * (1 - 0.35 * vs)))
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
    wavfile.write(build / "audio.wav", SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))
    print(build / "audio.wav")


def cmd_render(args):
    project, plan, build = load_plan(args.project)
    T = json.loads((build / "timeline.json").read_text())
    frames = build / "frames"
    start = round(getattr(args, "from_sec", 0) * FPS)
    if start and len(list(frames.glob("f*.png"))) < start:
        sys.exit("--from needs a complete earlier render in build/frames")
    if frames.exists() and not start:
        shutil.rmtree(frames)
    if start:
        for f in frames.glob("f*.png"):
            if int(f.stem[1:]) >= start:
                f.unlink()
    capture(build, frames, dur=T["total"], start=start)
    cmd_mix(args)
    out = project / "out" / f"{plan.get('title', project.name)}.mp4"
    out.parent.mkdir(exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"), "-i", str(build / "audio.wav"),
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
         "-movflags", "+faststart", str(out)])
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=False)
    loud = [ln.strip() for ln in r.stderr.splitlines() if re.match(r"\s+(I|Peak):", ln)]
    print(out, f"{duration(out):.2f}s", " ".join(loud[-2:]))
    if args.verify:
        m = whisper()
        for a, b, txt in transcribe(m, out):
            print(f"  {a:6.2f}-{b:6.2f} {txt}")


def cmd_all(args):
    cmd_clips(args, only_missing=True)
    cmd_tts(args)
    cmd_build(args)
    cmd_preview(args)
    cmd_render(args)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s = sub.add_parser("stt")
    s.add_argument("files", nargs="+")
    s.add_argument("--lang", default="tr")
    s = sub.add_parser("still")
    s.add_argument("src")
    s.add_argument("at", type=float)
    s.add_argument("--out")
    s = sub.add_parser("voice")
    s.add_argument("project")
    s.add_argument("key")
    s.add_argument("file")
    for name in ("clips", "tts", "build", "preview", "mix", "render", "all"):
        s = sub.add_parser(name)
        s.add_argument("project")
        s.add_argument("--verify", action="store_true", help="transcribe the result with Whisper")
        if name == "preview":
            s.add_argument("--at", help="comma-separated times in seconds")
        if name == "render":
            s.add_argument("--from", dest="from_sec", type=float, default=0,
                           help="re-render only from this second on (scene timings must be unchanged)")
    args = p.parse_args()
    globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    main()
