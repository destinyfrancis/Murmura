import { expect, test } from '@playwright/test'

async function mockHealth(page) {
  await page.route('**/api/health', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'ok',
        capabilities: { simulation: true },
      }),
    })
  })
  await page.route('**/api/settings', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: {} }),
    })
  })
  await page.route('**/api/domain-packs', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ packs: [] }),
    })
  })
}

test.describe('Process smoke', () => {
  test.beforeEach(async ({ page }) => {
    await mockHealth(page)
  })

  for (const viewport of [
    { name: 'desktop', width: 1440, height: 960 },
    { name: 'mobile', width: 390, height: 844 },
  ]) {
    test(`renders /process/quick on ${viewport.name}`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/process/quick')

      await expect(page.locator('.nav-brand')).toHaveText('Murmura')
      await expect(page.locator('body')).not.toContainText(/MORAI|Morai|MurmuraScope/)
      await page.screenshot({
        path: testInfo.outputPath(`process-${viewport.name}.png`),
        fullPage: true,
      })
    })
  }
})

test.describe('Brand and i18n sanity', () => {
  test.beforeEach(async ({ page }) => {
    await mockHealth(page)
  })

  test('landing page follows English locale', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('murmura_locale', 'en-US'))
    await page.goto('/landing')

    await expect(page.locator('.nav-logo')).toHaveText('Murmura')
    await expect(page.getByRole('button', { name: /Launch Engine/ }).first()).toBeVisible()
    await expect(page.locator('body')).not.toContainText(/MORAI|Morai|MurmuraScope/)
  })

  test('home page follows Traditional Chinese locale', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('murmura_locale', 'zh-TW'))
    await page.goto('/')

    await expect(page.getByRole('heading', { name: 'Murmura' })).toBeVisible()
    await expect(page.locator('.hero-subtitle')).toHaveText('通用預測引擎')
    await expect(page.locator('body')).not.toContainText(/MORAI|Morai|MurmuraScope/)
  })
})
