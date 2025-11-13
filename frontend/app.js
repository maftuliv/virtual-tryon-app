// API Configuration
const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000' : '';

// State Management
const state = {
    personImages: [],
    garmentImage: null,
    uploadedPersonPaths: [],
    uploadedGarmentPath: null,
    sessionId: null,
    garmentCategory: 'auto'  // Default to auto
};

// DOM Elements
const personImagesInput = document.getElementById('personImages');
const garmentImageInput = document.getElementById('garmentImage');
const personUploadZone = document.getElementById('personUploadZone');
const garmentUploadZone = document.getElementById('garmentUploadZone');
const personPreview = document.getElementById('personPreview');
const garmentPreview = document.getElementById('garmentPreview');
const generateSwitch = document.getElementById('generateSwitch');
const progressBar = document.getElementById('progressBar');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
// resetBtn is now created dynamically in each result card
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const ratingSlider = document.getElementById('ratingSlider');
const ratingValue = document.getElementById('ratingValue');
const feedbackComment = document.getElementById('feedbackComment');
const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
const feedbackSuccess = document.getElementById('feedbackSuccess');
// testFeedbackBtn removed - using direct function call from footer button

// Step Management
let currentStep = 1;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    setupUploadZones();
    setupEventListeners();
    setupStepper();
    checkServerHealth();
    setupAdminAccess();
});

// Setup admin access with keyboard shortcut
function setupAdminAccess() {
    let keysPressed = [];
    const secretCode = ['Control', 'Shift', 'A'];

    document.addEventListener('keydown', (e) => {
        keysPressed.push(e.key);
        keysPressed = keysPressed.slice(-3); // Keep only last 3 keys

        // Check if secret code matches
        if (keysPressed.join(',') === secretCode.join(',')) {
            const statsLink = document.getElementById('statsLink');
            if (statsLink) {
                statsLink.style.display = 'inline-flex';
                // Save to sessionStorage so it persists during session
                sessionStorage.setItem('admin_access', 'true');
                console.log('🔓 Admin access granted');
            }
        }
    });

    // Check if admin access was already granted in this session
    if (sessionStorage.getItem('admin_access') === 'true') {
        const statsLink = document.getElementById('statsLink');
        if (statsLink) {
            statsLink.style.display = 'inline-flex';
        }
    }
}

// Setup Stepper Navigation
function setupStepper() {
    const step1Btn = document.getElementById('step1Btn');
    const step2Btn = document.getElementById('step2Btn');
    const step1Content = document.getElementById('step1Content');
    const step2Content = document.getElementById('step2Content');

    if (step1Btn) {
        step1Btn.addEventListener('click', () => switchStep(1));
    }
    if (step2Btn) {
        step2Btn.addEventListener('click', () => switchStep(2));
    }

    // Check if mobile device
    const isMobile = window.innerWidth <= 768;
    
    // Initialize with step 1 - set initial state
    if (step1Content) {
        step1Content.style.display = 'block';
        if (!isMobile) {
            step1Content.style.position = 'absolute';
            step1Content.style.top = '0';
            step1Content.style.left = '0';
            step1Content.style.right = '0';
            step1Content.style.width = '100%';
        }
        step1Content.classList.add('step-active');
    }
    if (step2Content) {
        step2Content.style.display = 'none';
        if (!isMobile) {
            step2Content.style.position = 'absolute';
            step2Content.style.top = '0';
            step2Content.style.left = '0';
            step2Content.style.right = '0';
            step2Content.style.width = '100%';
        }
    }
    
    // Initialize with step 1
    switchStep(1);
}

function switchStep(step) {
    currentStep = step;
    const step1Btn = document.getElementById('step1Btn');
    const step2Btn = document.getElementById('step2Btn');
    const step1Content = document.getElementById('step1Content');
    const step2Content = document.getElementById('step2Content');

    // Update buttons
    if (step1Btn) {
        if (step === 1) {
            step1Btn.classList.add('active');
        } else {
            step1Btn.classList.remove('active');
        }
    }
    if (step2Btn) {
        if (step === 2) {
            step2Btn.classList.add('active');
        } else {
            step2Btn.classList.remove('active');
        }
    }

    // Check if mobile device
    const isMobile = window.innerWidth <= 768;
    
    // Smooth slide animation (desktop only)
    if (step1Content && step2Content && !isMobile) {
        if (step === 1) {
            // Switching to step 1: step2 slides out right, step1 slides in from left
            step2Content.classList.remove('step-active');
            step2Content.classList.add('step-slide-out-right');
            
            // Ensure step1 is positioned correctly before making it visible
            step1Content.style.display = 'block';
            step1Content.style.position = 'absolute';
            step1Content.style.top = '0';
            step1Content.style.left = '0';
            step1Content.style.right = '0';
            step1Content.style.width = '100%';
            step1Content.classList.remove('step-slide-out-right', 'step-slide-out-left');
            step1Content.classList.add('step-slide-in-left');
            
            // Trigger reflow
            step1Content.offsetHeight;
            
            setTimeout(() => {
                step1Content.classList.remove('step-slide-in-left');
                step1Content.classList.add('step-active');
                
                setTimeout(() => {
                    step2Content.style.display = 'none';
                    step2Content.classList.remove('step-slide-out-right');
                }, 500);
            }, 10);
        } else {
            // Switching to step 2: step1 slides out left, step2 slides in from right
            step1Content.classList.remove('step-active');
            step1Content.classList.add('step-slide-out-left');
            
            // Ensure step2 is positioned correctly before making it visible
            step2Content.style.display = 'block';
            step2Content.style.position = 'absolute';
            step2Content.style.top = '0';
            step2Content.style.left = '0';
            step2Content.style.right = '0';
            step2Content.style.width = '100%';
            step2Content.style.visibility = 'hidden';
            step2Content.classList.remove('step-slide-out-left', 'step-active');
            step2Content.classList.add('step-slide-in-right');
            
            // Force reflow to ensure initial state is applied
            step2Content.offsetHeight;
            
            // Make visible and start animation
            step2Content.style.visibility = 'visible';
            
            setTimeout(() => {
                step2Content.classList.remove('step-slide-in-right');
                step2Content.classList.add('step-active');
                
                setTimeout(() => {
                    step1Content.style.display = 'none';
                    step1Content.classList.remove('step-slide-out-left');
                }, 500);
            }, 10);
        }
    } else if (step1Content && step2Content && isMobile) {
        // Simple show/hide for mobile devices
        if (step === 1) {
            step1Content.style.display = 'block';
            step2Content.style.display = 'none';
        } else {
            step1Content.style.display = 'none';
            step2Content.style.display = 'block';
        }
    }
}

