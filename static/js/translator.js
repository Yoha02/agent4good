/**
 * Multi-Language Translation System
 * Powered by Google Cloud Translation API
 */

class PageTranslator {
    constructor() {
        this.currentLanguage = localStorage.getItem('preferredLanguage') || 'en';
        this.supportedLanguages = [];
        this.translationCache = {};
        this.isTranslating = false;
        this.originalTexts = new Map(); // Store original texts before translation
        
        // Popular languages to show first
        this.popularLanguages = ['en', 'es', 'fr', 'de', 'zh-CN', 'ja', 'ko', 'ar', 'hi', 'pt', 'ru', 'it'];
    }

    /**
     * Initialize the translator
     */
    async init() {
        try {
            // Load supported languages
            await this.loadSupportedLanguages();
            
            // Create language selector UI
            this.createLanguageSelector();
            
            // If user has a saved preference and it's not English, translate
            if (this.currentLanguage !== 'en') {
                await this.translatePage(this.currentLanguage);
            }
            
            console.log('[Translator] Initialized successfully');
        } catch (error) {
            console.error('[Translator] Initialization failed:', error);
        }
    }

    /**
     * Load supported languages from API
     */
    async loadSupportedLanguages() {
        try {
            const response = await fetch('/api/languages?target=en');
            const data = await response.json();
            
            if (data.success) {
                this.supportedLanguages = data.languages;
                console.log(`[Translator] Loaded ${data.count} languages`);
            }
        } catch (error) {
            console.error('[Translator] Failed to load languages:', error);
            // Fallback to common languages
            this.supportedLanguages = [
                { code: 'en', name: 'English' },
                { code: 'es', name: 'Spanish' },
                { code: 'fr', name: 'French' },
                { code: 'de', name: 'German' },
                { code: 'zh-CN', name: 'Chinese (Simplified)' },
                { code: 'ja', name: 'Japanese' },
                { code: 'ko', name: 'Korean' },
                { code: 'ar', name: 'Arabic' },
                { code: 'hi', name: 'Hindi' },
                { code: 'pt', name: 'Portuguese' }
            ];
        }
    }

    /**
     * Create the language selector dropdown UI
     */
    createLanguageSelector() {
        // Try to find navbar first, fallback to body
        const navbar = document.querySelector('nav') || document.querySelector('.navbar');
        
        if (navbar) {
            this.createNavbarLanguageSelector(navbar);
        } else {
            // Fallback: create standalone selector
            this.createStandaloneLanguageSelector();
        }
    }

    /**
     * Create language selector integrated into navbar
     */
    createNavbarLanguageSelector(navbar) {
        // Find the button container in navbar (usually has the CTA buttons)
        const buttonContainer = navbar.querySelector('.hidden.md\\:flex.space-x-4') || 
                               navbar.querySelector('[class*="space-x"]');
        
        if (!buttonContainer) {
            console.warn('[Translator] Could not find navbar button container, using standalone');
            this.createStandaloneLanguageSelector();
            return;
        }

        // Create language selector button (globe icon)
        const languageButton = document.createElement('div');
        languageButton.id = 'language-selector-container';
        languageButton.className = 'relative';
        languageButton.style.cssText = `
            display: inline-block;
        `;

        // Create globe button
        const globeButton = document.createElement('button');
        globeButton.id = 'language-globe-button';
        globeButton.className = 'bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 flex items-center space-x-2';
        globeButton.innerHTML = `
            <i class="fas fa-globe"></i>
            <i class="fas fa-chevron-down text-xs"></i>
        `;
        globeButton.style.cssText = `
            cursor: pointer;
            position: relative;
        `;

        // Create dropdown menu
        const dropdown = document.createElement('div');
        dropdown.id = 'language-dropdown';
        dropdown.style.cssText = `
            display: none;
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            background: rgba(26, 58, 82, 0.98);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            min-width: 200px;
            max-height: 400px;
            overflow-y: auto;
            z-index: 9999;
        `;

        // Add label
        const label = document.createElement('div');
        label.style.cssText = `
            color: #10b981;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        `;
        label.textContent = 'Select Language';

        // Create select element
        const select = document.createElement('select');
        select.id = 'language-selector';
        select.style.cssText = `
            width: 100%;
            padding: 10px 12px;
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.95);
            color: #1a3a52;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif;
            outline: none;
        `;

        // Sort and add language options
        const sortedLanguages = this.getSortedLanguages();
        sortedLanguages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.code;
            option.textContent = lang.name;
            if (lang.code === this.currentLanguage) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        // Add focus styles
        select.onfocus = () => {
            select.style.borderColor = '#10b981';
            select.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
        };
        select.onblur = () => {
            select.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            select.style.boxShadow = 'none';
        };

        // Add change event listener
        select.addEventListener('change', async (e) => {
            const newLanguage = e.target.value;
            dropdown.style.display = 'none';
            await this.changeLanguage(newLanguage);
        });

        // Toggle dropdown on button click
        globeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!languageButton.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Assemble the dropdown
        dropdown.appendChild(label);
        dropdown.appendChild(select);
        
        // Assemble the language selector
        languageButton.appendChild(globeButton);
        languageButton.appendChild(dropdown);
        
        // Insert before the last button (or at the end)
        buttonContainer.appendChild(languageButton);

        console.log('[Translator] Language selector added to navbar');
    }

