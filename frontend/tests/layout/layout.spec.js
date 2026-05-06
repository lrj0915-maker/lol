import { test, expect } from '@playwright/test'

const sizes = [
  { name: '1000x700', width: 1000, height: 700 },
  { name: '1200x800', width: 1200, height: 800 },
  { name: '1440x900', width: 1440, height: 900 },
]

for (const size of sizes) {
  test(`Runes layout no overlap @ ${size.name}`, async ({ page }) => {
    await page.setViewportSize({ width: size.width, height: size.height })
    await page.goto('/#/runes')

    const toolbar = page.locator('.toolbar-controls').first()
    await expect(toolbar).toBeVisible()

    const roles = page.locator('.roles-group').first()
    const actions = page.locator('.actions-group').first()
    await expect(roles).toBeVisible()
    await expect(actions).toBeVisible()

    const roleBox = await roles.boundingBox()
    const actionBox = await actions.boundingBox()
    expect(roleBox).toBeTruthy()
    expect(actionBox).toBeTruthy()
    expect(actionBox.y).toBeGreaterThanOrEqual(roleBox.y)
  })

  test(`Augments layout no overlap @ ${size.name}`, async ({ page }) => {
    await page.setViewportSize({ width: size.width, height: size.height })
    await page.goto('/#/augments')

    const content = page.locator('.content-grid').first()
    const tierBlock = page.locator('.tier-block').first()
    await expect(content).toBeVisible()
    await expect(tierBlock).toBeVisible()

    const cards = page.locator('.aug-card')
    if (await cards.count()) {
      const first = await cards.nth(0).boundingBox()
      const second = (await cards.count()) > 1 ? await cards.nth(1).boundingBox() : null
      if (first && second) {
        expect(second.y).toBeGreaterThanOrEqual(first.y)
      }
    }
  })
}

