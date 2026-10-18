"""Sound generators for the reel: a phonk-style drum kit and UI/impact effects.

Everything is synthesized from noise and oscillators, so the music bed and the effects
carry no licence. All functions return mono float arrays at SR.
"""

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def hp(x, f):
    return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- drum kit
def kick(dur=0.45):
    n = int(SR * dur)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-t / 0.035)) / SR
    return np.tanh(2.2 * np.sin(ph) * env(n, 0.001, 0.22))


def bass808(freq, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(freq * (1 + 0.6 * np.exp(-t / 0.02))) / SR
    return np.tanh(1.8 * np.sin(ph)) * env(n, 0.004, dur * 0.55)


def clap():
    n = int(SR * 0.25)
    e = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        i = int(off * SR)
        e[i:] += env(n - i, 0.0005, 0.012 if k < 2 else 0.09)
    return bp(rng.standard_normal(n) * e, 900, 5000)


def hat(open_=False):
    n = int(SR * (0.18 if open_ else 0.05))
    return hp(rng.standard_normal(n), 7000) * env(n, 0.0005, 0.06 if open_ else 0.012)


def cowbell(freq, dur=0.16):
    n = int(SR * dur)
    t = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * freq * t)) + 0.8 * np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    return bp(sq, 500, 4000) * env(n, 0.001, 0.07)


# ---------------------------------------------------------------- effects
def whoosh(dur=0.32, up=True):
    n = int(SR * dur)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    steps = 16
    for s in range(steps):
        a, b = s * n // steps, (s + 1) * n // steps
        p = s / (steps - 1)
        fc = 300 * (10 ** (p if up else 1 - p))
        out[a:b] = bp(x, fc * 0.7, min(fc * 1.4, 20000))[a:b]
    return out * np.sin(np.linspace(0, np.pi, n)) ** 2 * 2.2


def fall(dur=1.4):
    return whoosh(dur, up=False)


def boom():
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t / 0.05)) / SR)
    body = np.tanh(3.0 * s * env(n, 0.002, 0.45))
    crack = lp(rng.standard_normal(n), 2500) * env(n, 0.0005, 0.03)
    return 0.9 * body + 0.5 * crack


def hit():
    n = int(SR * 0.4)
    return np.tanh(2 * (0.7 * kick(0.4)[:n] + 0.6 * bp(rng.standard_normal(n), 200, 3000) * env(n, 0.001, 0.05)))


def click():
    n = int(SR * 0.025)
    return bp(rng.standard_normal(n), 1500, 6000) * env(n, 0.0003, 0.004)


def tone(f=880, dur=0.12, d=0.04, harm=(1, 0.3)):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm)) * env(n, 0.002, d)


def ding():
    return tone(1318.5, 0.9, 0.35, (1, 0.5, 0.25)) + 0.6 * tone(1975.5, 0.9, 0.25, (1, 0.5, 0.25))


def beep(f=880, dur=0.12):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * f * t)) * 0.4 * env(n, 0.001, 0.08)


def riser(dur=0.7):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(200 * (12 ** (t / dur))) / SR)
    return (0.5 * s + 0.6 * whoosh(dur, True)[:n]) * (t / dur) ** 2


def sparkle():
    out = np.zeros(int(SR * 0.9))
    for k, f in enumerate((1047, 1319, 1568, 2093)):
        i = int(k * 0.07 * SR)
        s = tone(f, 0.6, 0.2, (1, 0.5, 0.25))
        out[i:i + len(s)] += s[: len(out) - i]
    return out


EFFECTS = {
    "whoosh": whoosh, "fall": fall, "boom": boom, "hit": hit, "click": click, "tone": tone,
    "ding": ding, "beep": beep, "riser": riser, "sparkle": sparkle,
}

# A minor phonk loop: bar = 4 beats; roots and a cowbell riff over two bars
ROOTS = [55.0, 43.65, 49.0, 41.2]
RIFF = [880, 0, 784, 880, 0, 659, 587, 659, 880, 0, 784, 880, 1047, 0, 880, 784]


def phonk(n, bpm=120, muted=lambda t: False, fade_out=0.6, light=lambda t: False):
    """Drum + 808 + cowbell bed of n samples. muted(t) silences a beat, light(t) drops the riff."""
    out = np.zeros(n)
    beat = 60 / bpm
    dur = n / SR

    def put(t, sig, g):
        i = int(t * SR)
        j = min(n, i + len(sig))
        if 0 <= i < n:
            out[i:j] += g * sig[: j - i]

    for b in range(int(dur / beat) + 1):
        t = b * beat
        if muted(t):
            continue
        m = 1.0 if t < dur - fade_out else max(0.0, (dur - t) / fade_out)
        bib, bar = b % 4, b // 4
        if bib in (0, 2) or (bib == 1 and bar % 2 == 1):
            put(t, kick(), 0.9 * m)
        if bib == 0:
            # cut the 808 tail at the next muted window so silence stays silent
            ln = 4 * beat - 0.1
            for k in range(1, int(ln / 0.05)):
                if muted(t + k * 0.05):
                    ln = k * 0.05
                    break
            put(t, bass808(ROOTS[bar % 4], ln), 0.55 * m)
        if bib in (1, 3):
            put(t, clap(), 0.45 * m)
        for k in range(4):
            put(t + k * beat / 4 + (0.012 if k % 2 else 0), hat(open_=(k == 2 and bib == 3)), (0.16 if k % 2 else 0.24) * m)
        if not light(t):
            for k in range(2):
                f = RIFF[(b * 2 + k) % len(RIFF)]
                if f:
                    put(t + k * beat / 2, cowbell(f), 0.2 * m)
    return out