    /**
     * Create standalone language selector (fallback)
     */
    createStandaloneLanguageSelector() {
        const container = document.createElement('div');
        container.id = 'language-selector-container';
        container.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            background: rgba(26, 58, 82, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        `;

        const label = document.createElement('label');
        label.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            color: #10b981;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
        `;
        label.innerHTML = '<i class="fas fa-globe" style="font-size: 14px;"></i> Language';

        const select = document.createElement('select');
        select.id = 'language-selector';
        select.style.cssText = `
            width: 100%;
            padding: 10px 12px;
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.95);
            color: #1a3a52;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif;
            min-width: 180px;
            outline: none;
        `;

        const sortedLanguages = this.getSortedLanguages();
        sortedLanguages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.code;
            option.textContent = lang.name;
            if (lang.code === this.currentLanguage) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        select.addEventListener('change', async (e) => {
            const newLanguage = e.target.value;
            await this.changeLanguage(newLanguage);
        });

        container.appendChild(label);
        container.appendChild(select);
        document.body.appendChild(container);

        this.makeResponsive(container);
    }

    /**
     * Get sorted languages list
     */
    getSortedLanguages() {
        return [...this.supportedLanguages].sort((a, b) => {
            const aPopular = this.popularLanguages.indexOf(a.code);
            const bPopular = this.popularLanguages.indexOf(b.code);
            
            if (aPopular !== -1 && bPopular !== -1) {
                return aPopular - bPopular;
            }
            if (aPopular !== -1) return -1;
            if (bPopular !== -1) return 1;
            
            return a.name.localeCompare(b.name);
        });
    }

    /**
     * Make the language selector responsive (for standalone mode)
     */
    makeResponsive(container) {
        const updatePosition = () => {
            if (window.innerWidth < 768) {
                // Mobile: bottom-right, smaller
                container.style.top = 'auto';
                container.style.bottom = '20px';
                container.style.right = '10px';
                container.style.padding = '10px';
                const select = container.querySelector('select');
                if (select) {
                    select.style.minWidth = '140px';
                    select.style.fontSize = '13px';
                }
            } else {
                // Desktop: top-right, avoid navbar
                container.style.top = '100px';
                container.style.bottom = 'auto';
                container.style.right = '20px';
                container.style.padding = '12px';
                const select = container.querySelector('select');
                if (select) {
                    select.style.minWidth = '180px';
                    select.style.fontSize = '14px';
                }
            }
        };

        updatePosition();
        window.addEventListener('resize', updatePosition);
    }

    /**
     * Change the current language
     */
    async changeLanguage(languageCode) {
        if (languageCode === this.currentLanguage) return;
        
        console.log(`[Translator] Changing language from ${this.currentLanguage} to ${languageCode}`);
        
        const oldLanguage = this.currentLanguage;
        this.currentLanguage = languageCode;
        localStorage.setItem('preferredLanguage', languageCode);
        
        if (languageCode === 'en') {
            // Restore original English text
            this.restoreOriginalTexts();
        } else {
            // If we had translations, clear them to force fresh translation
            if (oldLanguage !== 'en') {
                // First restore to English, then translate to new language
                this.restoreOriginalTexts();
                // Wait a moment for DOM to update
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            // Translate to new language
            await this.translatePage(languageCode);
        }
    }

    /**
     * Translate the entire page
     */
    async translatePage(targetLanguage) {
        if (this.isTranslating) {
            console.log('[Translator] Translation already in progress, skipping...');
            return;
        }
        
        this.isTranslating = true;
        console.log(`[Translator] Translating page to ${targetLanguage}...`);
        
        // Show loading indicator
        this.showLoadingIndicator();
        
        try {
            // Clear previous translations if switching between non-English languages
            this.originalTexts.clear();
            
            // Find all text nodes to translate
            const textsToTranslate = this.extractPageTexts();
            
            if (textsToTranslate.length === 0) {
                console.log('[Translator] No texts to translate');
                return;
            }
            
            console.log(`[Translator] Found ${textsToTranslate.length} text elements`);
            
            // Batch translate (max 50 at a time for better reliability)
            const batchSize = 50;
            for (let i = 0; i < textsToTranslate.length; i += batchSize) {
                const batch = textsToTranslate.slice(i, i + batchSize);
                await this.translateBatch(batch, targetLanguage);
                
                // Small delay between batches to avoid overwhelming the API
                if (i + batchSize < textsToTranslate.length) {
                    await new Promise(resolve => setTimeout(resolve, 200));
                }
            }
            
            console.log('[Translator] Page translation complete');
        } catch (error) {
            console.error('[Translator] Translation failed:', error);
            alert('Translation failed. Please try again.');
        } finally {
            this.isTranslating = false;
            this.hideLoadingIndicator();
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        const selector = document.getElementById('language-selector-container');
        if (selector) {
            selector.style.opacity = '0.6';
            selector.style.pointerEvents = 'none';
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const selector = document.getElementById('language-selector-container');
        if (selector) {
            selector.style.opacity = '1';
            selector.style.pointerEvents = 'auto';
        }
    }

    /**
     * Extract all translatable text from the page
     */
    extractPageTexts() {
        const textsToTranslate = [];
        
        // Selectors for elements to translate
        const selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'span', 'a', 'button', 'label',
            'th', 'td', 'li', 'div.text-content',
            '[data-translate]'
        ];
        
        // Elements to skip
        const skipSelectors = [
            'script', 'style', 'code', 'pre',
            '#language-selector-container',
            '[data-no-translate]'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            
            elements.forEach(element => {
                // Skip if inside a skip selector
                if (skipSelectors.some(skip => element.closest(skip))) {
                    return;
                }
                
                // Get direct text content (not from children)
                const textNodes = Array.from(element.childNodes).filter(
                    node => node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0
                );
                
                textNodes.forEach(node => {
                    const text = node.textContent.trim();
                    if (text && text.length > 0 && !/^\d+$/.test(text)) { // Skip pure numbers
                        // Store original text if not already stored
                        if (!this.originalTexts.has(node)) {
                            this.originalTexts.set(node, text);
                        }
                        
                        textsToTranslate.push({
                            node: node,
                            text: text,
                            element: element
                        });
                    }
                });
                
                // Translate placeholders
                if (element.placeholder) {
                    const placeholder = element.placeholder.trim();
                    if (placeholder) {
                        if (!this.originalTexts.has(element)) {
                            this.originalTexts.set(element, { placeholder });
                        }
                        textsToTranslate.push({
                            node: element,
                            text: placeholder,
                            isPlaceholder: true
                        });
                    }
                }
                
                // Translate title attributes
                if (element.title) {
                    const title = element.title.trim();
                    if (title) {
                        if (!this.originalTexts.has(element)) {
                            this.originalTexts.set(element, { title });
                        }
                        textsToTranslate.push({
                            node: element,
                            text: title,
                            isTitle: true
                        });
                    }
                }
            });
        });
        
        return textsToTranslate;
    }

    /**
     * Translate a batch of texts
     */
    async translateBatch(batch, targetLanguage) {
        try {
            // Extract just the text strings
            const texts = batch.map(item => item.text);
            
            // Check cache first
            const cacheKey = `${targetLanguage}:${texts.join('||')}`;
            if (this.translationCache[cacheKey]) {
                this.applyTranslations(batch, this.translationCache[cacheKey]);
                return;
            }
            
            // Call translation API
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: texts,
                    target: targetLanguage,
                    source: 'en'
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.translations) {
                const translations = data.translations.map(t => t.translated);
                
                // Cache the translations
                this.translationCache[cacheKey] = translations;
                
                // Apply translations
                this.applyTranslations(batch, translations);
            }
        } catch (error) {
            console.error('[Translator] Batch translation failed:', error);
        }
    }

    /**
     * Apply translations to the page
     */
    applyTranslations(batch, translations) {
        batch.forEach((item, index) => {
            const translation = translations[index];
            
            if (item.isPlaceholder) {
                item.node.placeholder = translation;
            } else if (item.isTitle) {
                item.node.title = translation;
            } else {
                item.node.textContent = translation;
            }
        });
    }

    /**
     * Restore original English text
     */
    restoreOriginalTexts() {
        console.log(`[Translator] Restoring ${this.originalTexts.size} original texts`);
        
        let restored = 0;
        this.originalTexts.forEach((originalValue, node) => {
            try {
                if (typeof originalValue === 'string') {
                    // It's a text node
                    if (node.textContent !== originalValue) {
                        node.textContent = originalValue;
                        restored++;
                    }
                } else {
                    // It's an element with placeholder/title
                    if (originalValue.placeholder && node.placeholder) {
                        node.placeholder = originalValue.placeholder;
                        restored++;
                    }
                    if (originalValue.title && node.title) {
                        node.title = originalValue.title;
                        restored++;
                    }
                }
            } catch (error) {
                console.warn('[Translator] Failed to restore node:', error);
            }
        });
        
        console.log(`[Translator] Restored ${restored} text elements to English`);
    }
}

// Initialize translator when DOM is ready
let translator;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        translator = new PageTranslator();
        translator.init();
    });
} else {
    translator = new PageTranslator();
    translator.init();
}

// Export for use in other scripts
window.translator = translator;
