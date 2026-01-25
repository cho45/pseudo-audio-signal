import { test, expect, Page } from '@playwright/test';

test.describe('疑似音声発生器', () => {
  /**
   * UIから現在のRMS値（平均）を取得するヘルパー
   */
  async function getRMS(page: Page): Promise<number> {
      const text = await page.locator('.rms-highlight').textContent();
      // "RMS: 0.10000 (avg)" のような形式から数値を抽出
      const match = text?.match(/RMS:\s*([\d.]+)/);
      return match ? parseFloat(match[1]) : 0;
  }

  /**
   * 指定した時間待機してRMSが安定するのを待つ
   */
  async function waitAudioStable(page: Page, seconds: number = 2) {
      await page.waitForTimeout(seconds * 1000);
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('ページが正常に読み込まれる', async ({ page }) => {
    await expect(page).toHaveTitle(/ITU-T G.227/);
    await expect(page.locator('.toggle-btn')).toBeVisible();
    await expect(page.locator('.toggle-btn')).toHaveText('Start');
  });

  test('Start/Stopボタンのトグル', async ({ page }) => {
    const btn = page.locator('.toggle-btn');

    // 初期状態: Start
    await expect(btn).toHaveText('Start');
    await expect(btn).not.toHaveClass(/active/);

    // クリックで Start → Stop
    await btn.click();
    await expect(btn).toHaveText('Stop');
    await expect(btn).toHaveClass(/active/);

    // もう一度クリックで Stop → Start
    await btn.click();
    await expect(btn).toHaveText('Start');
    await expect(btn).not.toHaveClass(/active/);
  });

  test('キーボード: Spaceで再生/停止', async ({ page }) => {
    const btn = page.locator('.toggle-btn');

    await expect(btn).toHaveText('Start');

    await page.keyboard.press('Space');
    await expect(btn).toHaveText('Stop');

    await page.keyboard.press('Space');
    await expect(btn).toHaveText('Start');
  });

  test('キーボード: 数字キーで音源切り替え', async ({ page }) => {
    // 初期状態: 疑似音声
    await expect(page.locator('input[value="pseudoAudio"]')).toBeChecked();

    // 2: ホワイトノイズ
    await page.keyboard.press('Digit2');
    await expect(page.locator('input[value="whitenoise"]')).toBeChecked();

    // 3: 1000Hz
    await page.keyboard.press('Digit3');
    await expect(page.locator('input[value="sine1000Hz"]')).toBeChecked();

    // 4: 1500Hz
    await page.keyboard.press('Digit4');
    await expect(page.locator('input[value="sine1500Hz"]')).toBeChecked();

    // 5: カスタム
    await page.keyboard.press('Digit5');
    await expect(page.locator('input[value="sineCustom"]')).toBeChecked();

    // 1: 疑似音声に戻る
    await page.keyboard.press('Digit1');
    await expect(page.locator('input[value="pseudoAudio"]')).toBeChecked();
  });

  test('キーボード: O/+で+10dBオフセット切り替え', async ({ page }) => {
    const checkbox = page.locator('#offset10dB');

    await expect(checkbox).not.toBeChecked();

    await page.keyboard.press('KeyO');
    await expect(checkbox).toBeChecked();

    await page.keyboard.press('KeyO');
    await expect(checkbox).not.toBeChecked();

    // + キーでも同様
    await page.keyboard.press('Equal');
    await expect(checkbox).toBeChecked();
  });

  test('キーボード: 矢印キーでゲイン調整', async ({ page }) => {
    const gainInput = page.locator('#gainValue');

    // 初期値: -20
    await expect(gainInput).toHaveValue('-20');

    // 上矢印: +1
    await page.keyboard.press('ArrowUp');
    await expect(gainInput).toHaveValue('-19');

    // 下矢印: -1
    await page.keyboard.press('ArrowDown');
    await expect(gainInput).toHaveValue('-20');
  });

  test('ラジオボタンクリックで音源切り替え', async ({ page }) => {
    await page.locator('input[value="whitenoise"]').check();
    await expect(page.locator('input[value="whitenoise"]')).toBeChecked();

    await page.locator('input[value="sine1000Hz"]').check();
    await expect(page.locator('input[value="sine1000Hz"]')).toBeChecked();
  });

  test('カスタム周波数入力フィールドの表示/非表示', async ({ page }) => {
    const customFreqInput = page.locator('.custom-freq-input');

    // 初期状態では非表示
    await expect(customFreqInput).not.toBeVisible();

    // カスタム正弦波を選択すると表示
    await page.locator('input[value="sineCustom"]').check();
    await expect(customFreqInput).toBeVisible();

    // 別の音源を選択すると非表示
    await page.locator('input[value="pseudoAudio"]').check();
    await expect(customFreqInput).not.toBeVisible();
  });

  test('入力フィールドにフォーカス中はキーボードショートカット無効', async ({ page }) => {
    const gainInput = page.locator('#gainValue');

    // フォーカスしていない状態で2を押すとホワイトノイズに切り替わる
    await page.keyboard.press('Digit2');
    await expect(page.locator('input[value="whitenoise"]')).toBeChecked();

    // 疑似音声に戻す
    await page.keyboard.press('Digit1');

    // フォーカス中は切り替わらない
    await gainInput.focus();
    await page.keyboard.press('Digit2');
    await expect(page.locator('input[value="pseudoAudio"]')).toBeChecked();
  });

  test.describe('音響特性の検証 (RMSレベル)', () => {
    test.beforeEach(async ({ page }) => {
      // 全てのテストで音声をスタートさせる
      await page.locator('.toggle-btn').click();
    });

    test('正弦波 (1000Hz, -20dB) のRMS値が約0.1であること', async ({ page }) => {
      await page.locator('input[value="sine1000Hz"]').check();
      await waitAudioStable(page, 3);
      const rms = await getRMS(page);
      // 正弦波は安定しているため、誤差は小さめに見積もる
      expect(rms).toBeCloseTo(0.1, 3);
    });

    test('ホワイトノイズ (-20dB) のRMS値が約0.1であること', async ({ page }) => {
      await page.locator('input[value="whitenoise"]').check();
      await waitAudioStable(page, 3); // ノイズは平均化に時間がかかるため長めに待機
      const rms = await getRMS(page);
      // ノイズの統計的性質を考慮し、±10%程度の誤差を許容
      expect(rms).toBeGreaterThan(0.09);
      expect(rms).toBeLessThan(0.11);
    });

    test('疑似音声 (-20dB) のRMS値が約0.1であること', async ({ page }) => {
      await page.locator('input[value="pseudoAudio"]').check();
      await waitAudioStable(page, 3);
      const rms = await getRMS(page);
      // 疑似音声もノイズベースなので誤差を許容
      expect(rms).toBeGreaterThan(0.09);
      expect(rms).toBeLessThan(0.11);
    });

    test('+10dBオフセットが正しく適用されること', async ({ page }) => {
      await page.locator('input[value="sine1000Hz"]').check();
      await page.locator('#offset10dB').check();
      await waitAudioStable(page, 5); // 窓幅120フレーム（約2秒）が確実に埋まるよう十分に待機
      const rms = await getRMS(page);
      // 0.1 * 10^(10/20) = 0.1 * 3.162277... = 0.3162277...
      expect(rms).toBeCloseTo(0.3162, 3);
    });
  });
});
