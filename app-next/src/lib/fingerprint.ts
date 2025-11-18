import FingerprintJS from '@fingerprintjs/fingerprintjs';

let fpPromise: Promise<string> | null = null;

/**
 * Получить device fingerprint для идентификации анонимных пользователей.
 * Результат кешируется для повторного использования.
 */
export async function getDeviceFingerprint(): Promise<string> {
  if (!fpPromise) {
    fpPromise = (async () => {
      try {
        const fp = await FingerprintJS.load();
        const result = await fp.get();
        return result.visitorId;
      } catch (error) {
        console.error('Failed to generate fingerprint:', error);
        // Fallback: генерируем простой ID на основе navigator
        const fallback = `fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        return fallback;
      }
    })();
  }

  return fpPromise;
}