function setupUploadZones() {
    // Person images upload - only trigger if clicking on upload zone itself, not previews or buttons
    personUploadZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on preview items, remove buttons, or file selection button
        if (e.target.closest('.preview-item') || 
            e.target.closest('.preview-remove') || 
            e.target.closest('#personFileBtn') ||
            e.target.id === 'personFileBtn') {
            return;
        }
        personImagesInput.click();
    });
    personImagesInput.addEventListener('change', handlePersonImagesSelect);

    // Garment image upload - only trigger if clicking on upload zone itself, not previews or buttons
    garmentUploadZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on preview items, remove buttons, or file selection button
        if (e.target.closest('.preview-item') || 
            e.target.closest('.preview-remove') || 
            e.target.closest('#garmentFileBtn') ||
            e.target.id === 'garmentFileBtn') {
            return;
        }
        garmentImageInput.click();
    });
    garmentImageInput.addEventListener('change', handleGarmentImageSelect);

    // Drag and drop for person images
    setupDragAndDrop(personUploadZone, handlePersonImagesDrop);

    // Drag and drop for garment image
    setupDragAndDrop(garmentUploadZone, handleGarmentImageDrop);
}

function setupDragAndDrop(zone, dropHandler) {
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        dropHandler(e.dataTransfer.files);
    });
}

function setupEventListeners() {
    // File selection buttons
    const personFileBtn = document.getElementById('personFileBtn');
    const garmentFileBtn = document.getElementById('garmentFileBtn');
    
    if (personFileBtn && personImagesInput) {
        personFileBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            personImagesInput.click();
        });
    }
    
    if (garmentFileBtn && garmentImageInput) {
        garmentFileBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            garmentImageInput.click();
        });
    }

    // Generate button - triggers generation when clicked
    if (generateSwitch) {
        generateSwitch.addEventListener('click', (e) => {
            e.preventDefault();
            // Disable button to prevent double clicks
            if (generateSwitch.disabled) return;
            
            // Check if images are loaded before starting
            const hasPersonImages = state.personImages.length > 0;
            const hasGarmentImage = state.garmentImage !== null;
            
            if (!hasPersonImages || !hasGarmentImage) {
                // Show error message below button
                showCtaButtonError();
                return;
            }
            
            // Hide any previous error
            hideCtaButtonError();
            
            // Add loading state
            generateSwitch.classList.add('loading');
            generateSwitch.disabled = true;
            
            // Start generation
            handleTryOn();
        });
    }

    // Reset button is now in each result card, no need for global handler
    // downloadAllBtn removed - functionality removed

    // Category selector
    document.querySelectorAll('input[name="garmentCategory"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            state.garmentCategory = e.target.value;
            console.log('[CATEGORY] Selected category:', state.garmentCategory);
        });
    });

    // Feedback form handlers
    if (ratingSlider && ratingValue) {
        ratingSlider.addEventListener('input', (e) => {
            ratingValue.textContent = e.target.value;
        });
    }

    // Ensure feedback button handler is attached
    attachFeedbackHandler();

    // Test feedback button removed - now using direct function call from footer button

    // Tips toggle button
    const tipsToggle = document.getElementById('tipsToggle');
    const tipsExamples = document.getElementById('tipsExamples');
    if (tipsToggle && tipsExamples) {
        tipsToggle.addEventListener('click', () => {
            const isActive = tipsToggle.classList.contains('active');
            if (isActive) {
                tipsToggle.classList.remove('active');
                tipsExamples.style.display = 'none';
            } else {
                tipsToggle.classList.add('active');
                tipsExamples.style.display = 'grid';
            }
        });
    }
}

