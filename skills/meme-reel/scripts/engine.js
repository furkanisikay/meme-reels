// Reel engine: deterministic render(t) for a 1080x1920 page, driven by SC (scenes from
// timeline.json). Generic parts live here; each project adds FX[sceneId](ctx) for its own
// animated scenes. Captured frame by frame by capture.js, so never use timers or Date.
const $ = (id) => document.getElementById(id);
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const easeOut = (p) => 1 - Math.pow(1 - p, 3);
const easeInOut = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
const back = (p) => { const c = 1.9; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
const lerp = (a, b, p) => a + (b - a) * p;
function interp(arr, t) {
  if (t <= arr[0][0]) return arr[0][1];
  for (let i = 1; i < arr.length; i++) if (arr[i][0] >= t) {
    const [t0, v0] = arr[i - 1], [t1, v1] = arr[i];
    return v0 + (v1 - v0) * (t - t0) / (t1 - t0);
  }
  return arr[arr.length - 1][1];
}
// fade + rise an element in at local time a
function pop(el, lt, a, dur = 0.3, dy = 40) {
  if (!el) return;
  const p = easeOut(seg(lt, a, a + dur));
  el.style.opacity = p;
  el.style.transform = `translateY(${(1 - p) * dy}px) scale(${0.94 + 0.06 * p})`;
}
// overshoot scale-in (badges, stamps)
function stamp(el, lt, a, base = '') {
  if (!el) return;
  el.style.opacity = seg(lt, a, a + 0.08);
  el.style.transform = `${base} scale(${clamp(back(seg(lt, a, a + 0.3)), 0, 1.2)})`;
}
// type text into el between local times a and b
function type(el, text, lt, a, b) {
  if (el) el.textContent = text.slice(0, Math.round(text.length * seg(lt, a, b)));
}
const FX = {};

// subtitle chunks: at most 3 words; break at pauses and sentence punctuation
for (const s of SC) {
  if (!s.words) continue;
  s.chunks = [];
  let cur = [];
  s.words.forEach((w, i) => {
    cur.push(w);
    const nx = s.words[i + 1], pause = nx && nx[0] - w[1] > 0.2;
    if (cur.length === 3 || pause || /[.,:?!]$/.test(w[2])) { s.chunks.push(cur); cur = []; }
  });
  if (cur.length) s.chunks.push(cur);
}

function subtitle(s, t) {
  const el = $('sub');
  if (!s || !s.chunks || s.nosub) { el.textContent = ''; return; }
  let ch = s.chunks[0];
  for (const c of s.chunks) if (t >= c[0][0] - 0.05) ch = c;
  el.textContent = '';
  for (const w of ch) {
    const sp = document.createElement('span');
    const p = easeOut(seg(t, w[0], w[0] + 0.12));
    if (t >= w[0] && t < w[1] + 0.05) sp.className = 'on';
    sp.style.opacity = t >= w[0] - 0.02 ? 1 : 0.6;
    sp.style.transform = `scale(${(t >= w[0] ? 1 + 0.12 * (1 - p) : 1).toFixed(3)})`;
    sp.textContent = w[2].replace(/[.,]$/, '');
    el.appendChild(sp);
    el.appendChild(document.createTextNode(' '));
  }
}

function render(t) {
  let active = null;
  for (const s of SC) {
    const el = $(s.id);
    const on = t >= s.a && t < s.b;
    el.style.visibility = on ? 'visible' : 'hidden';
    if (!on) continue;
    active = s;
    const lt = t - s.a, d = s.b - s.a;
    // hard cut + punch-in at each scene start; the opener starts mid-action, no punch
    const punch = s.a === 0 ? 1 : 1 + 0.06 * (1 - easeOut(seg(lt, 0, 0.25)));
    el.style.transform = `scale(${punch})`;
    const c = $(s.id + 'c');
    if (c) c.style.transform = `scale(${clamp(back(seg(lt, 0, 0.3)), 0, 1.15)})`;

    if (s.clip) {
      const idx = Math.min(s.frames, Math.floor(lt * FPS) + 1);
      const img = $(s.id + 'i');
      img.src = `mm/${s.clip}/${String(idx).padStart(4, '0')}.jpg`;
      img.style.transform = `scale(${1 + 0.05 * lt / d})`;  // slow push-in keeps 288p sources alive
      pop($(s.id + 'q'), lt, 0.05, 0.2, 20);
    }
    // local time of the first shown word starting with prefix (case-insensitive)
    const word = (prefix, dflt = 0) => {
      const w = (s.words || []).find((x) => x[2].toLocaleLowerCase('tr').startsWith(prefix.toLocaleLowerCase('tr')));
      return w ? w[0] - s.a : dflt;
    };
    if (FX[s.id]) FX[s.id]({ s, el, t, lt, d, punch, word });
  }
  subtitle(active && !active.clip ? active : null, t);
}
window.render = render;
