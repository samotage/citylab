import { chromium } from 'playwright';

const OUT = 'output/maren/site-captures';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 430, height: 932 } });

await page.goto('https://power-your-grid.base44.app/', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(8000);

// Home viewport
await page.screenshot({ path: `${OUT}/app-home.png` });

// Scroll down to assets section
await page.evaluate(() => window.scrollTo(0, 600));
await page.waitForTimeout(1500);
await page.screenshot({ path: `${OUT}/app-home-assets.png` });

// Scroll to very bottom
await page.evaluate(() => window.scrollTo(0, 99999));
await page.waitForTimeout(1500);
await page.screenshot({ path: `${OUT}/app-home-bottom.png` });

// Back to top and click tabs
await page.evaluate(() => window.scrollTo(0, 0));
await page.waitForTimeout(500);

const tabs = ['Follow Me', 'Earnings', 'My Pod', 'Settings'];
for (const tab of tabs) {
  try {
    const btn = page.locator(`nav >> text="${tab}"`).first();
    if (await btn.isVisible({ timeout: 2000 })) {
      await btn.click();
      await page.waitForTimeout(4000);
      const slug = tab.toLowerCase().replace(/\s+/g, '-');
      await page.screenshot({ path: `${OUT}/app-${slug}.png` });
      // full page too
      await page.screenshot({ path: `${OUT}/app-${slug}-full.png`, fullPage: true });
      console.log(`Captured: ${tab}`);
    } else {
      console.log(`Tab not visible: ${tab}`);
    }
  } catch (e) {
    console.log(`Failed ${tab}: ${e.message}`);
  }
}

await browser.close();
console.log('Done.');