// Server Health Check
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_URL}/api/health`);
        if (response.ok) {
            console.log('Server is running');
        } else {
            showError('Сервер недоступен. Пожалуйста, запустите backend сервер.');
        }
    } catch (error) {
        showError('Не удалось подключиться к серверу. Убедитесь, что backend запущен на порту 5000.');
    }
}

// Handle Person Images
function handlePersonImagesSelect(e) {
    console.log('handlePersonImagesSelect triggered');
    const files = Array.from(e.target.files);
    console.log('Files selected:', files.length);
    if (files.length > 0) {
        processPersonImages(files);
    }
    // Clear input value to allow selecting the same file again
    // But do it after a small delay to prevent immediate re-trigger
    setTimeout(() => {
        e.target.value = '';
    }, 100);
}

function handlePersonImagesDrop(files) {
    const fileArray = Array.from(files);
    processPersonImages(fileArray);
}

function processPersonImages(files) {
    console.log('processPersonImages called with', files.length, 'files');

    if (files.length === 0) {
        console.log('No files to process');
        return;
    }

    if (files.length > 4) {
        showError('Можно загрузить максимум 4 фотографии');
        return;
    }

    // Validate file types
    const validFiles = files.filter(file => {
        if (!file.type.startsWith('image/')) {
            showError(`Файл ${file.name} не является изображением`);
            return false;
        }
        return true;
    });

    console.log('Valid files:', validFiles.length);
    state.personImages = validFiles;
    displayPersonPreviews();
    updateGenerateSwitch();
    
    // Hide error if images are now loaded
    hideCtaButtonError();
    
    // Automatically switch to step 2 after successful photo upload
    if (validFiles.length > 0 && currentStep === 1) {
        // Small delay for better UX
        setTimeout(() => {
            switchStep(2);
        }, 300);
    }
}

function displayPersonPreviews() {
    console.log('displayPersonPreviews called, images count:', state.personImages.length);
    console.log('personPreview element:', personPreview);
    console.log('personPreview ID:', personPreview ? personPreview.id : 'null');
    personPreview.innerHTML = '';

    if (state.personImages.length === 0) {
        console.log('No images to display');
        return;
    }

    state.personImages.forEach((file, index) => {
        console.log(`Reading file ${index}:`, file.name);
        const reader = new FileReader();
        reader.onload = (e) => {
            console.log(`File ${index} loaded successfully`);
            const previewItem = createPreviewItem(e.target.result, index, 'person');
            console.log('Appending to personPreview:', personPreview.id);
            personPreview.appendChild(previewItem);
            console.log('Preview appended, parent ID:', previewItem.parentElement.id);
        };
        reader.onerror = (e) => {
            console.error(`Error reading file ${index}:`, e);
        };
        reader.readAsDataURL(file);
    });
}

// Handle Garment Image
function handleGarmentImageSelect(e) {
    console.log('handleGarmentImageSelect triggered');
    const file = e.target.files[0];
    console.log('File selected:', file ? file.name : 'none');
    if (file) {
        processGarmentImage(file);
    }
    // Clear input value to allow selecting the same file again
    // But do it after a small delay to prevent immediate re-trigger
    setTimeout(() => {
        e.target.value = '';
    }, 100);
}

function handleGarmentImageDrop(files) {
    if (files.length > 0) {
        processGarmentImage(files[0]);
    }
}

function processGarmentImage(file) {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        showError('Файл должен быть изображением');
        return;
    }

    state.garmentImage = file;
    displayGarmentPreview();
    updateGenerateSwitch();
    
    // Hide error if image is now loaded
    hideCtaButtonError();
    
    // Плавный автоскролл до кнопки "Сделать примерку" в мобильной версии
    // Только если уже загружено фото пользователя (шаг 1)
    const isMobile = window.innerWidth <= 768;
    const hasPersonImages = state.personImages.length > 0;
    
    if (isMobile && hasPersonImages) {
        // Небольшая задержка для завершения отображения превью
        setTimeout(() => {
            const generateButton = document.getElementById('generateSwitch');
            if (generateButton) {
                generateButton.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
            }
        }, 300);
    }
}

function displayGarmentPreview() {
    garmentPreview.innerHTML = '';

    const reader = new FileReader();
    reader.onload = (e) => {
        const previewItem = createPreviewItem(e.target.result, 0, 'garment');
        garmentPreview.appendChild(previewItem);
    };
    reader.readAsDataURL(state.garmentImage);
}

// Create Preview Item
function createPreviewItem(src, index, type) {
    const div = document.createElement('div');
    div.className = 'preview-item';
    div.dataset.index = index;
    div.dataset.type = type;

    const img = document.createElement('img');
    img.src = src;
    img.alt = type === 'person' ? 'Person Image' : 'Garment Image';

    // Validate image on load
    img.onload = async () => {
        await validatePreviewImage(div, src, type, index);
    };

    const removeBtn = document.createElement('button');
    removeBtn.className = 'preview-remove';
    removeBtn.innerHTML = '×';
    removeBtn.onclick = (e) => {
        e.stopPropagation();
        if (type === 'person') {
            removePersonImage(index);
        } else {
            removeGarmentImage();
        }
    };

    div.appendChild(img);
    div.appendChild(removeBtn);

    return div;
}

// Validate preview image and add status badge
async function validatePreviewImage(previewDiv, imageSrc, type, index) {
    try {
        // Load image to get dimensions
        const tempImg = new Image();
        tempImg.src = imageSrc;

        await new Promise((resolve) => {
            tempImg.onload = resolve;
        });

        const width = tempImg.width;
        const height = tempImg.height;
        const aspectRatio = width / height;

        // Create status badge
        const badge = document.createElement('div');
        badge.className = 'preview-status-badge';

        if (type === 'person') {
            // For person images: check orientation only
            if (height > width) {
                // Vertical photo - good for full body
                badge.classList.add('status-ok');
                badge.innerHTML = '<span class="status-icon">✅</span><span>OK</span>';
                previewDiv.classList.add('validated-ok');
            } else {
                // Horizontal photo - warning
                badge.classList.add('status-warning');
                badge.innerHTML = '<span class="status-icon">⚠️</span><span>Рекомендуется вертикальное фото</span>';
                previewDiv.classList.add('has-warnings');
            }
        } else if (type === 'garment') {
            // For garment images: basic checks
            if (width < 512 && height < 512) {
                badge.classList.add('status-error');
                badge.innerHTML = '<span class="status-icon">❌</span><span>Разрешение слишком низкое</span>';
                previewDiv.classList.add('has-errors');
            } else if (aspectRatio > 2.0 || aspectRatio < 0.5) {
                badge.classList.add('status-warning');
                badge.innerHTML = '<span class="status-icon">⚠️</span><span>Необычные пропорции</span>';
                previewDiv.classList.add('has-warnings');
            } else {
                badge.classList.add('status-ok');
                badge.innerHTML = '<span class="status-icon">✅</span><span>OK</span>';
                previewDiv.classList.add('validated-ok');
            }
        }

        previewDiv.appendChild(badge);

        console.log(`[VALIDATION] ${type} - ${width}x${height}, ratio: ${aspectRatio.toFixed(2)}, orientation: ${height > width ? 'vertical' : 'horizontal'}`);

        // Update button state after validation
        setTimeout(() => {
            updateGenerateSwitch();
        }, 100);

    } catch (error) {
        console.error('[VALIDATION] Error validating preview:', error);
    }
}

// Remove Images
function removePersonImage(index) {
    state.personImages.splice(index, 1);
    displayPersonPreviews();
    updateGenerateSwitch();
}

function removeGarmentImage() {
    state.garmentImage = null;
    garmentPreview.innerHTML = '';
    garmentImageInput.value = '';
    updateGenerateSwitch();
}

// Update Generate Button State
function updateGenerateSwitch() {
    const hasPersonImages = state.personImages.length > 0;
    const hasGarmentImage = state.garmentImage !== null;
    const hasErrors = document.querySelectorAll('.preview-item.has-errors').length > 0;
    const canGenerate = hasPersonImages && hasGarmentImage && !hasErrors;

    if (generateSwitch) {
        // Enable/disable button based on ready state
        generateSwitch.disabled = !canGenerate;
        if (canGenerate) {
            generateSwitch.classList.remove('disabled');
        } else {
            generateSwitch.classList.add('disabled');
        }
    }
}

// Handle Try-On Process
async function handleTryOn() {
    try {
        // Disable button and add loading state
        if (generateSwitch) {
            generateSwitch.disabled = true;
            generateSwitch.classList.add('loading');
        }
        progressBar.style.display = 'block';
        resultsSection.style.display = 'none';
        hideError();

        // Update progress text
        updateProgressText('Загрузка изображений...');

        // Step 1: Upload files
        const formData = new FormData();

        state.personImages.forEach(file => {
            formData.append('person_images', file);
        });

        formData.append('garment_image', state.garmentImage);

        const uploadResponse = await fetch(`${API_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Ошибка загрузки файлов');
        }

        const uploadData = await uploadResponse.json();

        if (!uploadData.success) {
            throw new Error(uploadData.error || 'Загрузка не удалась');
        }

        console.log('[UPLOAD] Upload data received:', uploadData);

        // Display validation warnings if any
        if (uploadData.validation_warnings) {
            displayValidationWarnings(uploadData.validation_warnings);
        }

        state.uploadedPersonPaths = uploadData.person_images;
        state.uploadedGarmentPath = uploadData.garment_image;
        state.sessionId = uploadData.session_id;

        // Step 2: Perform virtual try-on
        updateProgressText('создается магия твоего стиля ✨');

        const tryonResponse = await fetch(`${API_URL}/api/tryon`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                person_images: state.uploadedPersonPaths,
                garment_image: state.uploadedGarmentPath,
                garment_category: state.garmentCategory  // Send selected category
            })
        });

        if (!tryonResponse.ok) {
            const errorData = await tryonResponse.json().catch(() => ({}));
            // Handle special error format with message field
            const errorMessage = errorData.message || errorData.error || 'Ошибка обработки изображений';
            throw new Error(errorMessage);
        }

        const tryonData = await tryonResponse.json();

        if (!tryonData.success) {
            throw new Error(tryonData.error || 'Обработка не удалась');
        }

        // Check if we have results
        if (!tryonData.results || tryonData.results.length === 0) {
            throw new Error('Не удалось получить результаты. Проверьте настройки API.');
        }

        // Display results
        displayResults(tryonData.results);

        // Hide progress, show results
        progressBar.style.display = 'none';
        resultsSection.style.display = 'block';
        
        // Re-enable button
        if (generateSwitch) {
            generateSwitch.disabled = false;
            generateSwitch.classList.remove('loading');
        }

    } catch (error) {
        console.error('Error:', error);

        // More detailed error message
        let errorMsg = error.message;

        // NanoBanana API specific errors
        if (error.message.includes('NANOBANANA_API_KEY_MISSING') || error.message.includes('NANOBANANA_API_KEY not set')) {
            // Special handling for missing Nano Banana key - show original message
            errorMsg = error.message.replace('NANOBANANA_API_KEY_MISSING', '').trim();
            if (!errorMsg || errorMsg === error.message) {
                errorMsg = '🍌 Nano Banana API ключ не настроен\n\n' +
                           'Добавьте NANOBANANA_API_KEY в Railway Variables:\n' +
                           '1. Зайдите на https://nanobananaapi.ai/api-key\n' +
                           '2. Создайте API ключ\n' +
                           '3. Добавьте его в Railway Dashboard → Variables';
            }
        } else if (error.message.includes('401')) {
            errorMsg = '🔑 Неверный API ключ\n\nПроверьте настройки';
        } else if (error.message.includes('402')) {
            errorMsg = '💳 Недостаточно кредитов\n\nПополните баланс';
        } else if (error.message.includes('timeout')) {
            errorMsg = '⏱️ Превышено время ожидания\n\nПопробуйте снова';
        }

        showError(errorMsg);
        progressBar.style.display = 'none';
        // Reset button on error
        if (generateSwitch) {
            generateSwitch.disabled = false;
            generateSwitch.classList.remove('loading');
        }
    }
}

