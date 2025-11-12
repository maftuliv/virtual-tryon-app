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
const resetBtn = document.getElementById('resetBtn');
const downloadAllBtn = document.getElementById('downloadAllBtn');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const ratingSlider = document.getElementById('ratingSlider');
const ratingValue = document.getElementById('ratingValue');
const feedbackComment = document.getElementById('feedbackComment');
const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
const feedbackSuccess = document.getElementById('feedbackSuccess');
const testFeedbackBtn = document.getElementById('testFeedbackBtn');

// Step Management
let currentStep = 1;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    setupUploadZones();
    setupEventListeners();
    setupStepper();
    checkServerHealth();
});

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

    // Update content visibility with smooth transition
    if (step1Content) {
        if (step === 1) {
            step1Content.style.opacity = '0';
            step1Content.style.display = 'block';
            setTimeout(() => {
                step1Content.style.transition = 'opacity 0.3s ease';
                step1Content.style.opacity = '1';
            }, 10);
        } else {
            step1Content.style.transition = 'opacity 0.3s ease';
            step1Content.style.opacity = '0';
            setTimeout(() => {
                step1Content.style.display = 'none';
            }, 300);
        }
    }
    if (step2Content) {
        if (step === 2) {
            step2Content.style.opacity = '0';
            step2Content.style.display = 'block';
            setTimeout(() => {
                step2Content.style.transition = 'opacity 0.3s ease';
                step2Content.style.opacity = '1';
            }, 10);
        } else {
            step2Content.style.transition = 'opacity 0.3s ease';
            step2Content.style.opacity = '0';
            setTimeout(() => {
                step2Content.style.display = 'none';
            }, 300);
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

    // Generate switch - triggers generation when toggled ON
    if (generateSwitch) {
        generateSwitch.addEventListener('change', (e) => {
            if (e.target.checked) {
                // Switch turned ON - start generation
                handleTryOn();
            } else {
                // Switch turned OFF - do nothing (user can reset manually)
            }
        });
    }

    resetBtn.addEventListener('click', resetApplication);
    downloadAllBtn.addEventListener('click', downloadAllResults);

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

    if (submitFeedbackBtn) {
        submitFeedbackBtn.addEventListener('click', handleFeedbackSubmit);
    }

    // Test feedback button - shows feedback form without generation
    if (testFeedbackBtn) {
        testFeedbackBtn.addEventListener('click', showTestFeedbackForm);
    }

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
    
    // Show notification and suggest moving to step 2
    if (validFiles.length > 0 && currentStep === 1) {
        showInfo('Фото загружено! Теперь перейдите к шагу 2, чтобы добавить одежду.');
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
        // Create a temporary image to get dimensions and analyze
        const tempImg = new Image();
        tempImg.src = imageSrc;

        await new Promise((resolve) => {
            tempImg.onload = resolve;
        });

        const width = tempImg.width;
        const height = tempImg.height;
        const aspectRatio = width / height;

        // Check for common issues
        const warnings = [];
        const errors = [];

        // Resolution checks
        if (width < 512 || height < 512) {
            errors.push('Разрешение слишком низкое (мин. 512px)');
        }

        if (height > 2000 || width > 2000) {
            warnings.push('Будет автоматически уменьшено');
        }

        // Aspect ratio and orientation checks
        if (type === 'person') {
            // For person images, we need portrait orientation (height > width)
            // Typical full-body photos have aspect ratio between 0.5-0.8 (width/height)
            if (width > height) {
                errors.push('❌ Фото должно быть вертикальным (портрет)');
            } else if (aspectRatio > 0.85) {
                // Too square - likely a cropped photo or just upper body
                errors.push('❌ Похоже на обрезанное фото. Нужен человек в ПОЛНЫЙ РОСТ');
            } else if (aspectRatio < 0.4) {
                warnings.push('Необычные пропорции - проверьте результат');
            }

            // Additional hints for person photos
            if (width >= 512 && height >= 512 && width < height && aspectRatio <= 0.85) {
                // Good signs - but still show helpful hint
                if (aspectRatio > 0.65 && aspectRatio <= 0.85) {
                    warnings.push('Убедитесь, что виден человек ПОЛНОСТЬЮ (с ног до головы)');
                }
            }
        } else if (type === 'garment') {
            // For garment images, more flexible
            if (width < 512 && height < 512) {
                errors.push('Разрешение слишком низкое');
            }

            // Garments can be landscape or portrait, but not too extreme
            if (aspectRatio > 2.0 || aspectRatio < 0.5) {
                warnings.push('Необычные пропорции - убедитесь, что одежда видна полностью');
            }
        }

        // Create status badge
        const badge = document.createElement('div');
        badge.className = 'preview-status-badge';

        if (errors.length > 0) {
            // Critical errors - show error badge
            badge.classList.add('status-error');
            badge.innerHTML = '<span class="status-icon">❌</span><span>' + errors[0] + '</span>';
            previewDiv.classList.add('has-errors');
            badge.title = errors.join('\n');

            // Show detailed error message
            setTimeout(() => {
                showError('⚠️ Проблема с изображением:\n\n' + errors.join('\n') + '\n\nПожалуйста, загрузите другое фото.');
            }, 300);
        } else if (warnings.length > 0) {
            // Warnings - might still work
            badge.classList.add('status-warning');
            badge.innerHTML = '<span class="status-icon">⚠️</span><span>' + warnings[0] + '</span>';
            previewDiv.classList.add('has-warnings');
            badge.title = warnings.join('\n');
        } else {
            // All good
            badge.classList.add('status-ok');
            badge.innerHTML = '<span class="status-icon">✅</span><span>OK</span>';
            previewDiv.classList.add('validated-ok');
        }

        previewDiv.appendChild(badge);

        console.log(`[VALIDATION] ${type} - ${width}x${height}, ratio: ${aspectRatio.toFixed(2)}, errors: ${errors.length}, warnings: ${warnings.length}`);

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

// Update Generate Switch State
function updateGenerateSwitch() {
    const hasPersonImages = state.personImages.length > 0;
    const hasGarmentImage = state.garmentImage !== null;
    const hasErrors = document.querySelectorAll('.preview-item.has-errors').length > 0;
    const canGenerate = hasPersonImages && hasGarmentImage && !hasErrors;

    if (generateSwitch) {
        // Disable switch if images not ready
        generateSwitch.disabled = !canGenerate;
    }
}

// Handle Try-On Process
async function handleTryOn() {
    try {
        // Disable switch
        if (generateSwitch) {
            generateSwitch.disabled = true;
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

        // Check person detection results
        console.log('[UPLOAD] Upload data received:', uploadData);
        console.log('[UPLOAD] Person detection data:', uploadData.person_detection);
        console.log('[UPLOAD] Can proceed:', uploadData.can_proceed);

        if (uploadData.person_detection) {
            console.log('[UPLOAD] Calling displayPersonDetectionResults...');
            displayPersonDetectionResults(uploadData.person_detection);
        } else {
            console.warn('[UPLOAD] ⚠️ No person_detection data in upload response');
        }

        // Block proceeding if person not detected
        if (uploadData.can_proceed === false) {
            console.error('[UPLOAD] ❌ Cannot proceed - person not detected');
            throw new Error('❌ Человек не обнаружен на фото. Пожалуйста, загрузите фото человека в полный рост.');
        }

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
        
        // Re-enable switch (but keep it checked)
        if (generateSwitch) {
            generateSwitch.disabled = false;
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
        // Reset switch on error
        if (generateSwitch) {
            generateSwitch.checked = false;
            generateSwitch.disabled = false;
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

        const card = document.createElement('div');
        card.className = 'result-card';

        const img = document.createElement('img');
        img.src = result.result_image;
        img.alt = `Result ${index + 1}`;

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

        const info = document.createElement('div');
        info.className = 'result-info';

        const title = document.createElement('h3');
        title.textContent = `Результат ${index + 1}`;

        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.innerHTML = '💾 Скачать';
        downloadBtn.onclick = () => downloadResult(result.result_image, index);

        info.appendChild(title);
        info.appendChild(downloadBtn);

        card.appendChild(img);
        card.appendChild(info);

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

    // Show feedback form after results are displayed
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection && successCount > 0) {
        feedbackSection.style.display = 'block';
        // Reset form
        if (ratingSlider) ratingSlider.value = 3;
        if (ratingValue) ratingValue.textContent = '3';
        if (feedbackComment) feedbackComment.value = '';
        if (feedbackSuccess) feedbackSuccess.style.display = 'none';
    }
}

// Download Single Result
function downloadResult(imageData, index) {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `virtual-tryon-result-${index + 1}.png`;
    link.click();
}

// Download All Results
function downloadAllResults() {
    const resultImages = resultsGrid.querySelectorAll('img');

    resultImages.forEach((img, index) => {
        setTimeout(() => {
            downloadResult(img.src, index);
        }, index * 200); // Delay to avoid blocking
    });
}

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

    // Reset generate switch
    if (generateSwitch) {
        generateSwitch.checked = false;
        generateSwitch.disabled = false;
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

// Person Detection Results Display
function displayPersonDetectionResults(detectionResults) {
    console.log('[PERSON DETECTION] ========================================');
    console.log('[PERSON DETECTION] Results received:', detectionResults);
    console.log('[PERSON DETECTION] Number of results:', detectionResults.length);

    // Update preview badges with detection results
    detectionResults.forEach(result => {
        console.log(`[PERSON DETECTION] Processing result for image ${result.image_index}:`, result);

        const previewItems = document.querySelectorAll('.preview-item');
        console.log(`[PERSON DETECTION] Found ${previewItems.length} preview items`);

        if (previewItems[result.image_index]) {
            const previewItem = previewItems[result.image_index];
            console.log(`[PERSON DETECTION] Found preview item for index ${result.image_index}`);

            // Remove old badge if exists
            const oldBadge = previewItem.querySelector('.preview-status-badge');
            if (oldBadge) {
                console.log(`[PERSON DETECTION] Removing old badge`);
                oldBadge.remove();
            } else {
                console.log(`[PERSON DETECTION] No old badge found`);
            }

            // Create new badge based on detection result
            const badge = document.createElement('div');
            badge.className = 'preview-status-badge';
            badge.style.cursor = 'pointer';

            if (result.error || !result.person_detected) {
                // Critical error - person not detected
                badge.classList.add('status-error');
                badge.innerHTML = '<span class="status-icon">❌</span><span>Человек не обнаружен</span>';
                previewItem.classList.add('has-errors');
            } else if (result.confidence < 0.5) {
                // Low confidence warning
                badge.classList.add('status-warning');
                badge.innerHTML = '<span class="status-icon">⚠️</span><span>Низкая уверенность</span>';
                previewItem.classList.add('has-warnings');
            } else if (!result.is_full_body) {
                // Not full body warning
                badge.classList.add('status-warning');
                badge.innerHTML = '<span class="status-icon">⚠️</span><span>Не полный рост</span>';
                previewItem.classList.add('has-warnings');
            } else {
                // Success
                badge.classList.add('status-success');
                badge.innerHTML = `<span class="status-icon">✅</span><span>Человек обнаружен (${Math.round(result.confidence * 100)}%)</span>`;
                previewItem.classList.add('has-success');
            }

            // Add click handler to show detailed info
            badge.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log(`[PERSON DETECTION] Badge clicked for image ${result.image_index + 1}`);
                showDetectionDetails(result, result.image_index + 1);
            });

            console.log(`[PERSON DETECTION] Appending new clickable badge to preview item`);
            previewItem.appendChild(badge);
            console.log(`[PERSON DETECTION] Badge successfully added`);
        } else {
            console.error(`[PERSON DETECTION] ❌ Preview item not found for index ${result.image_index}`);
        }
    });
    console.log('[PERSON DETECTION] ======================================== DONE');
}

// Show detailed detection information in a modal
function showDetectionDetails(result, imageNumber) {
    const modal = document.createElement('div');
    modal.className = 'validation-detail-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        padding: 20px;
    `;

    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        border-radius: 16px;
        padding: 24px;
        max-width: 500px;
        width: 100%;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    `;

    let statusIcon = '❌';
    let statusText = 'Ошибка';
    let statusColor = '#ef4444';

    if (result.person_detected) {
        if (result.confidence >= 0.7 && result.is_full_body) {
            statusIcon = '✅';
            statusText = 'Отлично';
            statusColor = '#10b981';
        } else {
            statusIcon = '⚠️';
            statusText = 'Требует внимания';
            statusColor = '#f59e0b';
        }
    }

    let detailsHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 48px; margin-bottom: 12px;">${statusIcon}</div>
            <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 20px;">Фото ${imageNumber}</h3>
            <p style="margin: 0; color: ${statusColor}; font-weight: 600; font-size: 16px;">${statusText}</p>
        </div>

        <div style="background: #f3f4f6; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 12px 0; color: #1f2937; font-size: 14px; font-weight: 600;">Результаты анализа:</h4>
    `;

    if (result.person_detected) {
        detailsHTML += `
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #6b7280;">Человек обнаружен:</span>
                <span style="color: #10b981; font-weight: 600;">✓ Да</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #6b7280;">Уверенность AI:</span>
                <span style="font-weight: 600;">${Math.round(result.confidence * 100)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #6b7280;">Фото в полный рост:</span>
                <span style="font-weight: 600; color: ${result.is_full_body ? '#10b981' : '#f59e0b'}">
                    ${result.is_full_body ? '✓ Да' : '⚠ Возможно нет'}
                </span>
            </div>
            ${result.height_ratio ? `
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #6b7280;">Охват кадра по высоте:</span>
                <span style="font-weight: 600;">${Math.round(result.height_ratio * 100)}%</span>
            </div>
            ` : ''}
        `;
    } else {
        detailsHTML += `
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #6b7280;">Человек обнаружен:</span>
                <span style="color: #ef4444; font-weight: 600;">✗ Нет</span>
            </div>
        `;
    }

    detailsHTML += `</div>`;

    // Add warnings section
    if (result.warnings && result.warnings.length > 0) {
        detailsHTML += `
            <div style="background: #fef3c7; border: 1px solid #fbbf24; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #92400e; font-size: 14px; font-weight: 600;">Рекомендации:</h4>
        `;

        result.warnings.forEach(warning => {
            detailsHTML += `
                <div style="display: flex; align-items: start; margin-bottom: 8px; color: #92400e;">
                    <span style="margin-right: 8px;">•</span>
                    <span style="font-size: 14px;">${warning}</span>
                </div>
            `;
        });

        detailsHTML += `</div>`;
    }

    // Add recommendations for improvement
    if (result.critical || !result.person_detected) {
        detailsHTML += `
            <div style="background: #fee2e2; border: 1px solid #ef4444; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #991b1b; font-size: 14px; font-weight: 600;">Как исправить:</h4>
                <div style="color: #991b1b; font-size: 14px; line-height: 1.6;">
                    • Загрузите фото человека в полный рост<br>
                    • Убедитесь, что человек хорошо виден<br>
                    • Используйте хорошее освещение<br>
                    • Избегайте сильного размытия
                </div>
            </div>
        `;
    } else if (!result.is_full_body || result.confidence < 0.7) {
        detailsHTML += `
            <div style="background: #fef3c7; border: 1px solid #fbbf24; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #92400e; font-size: 14px; font-weight: 600;">Для лучшего результата:</h4>
                <div style="color: #92400e; font-size: 14px; line-height: 1.6;">
                    • Сфотографируйте человека в полный рост<br>
                    • Расположите камеру на уровне груди<br>
                    • Убедитесь что видны ноги до стоп<br>
                    • Человек должен занимать большую часть кадра
                </div>
            </div>
        `;
    }

    detailsHTML += `
        <button onclick="this.closest('.validation-detail-modal').remove()"
                style="width: 100%; padding: 12px; background: #3b82f6; color: white;
                       border: none; border-radius: 8px; font-size: 16px; font-weight: 600;
                       cursor: pointer;">
            Понятно
        </button>
    `;

    content.innerHTML = detailsHTML;
    modal.appendChild(content);

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    document.body.appendChild(modal);
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

// Handle Feedback Submission
async function handleFeedbackSubmit() {
    if (!ratingSlider || !submitFeedbackBtn) return;

    const rating = parseInt(ratingSlider.value);
    const comment = feedbackComment ? feedbackComment.value.trim() : '';

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

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Feedback error:', errorData);
            throw new Error(errorData.error || 'Ошибка отправки отзыва');
        }

        const result = await response.json();
        console.log('Feedback submitted successfully:', result);

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
        console.error('Error submitting feedback:', error);
        showError('Не удалось отправить отзыв. Попробуйте позже.');
    } finally {
        // Re-enable button
        submitFeedbackBtn.disabled = false;
        submitFeedbackBtn.innerHTML = '<span>📤 Отправить отзыв</span>';
    }
}

// Show feedback form for testing (without generation)
function showTestFeedbackForm() {
    // Hide results section if it's showing
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }
    
    // Hide results grid (no actual results)
    const resultsGrid = document.getElementById('resultsGrid');
    if (resultsGrid) {
        resultsGrid.innerHTML = `
            <div class="no-results" style="text-align: center; padding: 40px;">
                <span style="font-size: 3em;">🧪</span>
                <h3>Тестовый режим</h3>
                <p>Форма обратной связи показана для тестирования</p>
                <p style="color: #64748b; font-size: 0.9em;">Генерация не выполнялась</p>
            </div>
        `;
    }
    
    // Show feedback form
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection) {
        feedbackSection.style.display = 'block';
        // Reset form
        if (ratingSlider) ratingSlider.value = 3;
        if (ratingValue) ratingValue.textContent = '3';
        if (feedbackComment) feedbackComment.value = '';
        if (feedbackSuccess) feedbackSuccess.style.display = 'none';
    }
    
    // Scroll to feedback form
    if (feedbackSection) {
        feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
