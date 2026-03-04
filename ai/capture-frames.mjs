import puppeteer from '/opt/homebrew/lib/node_modules/@modelcontextprotocol/server-puppeteer/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';

const OUTPUT_DIR = '/Users/yonko/Projects/SignalBox/ai/demo-frames-v2';
const URL = 'http://127.0.0.1:8765/dashboard';

// Scroll positions from actual page measurement
const SECTIONS = {
  'F1-hero': 0,
  'F2-projects': 1086, // 1146 - 60 for header
  'F3-signals': 1552, // 1612 - 60
  'F4-pipeline': 2274, // 2334 - 60
  'F5-oracle': 2370, // show pipeline runs + oracle
};

async function main() {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });

  // Wait for data to load
  await page.waitForFunction(() => {
    return document.body.innerText.includes('HEALTHY') || document.body.innerText.includes('CAUTION');
  }, { timeout: 30000 });

  // Extra wait for animations/rendering
  await new Promise(r => setTimeout(r, 3000));

  for (const [name, scrollY] of Object.entries(SECTIONS)) {
    await page.evaluate((y) => window.scrollTo(0, y), scrollY);
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: `${OUTPUT_DIR}/${name}.png` });
    console.log(`${name} captured at scroll ${scrollY}`);
  }

  await browser.close();
  console.log('All dashboard frames captured!');
}

main().catch(e => { console.error(e); process.exit(1); });