function updateProgressText(text) {
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = text;
    }
}

// Display Results
function displayResults(results) {
    resultsGrid.innerHTML = '';

    let successCount = 0;

    results.forEach((result, index) => {
        if (result.error) {
            console.error(`Error for image ${index}:`, result.error);

            // Parse NanoBanana API specific errors
            let errorMsg = result.error;
            let errorTitle = 'Ошибка обработки изображения';

            // Show error card
            const errorCard = document.createElement('div');
            errorCard.className = 'result-card error-card';
            errorCard.innerHTML = `
                <div class="error-result">
                    <span class="error-icon">⚠️</span>
                    <p>${errorTitle}</p>
                    <small style="white-space: pre-line;">${errorMsg}</small>
                </div>
            `;
            resultsGrid.appendChild(errorCard);
            return;
        }

        // Check if result_image exists
        if (!result.result_image) {
            console.error(`No result image for index ${index}:`, result);
            return;
        }

        // New card structure with preview on left and promo on right
        const card = document.createElement('div');
        card.className = 'result-card-new';

        // Left side: Image preview with gradient mask
        const leftSide = document.createElement('div');
        leftSide.className = 'result-left';

        const imageContainer = document.createElement('div');
        imageContainer.className = 'result-image-container';

        const img = document.createElement('img');
        img.src = result.result_image;
        img.alt = `Результат ${index + 1}`;
        img.className = 'result-image-preview';

        // Add loading state
        img.onload = () => {
            card.classList.add('loaded');
        };

        img.onerror = () => {
            console.error(`Failed to load image ${index}`);
            card.innerHTML = `
                <div class="error-result">
                    <span class="error-icon">⚠️</span>
                    <p>Не удалось загрузить результат ${index + 1}</p>
                </div>
            `;
        };

        const resultTitle = document.createElement('h3');
        resultTitle.className = 'result-number';
        resultTitle.textContent = 'Вы восхитительны 🥹';

        // Buttons container
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'result-buttons-container';
        buttonsContainer.style.display = 'flex';
        buttonsContainer.style.gap = '12px';
        buttonsContainer.style.width = '100%';
        buttonsContainer.style.maxWidth = '280px';

        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.innerHTML = '💾 Скачать';
        // Always use base64 image (result_image) for instant access - no fetch delay
        // Generate filename from result_filename if available, otherwise use default
        downloadBtn.onclick = () => {
            // Use base64 image directly for instant Web Share API - no fetch needed
            const filename = result.result_filename || `taptolook.net_result_${index + 1}.png`;
            downloadResult(result.result_image, index, filename);
        };

        const retryBtn = document.createElement('button');
        retryBtn.className = 'download-btn';
        retryBtn.innerHTML = '🔄 Повторить';
        retryBtn.onclick = () => {
            // Scroll to top and reset to step 1
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setTimeout(() => {
                switchStep(1);
            }, 500);
        };

        buttonsContainer.appendChild(downloadBtn);
        buttonsContainer.appendChild(retryBtn);

        imageContainer.appendChild(img);
        leftSide.appendChild(imageContainer);
        leftSide.appendChild(resultTitle);
        leftSide.appendChild(buttonsContainer);

        // Right side: Coming soon promo
        const rightSide = document.createElement('div');
        rightSide.className = 'result-right';

        rightSide.innerHTML = `
            <div class="promo-content">
                <div class="promo-header">
                    <h3 class="promo-title">Полноценный образ</h3>
                    <span class="promo-badge">Скоро</span>
                </div>
                <p class="promo-description">
                    Скоро вы сможете собирать целостные образы: официальный, уличный,
                    вечерний — или подготовиться к любому мероприятию одним нажатием.
                    Подбирайте одежду, обувь и аксессуары, а мы покажем, как это выглядит вместе.
                </p>
                <div class="promo-features">
                    <div class="promo-feature">
                        <span class="feature-icon">✨</span>
                        <span class="feature-text">Полный образ за клик</span>
                    </div>
                    <div class="promo-feature">
                        <span class="feature-icon">👔</span>
                        <span class="feature-text">Все стили мероприятий</span>
                    </div>
                    <div class="promo-feature">
                        <span class="feature-icon">👟</span>
                        <span class="feature-text">Одежда + обувь + аксессуары</span>
                    </div>
                </div>
            </div>
        `;

        // Assemble card
        card.appendChild(leftSide);
        card.appendChild(rightSide);

        resultsGrid.appendChild(card);
        successCount++;
    });

    // Show message if no successful results AND no error cards were added
    if (successCount === 0 && resultsGrid.children.length === 0) {
        resultsGrid.innerHTML = `
            <div class="no-results">
                <span class="error-icon">😔</span>
                <h3>Не удалось получить результаты</h3>
                <p>Попробуйте загрузить другие изображения или проверьте настройки API</p>
            </div>
        `;
    }

    // Show results grid - CRITICAL: always show grid when displaying results
    if (resultsGrid) {
        resultsGrid.style.display = 'grid';
    }
    
    // Show results title and action buttons when there are actual results
    const resultsTitle = document.querySelector('.results-title');
    const actionButtons = document.querySelector('.action-buttons');
    if (resultsTitle && successCount > 0) {
        resultsTitle.style.display = 'block';
    }
    if (actionButtons && successCount > 0) {
        actionButtons.style.display = 'flex';
    }
    
    // Show feedback form after results are displayed (but don't hide results!)
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection && successCount > 0) {
        feedbackSection.style.display = 'block';
        // Reset form
        const ratingSlider = document.getElementById('ratingSlider');
        const ratingValue = document.getElementById('ratingValue');
        const feedbackComment = document.getElementById('feedbackComment');
        const feedbackSuccess = document.getElementById('feedbackSuccess');
        
        if (ratingSlider) ratingSlider.value = 3;
        if (ratingValue) ratingValue.textContent = '3';
        if (feedbackComment) feedbackComment.value = '';
        if (feedbackSuccess) feedbackSuccess.style.display = 'none';
        
        // Re-attach handler when section is shown
        attachFeedbackHandler();
    }
}

