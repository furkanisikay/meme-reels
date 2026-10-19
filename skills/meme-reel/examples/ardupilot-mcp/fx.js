// Per-scene animation for the ardupilot-mcp reel. Each FX[id] gets
// { s, el, t, lt, d, punch, word } and must only depend on those (deterministic frames).

// a: drone falls along the real SITL altitude/roll series, impact lands on "düştü"
FX.a = ({ el, t, lt, punch, word }) => {
  const V1 = word('düştü', 1.4) + 0.1;
  const rt = lerp(347.45, 352.9, seg(lt, 0, V1));
  const alt = Math.max(0, interp(ALT, rt));
  const landed = lt >= V1;
  const x = lerp(250, 830, seg(lt, 0, V1));
  const y = 900 - 30 - (alt / 20) * 700;
  const shake = landed ? Math.sin(lt * 90) * 22 * (1 - seg(lt, V1, V1 + 0.45)) : 0;
  $('drone').setAttribute('transform', `translate(${x + shake},${y}) rotate(${landed ? -24 : interp(ROLL, rt)}) scale(2.1)`);
  $('drone').querySelectorAll('.prop').forEach((p, i) => p.setAttribute('ry', landed ? 5 : 4 + 3 * Math.abs(Math.sin(t * 40 + i))));
  let path = '';
  for (let k = 0; k <= 50; k++) {
    const tk = (Math.min(lt, V1) * k) / 50;
    const ak = Math.max(0, interp(ALT, lerp(347.45, 352.9, seg(tk, 0, V1))));
    path += (k ? 'L' : 'M') + lerp(250, 830, seg(tk, 0, V1)).toFixed(1) + ',' + (900 - 30 - (ak / 20) * 700).toFixed(1);
  }
  $('trail').setAttribute('d', path);
  $('boom').setAttribute('opacity', landed ? 1 - seg(lt, V1 + 0.1, V1 + 0.6) : 0);
  $('flash').style.opacity = landed ? 0.85 * (1 - seg(lt, V1, V1 + 0.15)) : 0;
  $('altv').textContent = alt.toFixed(1) + ' m';
  el.style.transform = `scale(${punch}) translate(${shake * 0.6}px, ${shake * 0.3}px)`;
};

// b: raw log scrolls, record counter rolls up while "bir milyon..." is spoken
FX.b = ({ lt, d, word }) => {
  const c0 = word('bir', 2.2), c1 = d - 0.4;
  $('cnt').textContent = Math.round(1558457 * easeOut(seg(lt, c0, c1))).toLocaleString('tr-TR');
  const target = NEEDLE * 46 - 900;
  $('rawin').style.transform = `translateY(${-(easeInOut(seg(lt, 0, c1)) * target)}px)`;
  const hp = seg(lt, c1 - 0.1, c1 + 0.15);
  const nd = document.querySelector('.needle');
  nd.style.background = `rgba(244,63,94,${0.25 * hp})`;
  nd.querySelector('b').style.color = hp > 0 ? '#F43F5E' : '';
  nd.querySelector('b').style.transform = `scale(${1 + 0.4 * easeOut(hp)})`;
};

// c: file attached, question typed, the tool runs its 18 checks
FX.c = ({ lt, d }) => {
  pop($('cfile'), lt, 0.05, 0.25);
  pop($('cme'), lt, 0.35, 0.25);
  type($('ctype'), 'Bu drone neden düştü?', lt, 0.4, 1.3);
  document.querySelector('.k-chat .caret').style.opacity = lt < 1.4 && Math.floor(lt * 5) % 2 === 0 ? 1 : 0;
  pop($('ctool'), lt, 1.45, 0.25);
  const pb = seg(lt, 1.6, d - 0.5);
  $('cbar').style.width = (pb * 100).toFixed(1) + '%';
  $('ctxt').textContent = pb < 1 ? `${Math.max(1, Math.round(18 * pb))}/18 kontrol…` : '18 kontrol · 3 kritik bulgu';
  $('ctxt').style.color = pb < 1 ? '' : '#FDA4B4';
};

