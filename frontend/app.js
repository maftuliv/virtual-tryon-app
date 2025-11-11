// API Configuration
const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000' : '';

// State Management
const state = {
    personImages: [],
    garmentImage: null,
    uploadedPersonPaths: [],
    uploadedGarmentPath: null,
    sessionId: null
};

// DOM Elements
const personImagesInput = document.getElementById('personImages');
const garmentImageInput = document.getElementById('garmentImage');
const personUploadZone = document.getElementById('personUploadZone');
const garmentUploadZone = document.getElementById('garmentUploadZone');
const personPreview = document.getElementById('personPreview');
const garmentPreview = document.getElementById('garmentPreview');
const tryonBtn = document.getElementById('tryonBtn');
const progressBar = document.getElementById('progressBar');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const resetBtn = document.getElementById('resetBtn');
const downloadAllBtn = document.getElementById('downloadAllBtn');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    setupUploadZones();
    setupEventListeners();
    checkServerHealth();
});

function setupUploadZones() {
    // Person images upload - only trigger if clicking on upload zone itself, not previews
    personUploadZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on preview items or remove buttons
        if (e.target.closest('.preview-item') || e.target.closest('.preview-remove')) {
            return;
        }
        personImagesInput.click();
    });
    personImagesInput.addEventListener('change', handlePersonImagesSelect);

    // Garment image upload - only trigger if clicking on upload zone itself, not previews
    garmentUploadZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on preview items or remove buttons
        if (e.target.closest('.preview-item') || e.target.closest('.preview-remove')) {
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
    tryonBtn.addEventListener('click', handleTryOn);
    resetBtn.addEventListener('click', resetApplication);
    downloadAllBtn.addEventListener('click', downloadAllResults);
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
    processPersonImages(files);
    // Clear input value to allow selecting the same file again
    e.target.value = '';
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
    updateTryOnButton();
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
    processGarmentImage(file);
    // Clear input value to allow selecting the same file again
    e.target.value = '';
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
    updateTryOnButton();
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

    const img = document.createElement('img');
    img.src = src;
    img.alt = type === 'person' ? 'Person Image' : 'Garment Image';

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

// Remove Images
function removePersonImage(index) {
    state.personImages.splice(index, 1);
    displayPersonPreviews();
    updateTryOnButton();
}

function removeGarmentImage() {
    state.garmentImage = null;
    garmentPreview.innerHTML = '';
    garmentImageInput.value = '';
    updateTryOnButton();
}

// Update Try-On Button State
function updateTryOnButton() {
    const hasPersonImages = state.personImages.length > 0;
    const hasGarmentImage = state.garmentImage !== null;

    tryonBtn.disabled = !(hasPersonImages && hasGarmentImage);
}

// Handle Try-On Process
async function handleTryOn() {
    try {
        // Disable button
        tryonBtn.disabled = true;
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

        state.uploadedPersonPaths = uploadData.person_images;
        state.uploadedGarmentPath = uploadData.garment_image;
        state.sessionId = uploadData.session_id;

        // Step 2: Perform virtual try-on
        updateProgressText('Обработка с помощью FASHN AI... (5-17 секунд)');

        const tryonResponse = await fetch(`${API_URL}/api/tryon`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                person_images: state.uploadedPersonPaths,
                garment_image: state.uploadedGarmentPath
            })
        });

        if (!tryonResponse.ok) {
            const errorData = await tryonResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Ошибка обработки изображений');
        }

        const tryonData = await tryonResponse.json();

        if (!tryonData.success) {
            throw new Error(tryonData.error || 'Обработка не удалась');
        }

        // Check if we have results
        if (!tryonData.results || tryonData.results.length === 0) {
            throw new Error('Не удалось получить результаты. Проверьте настройки FASHN API.');
        }

        // Display results
        displayResults(tryonData.results);

        // Hide progress, show results
        progressBar.style.display = 'none';
        resultsSection.style.display = 'block';

    } catch (error) {
        console.error('Error:', error);

        // More detailed error message
        let errorMsg = error.message;

        // FASHN API specific errors
        if (error.message.includes('POSE_ERROR')) {
            errorMsg = '❌ Не удалось определить позу человека\n\n' +
                       'Требования к фото:\n' +
                       '• Человек в полный рост\n' +
                       '• Четкое изображение\n' +
                       '• Хорошее освещение\n' +
                       '• Тело хорошо видно\n' +
                       '• Простой фон';
        } else if (error.message.includes('IMAGE_LOAD_ERROR')) {
            errorMsg = '❌ Не удалось загрузить изображение\n\n' +
                       'Проверьте:\n' +
                       '• Формат файла (JPG или PNG)\n' +
                       '• Размер не более 10MB\n' +
                       '• Файл не поврежден';
        } else if (error.message.includes('CONTENT_ERROR')) {
            errorMsg = '❌ Обнаружен запрещенный контент\n\n' +
                       'Используйте подходящие изображения';
        } else if (error.message.includes('FORMAT_ERROR')) {
            errorMsg = '❌ Неверный формат изображения\n\n' +
                       'Используйте JPG или PNG файлы';
        } else if (error.message.includes('FASHN_API_KEY')) {
            errorMsg = '⚙️ API ключ FASHN не настроен\n\nОбратитесь к администратору';
        } else if (error.message.includes('401')) {
            errorMsg = '🔑 Неверный API ключ FASHN\n\nПроверьте настройки';
        } else if (error.message.includes('402')) {
            errorMsg = '💳 Недостаточно кредитов FASHN\n\nПополните баланс';
        } else if (error.message.includes('timeout')) {
            errorMsg = '⏱️ Превышено время ожидания\n\nПопробуйте снова';
        }

        showError(errorMsg);
        progressBar.style.display = 'none';
        tryonBtn.disabled = false;
    }
}

// Update progress text
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

            // Parse FASHN API specific errors
            let errorMsg = result.error;
            let errorTitle = 'Ошибка обработки изображения';

            if (result.error.includes('POSE_ERROR')) {
                errorTitle = 'Не удалось определить позу человека';
                errorMsg = 'Требования к фото:\n• Человек в полный рост\n• Четкое изображение\n• Хорошее освещение\n• Тело хорошо видно\n• Простой фон';
            } else if (result.error.includes('IMAGE_LOAD_ERROR')) {
                errorTitle = 'Не удалось загрузить изображение';
                errorMsg = 'Проверьте:\n• Формат файла (JPG или PNG)\n• Размер не более 10MB\n• Файл не поврежден';
            } else if (result.error.includes('CONTENT_ERROR')) {
                errorTitle = 'Обнаружен запрещенный контент';
                errorMsg = 'Используйте подходящие изображения';
            } else if (result.error.includes('FORMAT_ERROR')) {
                errorTitle = 'Неверный формат изображения';
                errorMsg = 'Используйте JPG или PNG файлы';
            }

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

    // Reset button
    tryonBtn.disabled = true;

    // Hide error
    hideError();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