// Universal function to save image to gallery on mobile devices
// Uses Web Share API for iOS/Android, or shows fullscreen modal for long-press save
async function saveImageToGallery(imageSource, filename, index) {
    try {
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
        
        // Step 1: Convert image source to Blob
        let blob;
        let blobUrl;
        
        if (typeof imageSource === 'string') {
            if (imageSource.startsWith('data:')) {
                // Base64 data URL - INSTANT conversion (no async delay)
                // Extract base64 data and MIME type
                const commaIndex = imageSource.indexOf(',');
                const mimeType = imageSource.substring(5, commaIndex).split(';')[0] || 'image/png';
                const base64Data = imageSource.substring(commaIndex + 1);
                
                // Fast synchronous base64 to Blob conversion
                // This is instant - no network requests, no async operations
                const binaryString = atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                blob = new Blob([bytes], { type: mimeType });
                blobUrl = URL.createObjectURL(blob);
            } else {
                // URL - fetch and convert to Blob
                try {
                    // Use fetch with credentials for CORS
                    const response = await fetch(imageSource, {
                        method: 'GET',
                        mode: 'cors',
                        credentials: 'omit',
                        cache: 'no-cache'
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    blob = await response.blob();
                    
                    // Verify it's an image
                    if (!blob.type.startsWith('image/')) {
                        throw new Error('Response is not an image');
                    }
                    
                    blobUrl = URL.createObjectURL(blob);
                } catch (fetchError) {
                    console.error('Error fetching image:', fetchError);
                    
                    // Fallback: show fullscreen modal with direct URL
                    // User can long-press to save
                    showFullscreenImageModal(imageSource, filename);
                    return;
                }
            }
        } else if (imageSource instanceof Blob) {
            blob = imageSource;
            blobUrl = URL.createObjectURL(blob);
        } else {
            throw new Error('Invalid image source');
        }
        
        // Step 2: For mobile devices, use Web Share API or show fullscreen modal
        if (isMobile) {
            // Try Web Share API first (iOS 12.2+, Android Chrome 89+)
            // INSTANT: No canShare check - call share directly for maximum speed
            if (navigator.share) {
                try {
                    // Create File object from Blob (synchronous, instant)
                    const file = new File([blob], filename, {
                        type: blob.type || 'image/png',
                        lastModified: Date.now()
                    });
                    
                    const shareData = {
                        files: [file],
                        title: 'Tap to Look - Результат примерки',
                        text: 'Мой результат виртуальной примерки'
                    };
                    
                    // Call share directly - no canShare check to avoid delay
                    // This opens the share menu INSTANTLY
                    await navigator.share(shareData);
                    // Clean up after share completes
                    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
                    return; // Success - user chose where to save (Photos, Files, etc.)
                } catch (shareError) {
                    // Web Share API failed or user cancelled
                    // Error code 20 = user cancelled (AbortError)
                    if (shareError.name === 'AbortError' || shareError.code === 20) {
                        console.log('User cancelled share');
                        URL.revokeObjectURL(blobUrl);
                        return;
                    }
                    // DOMException: "Failed to execute 'share' on 'Navigator': Share failed"
                    // NotSupportedError, TypeError, etc. - fall through to modal
                    console.log('Web Share API not available:', shareError.name);
                    // Fall through to fullscreen modal
                }
            }
            
            // Step 3: Fallback - Show fullscreen modal with image
            // User can long-press to save to gallery
            showFullscreenImageModal(blobUrl, filename);
        } else {
            // Desktop - standard download
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            link.style.cssText = 'position: fixed; left: -9999px; opacity: 0;';
            
            document.body.appendChild(link);
            link.click();
            
            setTimeout(() => {
                if (link.parentNode) {
                    document.body.removeChild(link);
                }
                URL.revokeObjectURL(blobUrl);
            }, 1000);
        }
    } catch (error) {
        console.error('Error saving image to gallery:', error);
        showError('Не удалось сохранить изображение. Попробуйте сделать длительное нажатие на изображение.');
    }
}

// Show fullscreen modal with image for long-press save
function showFullscreenImageModal(imageUrl, filename) {
    // Remove existing modal if present
    const existingModal = document.getElementById('fullscreenImageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Check if URL is a blob URL (needs cleanup) or regular URL
    const isBlobUrl = imageUrl.startsWith('blob:');
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'fullscreenImageModal';
    modal.className = 'fullscreen-image-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.98);
        z-index: 10000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-sizing: border-box;
        animation: fadeIn 0.3s ease;
    `;
    
    // Add fade-in animation
    if (!document.getElementById('fullscreenModalStyles')) {
        const style = document.createElement('style');
        style.id = 'fullscreenModalStyles';
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.setAttribute('aria-label', 'Закрыть');
    closeBtn.style.cssText = `
        position: absolute;
        top: 15px;
        right: 15px;
        background: rgba(255, 255, 255, 0.25);
        border: 2px solid rgba(255, 255, 255, 0.5);
        color: white;
        font-size: 28px;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        cursor: pointer;
        z-index: 10001;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    `;
    closeBtn.onmouseover = () => {
        closeBtn.style.background = 'rgba(255, 255, 255, 0.4)';
    };
    closeBtn.onmouseout = () => {
        closeBtn.style.background = 'rgba(255, 255, 255, 0.25)';
    };
    closeBtn.onclick = () => {
        modal.remove();
        if (isBlobUrl) {
            URL.revokeObjectURL(imageUrl);
        }
    };
    
    // Create instruction text
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    const instruction = document.createElement('div');
    instruction.innerHTML = isIOS ? 
        '<strong>💾 Сохранить в Фото:</strong><br>Сделайте длительное нажатие на изображение и выберите "Сохранить в Фото"' :
        '<strong>💾 Сохранить изображение:</strong><br>Сделайте длительное нажатие на изображение и выберите "Сохранить изображение"';
    instruction.style.cssText = `
        color: white;
        font-size: 14px;
        text-align: center;
        margin-bottom: 15px;
        padding: 12px 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        line-height: 1.5;
    `;
    
    // Create image container
    const imgContainer = document.createElement('div');
    imgContainer.style.cssText = `
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        max-width: 100%;
        max-height: calc(100% - 120px);
        overflow: auto;
        -webkit-overflow-scrolling: touch;
    `;
    
    // Create image
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = filename;
    img.style.cssText = `
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        object-fit: contain;
        -webkit-user-select: none;
        -webkit-touch-callout: default;
        touch-action: manipulation;
        display: block;
    `;
    
    // Handle image load error
    img.onerror = () => {
        instruction.textContent = 'Ошибка загрузки изображения';
        instruction.style.color = '#ff6b6b';
    };
    
    // Make image downloadable via long press
    // Don't prevent default context menu - let browser handle it
    // This allows users to long-press and save image
    
    // Add image to container
    imgContainer.appendChild(img);
    
    // Assemble modal
    modal.appendChild(closeBtn);
    modal.appendChild(instruction);
    modal.appendChild(imgContainer);
    
    // Add to document
    document.body.appendChild(modal);
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    
    // Close function
    const closeModal = () => {
        modal.remove();
        document.body.style.overflow = '';
        if (isBlobUrl) {
            URL.revokeObjectURL(imageUrl);
        }
    };
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target === imgContainer) {
            closeModal();
        }
    });
    
    // Close on Escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
    
    // Clean up on modal removal
    const observer = new MutationObserver(() => {
        if (!document.getElementById('fullscreenImageModal')) {
            document.body.style.overflow = '';
            if (isBlobUrl) {
                URL.revokeObjectURL(imageUrl);
            }
            observer.disconnect();
        }
    });
    observer.observe(document.body, { childList: true });
}

// Download Single Result from URL - Now uses saveImageToGallery
async function downloadResultFromUrl(imageUrl, filename, index) {
    await saveImageToGallery(imageUrl, filename, index);
}

// Download Single Result - Now uses saveImageToGallery for consistent behavior
async function downloadResult(imageData, index, customFilename = null) {
    // Use custom filename if provided, otherwise generate with timestamp
    let filename;
    if (customFilename) {
        filename = customFilename;
    } else {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        filename = `taptolook.net_result_${timestamp}_${index + 1}.png`;
    }
    
    // Use the universal saveImageToGallery function
    await saveImageToGallery(imageData, filename, index);
}

// downloadAllResults function removed - functionality no longer needed

// Reset Application
function resetApplication() {
    // Clear state
    state.personImages = [];
    state.garmentImage = null;
    state.uploadedPersonPaths = [];
    state.uploadedGarmentPath = null;
    state.sessionId = null;

    // Clear inputs
    personImagesInput.value = '';
    garmentImageInput.value = '';

    // Clear previews
    personPreview.innerHTML = '';
    garmentPreview.innerHTML = '';

    // Hide results
    resultsSection.style.display = 'none';
    resultsGrid.innerHTML = '';

    // Hide feedback form
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection) {
        feedbackSection.style.display = 'none';
    }

    // Reset generate button
    if (generateSwitch) {
        generateSwitch.disabled = false;
        generateSwitch.classList.remove('loading', 'disabled');
    }
    updateGenerateSwitch();

    // Reset to step 1
    switchStep(1);

    // Hide tips examples
    const tipsToggle = document.getElementById('tipsToggle');
    const tipsExamples = document.getElementById('tipsExamples');
    if (tipsToggle && tipsExamples) {
        tipsToggle.classList.remove('active');
        tipsExamples.style.display = 'none';
    }

    // Hide error
    hideError();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Validation Warnings Display
function displayValidationWarnings(warnings) {
    console.log('[VALIDATION] Warnings received:', warnings);

    let warningMessages = [];

    // Person images warnings
    if (warnings.person_images && warnings.person_images.length > 0) {
        warnings.person_images.forEach(item => {
            if (item.warnings && item.warnings.length > 0) {
                warningMessages.push(`Фото человека ${item.image_index + 1}:`);
                item.warnings.forEach(w => warningMessages.push(`  • ${w}`));
            }
        });
    }

    // Garment image warnings
    if (warnings.garment_image && warnings.garment_image.length > 0) {
        warningMessages.push('Фото одежды:');
        warnings.garment_image.forEach(w => warningMessages.push(`  • ${w}`));
    }

    // Display warnings if any
    if (warningMessages.length > 0) {
        const warningText = '⚠️ Обратите внимание:\n\n' + warningMessages.join('\n');
        console.log('[VALIDATION] Displaying warnings:', warningText);
        // Show as info, not error - don't block processing
        showInfo(warningText);
    }
}

// Info message (non-blocking warnings)
function showInfo(message) {
    // Create temporary info box if it doesn't exist
    let infoBox = document.getElementById('infoMessage');
    if (!infoBox) {
        infoBox = document.createElement('div');
        infoBox.id = 'infoMessage';
        infoBox.className = 'info-message';
        infoBox.style.cssText = `
            display: none;
            background: rgba(234, 179, 8, 0.15);
            backdrop-filter: blur(15px);
            border: 2px solid rgba(234, 179, 8, 0.5);
            color: #78350f;
            padding: 20px 25px;
            border-radius: 20px;
            margin: 25px 0;
            animation: slideIn 0.4s ease;
            white-space: pre-line;
            font-size: 0.9em;
            line-height: 1.6;
        `;
        const actionSection = document.querySelector('.action-section');
        if (actionSection) {
            // Find the first child (ai-model-selector) to insert before it
            const firstChild = actionSection.firstElementChild;
            if (firstChild) {
                actionSection.insertBefore(infoBox, firstChild);
            } else {
                // If no children, just append
                actionSection.appendChild(infoBox);
            }
        }
    }

    infoBox.textContent = message;
    infoBox.style.display = 'block';

    // Auto-hide after 8 seconds
    setTimeout(() => {
        infoBox.style.display = 'none';
    }, 8000);
}

// Error Handling
function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Show error message below CTA button
function showCtaButtonError() {
    const ctaError = document.getElementById('ctaButtonError');
    if (!ctaError) return;
    
    const hasPersonImages = state.personImages.length > 0;
    const hasGarmentImage = state.garmentImage !== null;
    
    let errorMessage = '';
    if (!hasPersonImages && !hasGarmentImage) {
        errorMessage = '⚠️ Сначала загрузите ваше фото и фотографию одежды';
    } else if (!hasPersonImages) {
        errorMessage = '⚠️ Сначала загрузите ваше фото';
    } else if (!hasGarmentImage) {
        errorMessage = '⚠️ Сначала загрузите фотографию одежды';
    }
    
    ctaError.textContent = errorMessage;
    ctaError.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(hideCtaButtonError, 5000);
}

// Hide error message below CTA button
function hideCtaButtonError() {
    const ctaError = document.getElementById('ctaButtonError');
    if (ctaError) {
        ctaError.style.display = 'none';
    }
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + R to reset
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        resetApplication();
    }

    // Escape to hide error
    if (e.key === 'Escape') {
        hideError();
    }
});

// Examples Modal
function showExamplesModal(type) {
    if (type === 'garment') {
        const modal = document.getElementById('garmentExamplesModal');
        if (modal) {
            modal.style.display = 'flex';
            loadGarmentSliderImages();
        }
    } else {
        const modal = document.getElementById('examplesModal');
        if (modal) {
            modal.style.display = 'flex';
            loadSliderImages();
        }
    }
}

// Lazy load slider images for person
function loadSliderImages() {
    const lazyImages = document.querySelectorAll('#examplesModal .slider-image.lazy-load');

    lazyImages.forEach(img => {
        if (img.dataset.src && !img.src) {
            img.src = img.dataset.src;
            img.classList.remove('lazy-load');
        }
    });
}

// Lazy load slider images for garment
function loadGarmentSliderImages() {
    const lazyImages = document.querySelectorAll('#garmentExamplesModal .slider-image.lazy-load');

    lazyImages.forEach(img => {
        if (img.dataset.src && !img.src) {
            img.src = img.dataset.src;
            img.classList.remove('lazy-load');
        }
    });
}

function closeExamplesModal() {
    const modal = document.getElementById('examplesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closeGarmentExamplesModal() {
    const modal = document.getElementById('garmentExamplesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Slider functionality
const sliderState = {
    good: { current: 0, total: 7 },
    bad: { current: 0, total: 5 },
    'garment-good': { current: 0, total: 11 },
    'garment-bad': { current: 0, total: 11 }
};

function changeSlide(type, direction) {
    const state = sliderState[type];
    let slider, counter;

    if (type === 'garment-good') {
        slider = document.getElementById('garmentGoodSlider');
        counter = document.getElementById('garmentGoodCounter');
    } else if (type === 'garment-bad') {
        slider = document.getElementById('garmentBadSlider');
        counter = document.getElementById('garmentBadCounter');
    } else {
        slider = document.getElementById(`${type}Slider`);
        counter = document.getElementById(`${type}Counter`);
    }

    const images = slider.querySelectorAll('.slider-image');

    // Remove active class from current image
    images[state.current].classList.remove('active');

    // Calculate new index
    state.current = (state.current + direction + state.total) % state.total;

    // Add active class to new image
    images[state.current].classList.add('active');

    // Update counter
    counter.textContent = `${state.current + 1} / ${state.total}`;
}

// Add touch support for mobile swipe
function initSliderTouch() {
    const sliderTypes = [
        { type: 'good', id: 'goodSlider' },
        { type: 'bad', id: 'badSlider' }
    ];

    sliderTypes.forEach(({ type, id }) => {
        const slider = document.getElementById(id);
        if (!slider) return;

        let touchStartX = 0;
        let touchEndX = 0;

        slider.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        slider.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe(type);
        }, { passive: true });

        function handleSwipe(type) {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    changeSlide(type, 1); // Swipe left - next
                } else {
                    changeSlide(type, -1); // Swipe right - prev
                }
            }
        }
    });
}

// Add touch support for garment sliders
function initGarmentSliderTouch() {
    const sliderTypes = [
        { type: 'garment-good', id: 'garmentGoodSlider' },
        { type: 'garment-bad', id: 'garmentBadSlider' }
    ];

    sliderTypes.forEach(({ type, id }) => {
        const slider = document.getElementById(id);
        if (!slider) return;

        let touchStartX = 0;
        let touchEndX = 0;

        slider.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        slider.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe(type);
        }, { passive: true });

        function handleSwipe(type) {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    changeSlide(type, 1); // Swipe left - next
                } else {
                    changeSlide(type, -1); // Swipe right - prev
                }
            }
        }
    });
}

// Initialize touch support when modal opens
const originalShowModal = showExamplesModal;
showExamplesModal = function(type) {
    originalShowModal(type);
    if (type === 'garment') {
        setTimeout(initGarmentSliderTouch, 100);
    } else {
        setTimeout(initSliderTouch, 100);
    }
};

// Model switcher removed - using only NanoBanana API

// Add notification animations to document
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(-20px);
            }
        }

        .notification-icon {
            font-size: 2em;
        }

        .notification-content {
            flex: 1;
        }

        .notification-title {
            font-weight: 700;
            background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1em;
            margin-bottom: 3px;
        }

        .notification-desc {
            font-size: 0.85em;
            color: #64748b;
        }

        @media (max-width: 768px) {
            .model-change-notification {
                bottom: 20px !important;
                right: 20px !important;
                left: 20px !important;
                max-width: none !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Attach feedback button handler
function attachFeedbackHandler() {
    const btn = document.getElementById('submitFeedbackBtn');
    if (btn) {
        // Remove existing listeners by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        // Attach handler to new button
        const refreshedBtn = document.getElementById('submitFeedbackBtn');
        if (refreshedBtn) {
            refreshedBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                handleFeedbackSubmit();
            });
            console.log('[FEEDBACK] Button handler attached');
        }
    } else {
        console.warn('[FEEDBACK] submitFeedbackBtn not found');
    }
}

// Handle Feedback Submission
async function handleFeedbackSubmit() {
    const ratingSlider = document.getElementById('ratingSlider');
    const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
    const feedbackComment = document.getElementById('feedbackComment');
    const feedbackSuccess = document.getElementById('feedbackSuccess');
    const ratingValue = document.getElementById('ratingValue');
    
    if (!ratingSlider || !submitFeedbackBtn) {
        console.error('[FEEDBACK] Missing required elements');
        showError('Не удалось найти элементы формы отзыва');
        return;
    }

    const rating = parseInt(ratingSlider.value);
    const comment = feedbackComment ? feedbackComment.value.trim() : '';

    console.log('[FEEDBACK] Submitting feedback:', { rating, comment, sessionId: state.sessionId });

    // Validate rating
    if (!rating || rating < 1 || rating > 5) {
        showError('Пожалуйста, выберите оценку от 1 до 5');
        return;
    }

    // Disable button during submission
    submitFeedbackBtn.disabled = true;
    submitFeedbackBtn.innerHTML = '<span>⏳ Отправка...</span>';

    try {
        const response = await fetch(`${API_URL}/api/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rating: rating,
                comment: comment,
                timestamp: new Date().toISOString(),
                session_id: state.sessionId || null
            })
        });

        console.log('[FEEDBACK] Response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('[FEEDBACK] Error response:', errorData);
            throw new Error(errorData.error || `Ошибка отправки отзыва (${response.status})`);
        }

        const result = await response.json();
        console.log('[FEEDBACK] Success:', result);

        // Show success message
        if (feedbackSuccess) {
            feedbackSuccess.style.display = 'block';
        }

        // Reset form after 2 seconds
        setTimeout(() => {
            if (ratingSlider) ratingSlider.value = 3;
            if (ratingValue) ratingValue.textContent = '3';
            if (feedbackComment) feedbackComment.value = '';
            if (feedbackSuccess) feedbackSuccess.style.display = 'none';
        }, 2000);

    } catch (error) {
        console.error('[FEEDBACK] Error:', error);
        showError(error.message || 'Не удалось отправить отзыв. Попробуйте позже.');
    } finally {
        // Re-enable button
        submitFeedbackBtn.disabled = false;
        submitFeedbackBtn.innerHTML = '<span>📤 Отправить отзыв</span>';
    }
}

