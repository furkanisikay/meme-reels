const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [html, out, fps = '30', dur = '25', only] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(() => document.fonts.ready);
  const times = only ? only.split(',').map(Number) : [...Array(Math.round(+fps * +dur)).keys()].map((i) => i / +fps);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate((t) => window.render(t), times[i]);
    await page.waitForFunction(() => [...document.images].every((im) => im.complete && im.naturalWidth > 0));
    const name = only ? `t${times[i].toFixed(2)}.png` : `f${String(i).padStart(5, '0')}.png`;
    await page.screenshot({ path: path.join(out, name), type: 'png' });
  }
  await browser.close();
})();