// d: motor outputs move from hover (59%) to the logged values; motor 2 pinned at 95%
FX.d = ({ t, lt, d, word }) => {
  const tm = word('motor', 0.5), ty = word('yetme', d - 1.2);
  pop($('mhead'), lt, tm, 0.3, 30);
  const fin = { 1: 0.522, 2: 0.95, 3: 0.557, 4: 0.557 };
  const pr = easeInOut(seg(lt, 0.1, tm + 1.2));
  for (const m of [1, 2, 3, 4]) {
    const v = lerp(0.591, fin[m], pr);
    const ring = $('ring' + m), circ = parseFloat(ring.dataset.circ);
    ring.setAttribute('stroke-dasharray', `${(v * circ).toFixed(1)} ${circ}`);
    const hot = m === 2 && lt >= tm;
    const col = hot ? '#F43F5E' : '#38BDF8';
    ring.setAttribute('stroke', col); $('hub' + m).setAttribute('stroke', col); $('num' + m).setAttribute('fill', col);
    $('p' + m).textContent = '%' + Math.round(v * 100);
    $('p' + m).style.color = hot ? '#F43F5E' : '#7DD3FC';
    $('p' + m).style.fontSize = hot ? '84px' : '48px';
  }
  const bp = (lt % 0.5) / 0.5;
  $('glow2').setAttribute('opacity', lt >= tm ? 0.5 + 0.5 * Math.max(0, 1 - bp * 2.5) : 0);
  document.querySelectorAll('.blades').forEach((g) => g.setAttribute('transform', `rotate(${(t * 900 * g.dataset.dir) % 360} ${g.dataset.cx} ${g.dataset.cy})`));
  stamp($('tag2'), lt, ty, 'translateX(-50%)');
};

// e: install command, then one badge per spoken word
FX.e = ({ lt, word }) => {
  pop($('term'), lt, 0.0, 0.2);
  type($('tcmd'), 'pip install ardupilot-mcp', lt, 0.1, 0.8);
  document.querySelector('.k-cta .caret').style.opacity = lt < 0.9 && Math.floor(lt * 5) % 2 === 0 ? 1 : 0;
  pop($('tok'), lt, 0.9, 0.2, 10);
  pop($('bd1'), lt, word('ücretsiz', 0.2), 0.25, 30);
  pop($('bd2'), lt, word('açık', 1.2), 0.25, 30);
  pop($('bd3'), lt, word('kaynak', 1.6) + 0.45, 0.25, 30);
};

// f: the fixed drone lifts off; link arrow lands on "Link"
FX.f = ({ t, lt, word }) => {
  const lift = easeOut(seg(lt, 0.0, 1.1));
  const y = lerp(820, 600, lift) + Math.sin(lt * 3.2) * 10 * lift;
  $('okdrone').setAttribute('transform', `translate(540,${y}) rotate(${Math.sin(lt * 2.1) * 3}) scale(2.4)`);
  $('okdrone').querySelectorAll('.prop').forEach((p, i) => p.setAttribute('ry', 4 + 3 * Math.abs(Math.sin(t * 40 + i))));
  $('okg').setAttribute('cy', y); $('okg').setAttribute('opacity', 0.6 * lift);
  $('okbadge').setAttribute('opacity', seg(lt, 0.8, 0.9));
  $('okbadge').setAttribute('transform', `translate(720,${y - 130}) scale(${clamp(back(seg(lt, 0.8, 1.1)), 0, 1.3)})`);
  pop($('pill'), lt, 0.5, 0.3);
  const ta = word('link', 1.6);
  pop($('arrow'), lt, ta, 0.3);
  if (lt > ta + 0.3) $('arrow').style.transform = `translateY(${Math.abs(Math.sin((lt - ta - 0.3) * 6)) * 18}px)`;
};