// Close feedback form
function closeFeedbackForm() {
    const feedbackSection = document.getElementById('feedbackSection');
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    const resultsTitle = document.querySelector('.results-title');
    const actionButtons = document.querySelector('.action-buttons');
    
    // Hide feedback form
    if (feedbackSection) {
        feedbackSection.style.display = 'none';
    }
    
    // Check if there are actual results - if not, hide the entire results section
    if (resultsGrid && resultsGrid.children.length === 0) {
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }
    
    console.log('[FEEDBACK] Feedback form closed');
}

// Show feedback form for testing (without generation)
function showTestFeedbackForm() {
    console.log('[FEEDBACK] showTestFeedbackForm called');
    
    // Show results section to contain the feedback form
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    const resultsTitle = document.querySelector('.results-title');
    const actionButtons = document.querySelector('.action-buttons');
    
    // Check if there are actual results
    const hasResults = resultsGrid && resultsGrid.children.length > 0;
    
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }
    
    if (hasResults) {
        // If there are results, show everything (title, grid, buttons, feedback form)
        // CRITICAL: Always show results grid when results exist
        if (resultsGrid) {
            resultsGrid.style.display = 'grid';
        }
        if (resultsTitle) {
            resultsTitle.style.display = 'block';
        }
        if (actionButtons) {
            actionButtons.style.display = 'flex';
        }
    } else {
        // If no results, hide title, grid, and buttons (test mode)
        if (resultsTitle) {
            resultsTitle.style.display = 'none';
        }
        if (actionButtons) {
            actionButtons.style.display = 'none';
        }
        if (resultsGrid) {
            resultsGrid.style.display = 'none';
        }
    }
    
    // Show feedback form
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection) {
        feedbackSection.style.display = 'block';
        console.log('[FEEDBACK] Feedback section shown');
        
        // Re-attach handler when section is shown
        attachFeedbackHandler();
        
        // Reset form to default values
        const ratingSlider = document.getElementById('ratingSlider');
        const ratingValue = document.getElementById('ratingValue');
        const feedbackComment = document.getElementById('feedbackComment');
        const feedbackSuccess = document.getElementById('feedbackSuccess');
        
        if (ratingSlider) {
            ratingSlider.value = 3;
            console.log('[FEEDBACK] Rating slider reset to 3');
        }
        if (ratingValue) {
            ratingValue.textContent = '3';
        }
        if (feedbackComment) {
            feedbackComment.value = '';
        }
        if (feedbackSuccess) {
            feedbackSuccess.style.display = 'none';
        }
    } else {
        console.error('[FEEDBACK] Feedback section not found!');
    }
    
    // Scroll to feedback form smoothly
    setTimeout(() => {
        if (feedbackSection) {
            feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

// ============================================================
// ADMIN TESTING FUNCTIONS - Hidden from regular users
// ============================================================

/**
 * Test function to show results section with mock data
 * This allows testing the results UI without making API calls
 *
 * Usage:
 * - In browser console: window.testResults()
 * - Or press: Ctrl + Shift + T
 * - Or triple-click on logo (3 fast clicks)
 */
window.testResults = function(count = 3) {
    console.log('🧪 Testing results section with', count, 'mock results');

    // Use real example images from the examples/result folder
    const exampleImages = [
        'examples/result/rs_01.jpg',
        'examples/result/rs_02.jpg',
        'examples/result/rs_03.jpg'
    ];

    // Create mock results data using real example images
    const mockResults = [];
    for (let i = 0; i < Math.min(count, exampleImages.length); i++) {
        mockResults.push({
            result_image: exampleImages[i]
        });
    }

    // Show results section
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }

    // Display results
    displayResults(mockResults);

    // Scroll to results
    setTimeout(() => {
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);

    console.log('✅ Test results displayed successfully');
};

/**
 * Test function to show error state
 */
window.testError = function() {
    console.log('🧪 Testing error state');

    const mockResults = [{
        error: 'Это тестовая ошибка для проверки отображения'
    }];

    if (resultsSection) {
        resultsSection.style.display = 'block';
    }

    displayResults(mockResults);

    setTimeout(() => {
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);

    console.log('✅ Test error displayed successfully');
};

/**
 * Test function to show mixed results (success + error)
 */
window.testMixed = function() {
    console.log('🧪 Testing mixed results (success + error)');

    const mockResults = [
        {
            result_image: 'https://via.placeholder.com/400x600/ec4899/ffffff?text=Успех+1'
        },
        {
            error: 'Ошибка обработки второго изображения'
        },
        {
            result_image: 'https://via.placeholder.com/400x600/8b5cf6/ffffff?text=Успех+2'
        }
    ];

    if (resultsSection) {
        resultsSection.style.display = 'block';
    }

    displayResults(mockResults);

    setTimeout(() => {
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);

    console.log('✅ Test mixed results displayed successfully');
};

// Secret keyboard shortcut: Ctrl + Shift + T
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        console.log('🔐 Secret shortcut activated!');
        window.testResults();
    }
});

// Secret triple-click on logo
let logoClickCount = 0;
let logoClickTimer = null;

const logo = document.querySelector('.logo-container');
if (logo) {
    logo.addEventListener('click', () => {
        logoClickCount++;

        if (logoClickCount === 1) {
            logoClickTimer = setTimeout(() => {
                logoClickCount = 0;
            }, 1000); // Reset after 1 second
        }

        if (logoClickCount === 3) {
            clearTimeout(logoClickTimer);
            logoClickCount = 0;
            console.log('🔐 Secret logo click activated!');
            window.testResults();
        }
    });
}

console.log('🔧 Admin testing functions loaded. Try:');
console.log('   - window.testResults() - Show mock results');
console.log('   - window.testError() - Show error state');
console.log('   - window.testMixed() - Show mixed results');
console.log('   - Ctrl+Shift+T - Quick test shortcut');
console.log('   - Triple-click logo - Hidden trigger');

// ============================================================
// LOGO HOME NAVIGATION
// ============================================================

function goToHome(event) {
    event.preventDefault();
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // Switch to step 1
    setTimeout(() => {
        switchStep(1);
    }, 500);
}
