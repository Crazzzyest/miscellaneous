import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const filePath = 'file://' + path.join(__dirname, 'athenian_house.html');

const browser = await puppeteer.launch({
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  headless: true
});
const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 800, deviceScaleFactor: 2 });
await page.goto(filePath, { waitUntil: 'networkidle0', timeout: 30000 });
// Let Three.js render a few frames
await new Promise(r => setTimeout(r, 3000));
await page.screenshot({ path: 'athenian_house_screenshot.png', fullPage: false });
await browser.close();
console.log('done');
