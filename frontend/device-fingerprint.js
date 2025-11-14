/**
 * Device Fingerprinting System
 * Uses multiple techniques to create unique device identifier
 * Resistant to incognito mode and different browsers on same device
 */

class DeviceFingerprint {
    constructor() {
        this.fingerprint = null;
    }

    /**
     * Generate canvas fingerprint
     */
    getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Draw complex pattern
            canvas.width = 200;
            canvas.height = 50;

            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.textBaseline = 'alphabetic';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('TapToLook.net 🎨', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('TapToLook.net 🎨', 4, 17);

            return canvas.toDataURL();
        } catch (e) {
            return 'canvas_error';
        }
    }

    /**
     * Generate WebGL fingerprint
     */
    getWebGLFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

            if (!gl) return 'webgl_not_supported';

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);

            return `${vendor}~${renderer}`;
        } catch (e) {
            return 'webgl_error';
        }
    }

    /**
     * Get screen and browser info
     */
    getScreenInfo() {
        return {
            screenResolution: `${screen.width}x${screen.height}`,
            screenDepth: screen.colorDepth,
            screenAvail: `${screen.availWidth}x${screen.availHeight}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            language: navigator.language,
            languages: navigator.languages.join(','),
            platform: navigator.platform,
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            deviceMemory: navigator.deviceMemory || 0,
            maxTouchPoints: navigator.maxTouchPoints || 0
        };
    }

    /**
     * Get fonts fingerprint
     */
    getFontsFingerprint() {
        const testFonts = [
            'Arial', 'Verdana', 'Times New Roman', 'Courier New',
            'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS',
            'Trebuchet MS', 'Impact', 'Lucida Console'
        ];

        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        const baseWidths = {};
        baseFonts.forEach(baseFont => {
            ctx.font = `${testSize} ${baseFont}`;
            baseWidths[baseFont] = ctx.measureText(testString).width;
        });

        const detectedFonts = [];
        testFonts.forEach(font => {
            baseFonts.forEach(baseFont => {
                ctx.font = `${testSize} ${font}, ${baseFont}`;
                const width = ctx.measureText(testString).width;
                if (width !== baseWidths[baseFont]) {
                    if (!detectedFonts.includes(font)) {
                        detectedFonts.push(font);
                    }
                }
            });
        });

        return detectedFonts.join(',');
    }

    /**
     * Get audio fingerprint
     */
    async getAudioFingerprint() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return 'audio_not_supported';

            const context = new AudioContext();
            const oscillator = context.createOscillator();
            const analyser = context.createAnalyser();
            const gainNode = context.createGain();
            const scriptProcessor = context.createScriptProcessor(4096, 1, 1);

            gainNode.gain.value = 0; // Mute
            oscillator.type = 'triangle';
            oscillator.frequency.value = 10000;

            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gainNode);
            gainNode.connect(context.destination);

            oscillator.start(0);

            return new Promise((resolve) => {
                scriptProcessor.onaudioprocess = function(event) {
                    const output = event.outputBuffer.getChannelData(0);
                    let sum = 0;
                    for (let i = 0; i < output.length; i++) {
                        sum += Math.abs(output[i]);
                    }

                    oscillator.stop();
                    scriptProcessor.disconnect();
                    oscillator.disconnect();
                    analyser.disconnect();
                    gainNode.disconnect();

                    resolve(sum.toString());
                };
            });
        } catch (e) {
            return 'audio_error';
        }
    }

    /**
     * Get plugins info
     */
    getPluginsInfo() {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push(navigator.plugins[i].name);
        }
        return plugins.join(',');
    }

    /**
     * Simple hash function
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(36);
    }

    /**
     * Generate complete device fingerprint
     */
    async generate() {
        try {
            console.log('[FINGERPRINT] Generating device fingerprint...');

            // Collect all fingerprint components
            const canvas = this.getCanvasFingerprint();
            const webgl = this.getWebGLFingerprint();
            const screen = this.getScreenInfo();
            const fonts = this.getFontsFingerprint();
            const audio = await this.getAudioFingerprint();
            const plugins = this.getPluginsInfo();

            // Combine all data
            const fingerprintData = {
                canvas: this.simpleHash(canvas),
                webgl: this.simpleHash(webgl),
                screen: this.simpleHash(JSON.stringify(screen)),
                fonts: this.simpleHash(fonts),
                audio: this.simpleHash(audio),
                plugins: this.simpleHash(plugins),
                userAgent: this.simpleHash(navigator.userAgent)
            };

            // Create final fingerprint hash
            const combinedString = Object.values(fingerprintData).join('|');
            this.fingerprint = this.simpleHash(combinedString);

            console.log('[FINGERPRINT] Generated:', this.fingerprint);
            console.log('[FINGERPRINT] Components:', fingerprintData);

            return this.fingerprint;
        } catch (error) {
            console.error('[FINGERPRINT] Error generating fingerprint:', error);
            // Fallback to simpler fingerprint
            const fallback = this.simpleHash(
                navigator.userAgent +
                screen.width +
                screen.height +
                navigator.language
            );
            this.fingerprint = fallback;
            return fallback;
        }
    }

    /**
     * Get cached fingerprint or generate new one
     */
    async get() {
        if (this.fingerprint) {
            return this.fingerprint;
        }
        return await this.generate();
    }
}

// Create global instance
window.deviceFingerprint = new DeviceFingerprint();
