/**
 * Dashboard page controller for user's try-on history
 */

// State
let tryons = [];
let currentOffset = 0;
let hasMore = false;
let currentFilter = 'all';
let currentTryonId = null;
const LIMIT = 20;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    await auth.checkAuth();

    if (!auth.user) {
        // Redirect to main page if not logged in
        window.location.href = 'index.html';
        return;
    }

    // Update UI with user info
    updateUserUI();

    // Load dashboard data
    await Promise.all([
        loadStats(),
        loadTryons()
    ]);

    // Setup event listeners
    setupEventListeners();
});

function updateUserUI() {
    const userName = document.getElementById('userName');
    const userStatus = document.getElementById('userStatus');
    const userAvatar = document.getElementById('userAvatar');

    if (auth.user) {
        userName.textContent = auth.user.full_name || auth.user.email.split('@')[0];

        if (auth.user.is_premium) {
            userStatus.textContent = 'Premium';
            userStatus.className = 'user-status-badge premium';
        } else {
            userStatus.textContent = 'Free';
            userStatus.className = 'user-status-badge free';
        }

        if (auth.user.avatar_url) {
            userAvatar.src = auth.user.avatar_url;
        }
    }
}

async function loadStats() {
    try {
        const response = await auth.fetchWithAuth('/api/user/tryons/stats');

        if (!response.ok) {
            console.error('Failed to load stats:', response.status);
            return;
        }

        const data = await response.json();

        if (data.success && data.stats) {
            document.getElementById('statTotal').textContent = data.stats.total || 0;
            document.getElementById('statFavorites').textContent = data.stats.favorites || 0;
            document.getElementById('statStorage').textContent = `${data.stats.storage_used_mb || 0} MB`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadTryons(reset = true) {
    if (reset) {
        currentOffset = 0;
        tryons = [];
    }

    const galleryGrid = document.getElementById('galleryGrid');
    const galleryLoading = document.getElementById('galleryLoading');
    const emptyState = document.getElementById('emptyState');
    const loadMoreContainer = document.getElementById('loadMoreContainer');

    if (reset) {
        galleryLoading.style.display = 'block';
        emptyState.style.display = 'none';
        loadMoreContainer.style.display = 'none';
    }

    try {
        const response = await auth.fetchWithAuth(
            `/api/user/tryons?limit=${LIMIT}&offset=${currentOffset}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            if (reset) {
                tryons = data.tryons || [];
            } else {
                tryons = [...tryons, ...(data.tryons || [])];
            }

            hasMore = data.has_more || false;
            currentOffset += data.tryons.length;

            renderGallery();
        }
    } catch (error) {
        console.error('Error loading tryons:', error);
        galleryLoading.style.display = 'none';
        if (tryons.length === 0) {
            galleryGrid.innerHTML = '<p class="error-message">Ошибка загрузки. Попробуйте обновить страницу.</p>';
        }
    }
}

function renderGallery() {
    const galleryGrid = document.getElementById('galleryGrid');
    const galleryLoading = document.getElementById('galleryLoading');
    const emptyState = document.getElementById('emptyState');
    const loadMoreContainer = document.getElementById('loadMoreContainer');

    galleryLoading.style.display = 'none';

    // Filter tryons
    let filteredTryons = tryons;
    if (currentFilter === 'favorites') {
        filteredTryons = tryons.filter(t => t.is_favorite);
    }

    if (filteredTryons.length === 0) {
        galleryGrid.innerHTML = '';
        emptyState.style.display = 'block';
        loadMoreContainer.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';

    // Render gallery items
    const galleryHTML = filteredTryons.map(tryon => createTryonCard(tryon)).join('');
    galleryGrid.innerHTML = galleryHTML;

    // Show load more button if there are more items
    loadMoreContainer.style.display = hasMore ? 'block' : 'none';
}

function createTryonCard(tryon) {
    const date = new Date(tryon.created_at);
    const formattedDate = date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });

    const categoryLabels = {
        'tops': 'Верх',
        'bottoms': 'Низ',
        'one-pieces': 'Цельное',
        'auto': 'Авто'
    };
    const categoryLabel = categoryLabels[tryon.category] || tryon.category;

    const favoriteIcon = tryon.is_favorite ? '⭐' : '☆';
    const favoriteClass = tryon.is_favorite ? 'is-favorite' : '';

    return `
        <div class="gallery-item ${favoriteClass}" data-id="${tryon.id}">
            <div class="gallery-image-wrapper" onclick="openImageModal(${tryon.id})">
                <img src="${tryon.result_url}" alt="Результат примерки" class="gallery-image" loading="lazy">
                <div class="gallery-overlay">
                    <span class="gallery-view-icon">🔍</span>
                </div>
            </div>
            <div class="gallery-item-footer">
                <div class="gallery-item-info">
                    <span class="gallery-date">${formattedDate}</span>
                    <span class="gallery-category">${categoryLabel}</span>
                </div>
                <div class="gallery-item-actions">
                    <button class="gallery-action-btn favorite-btn" onclick="toggleFavorite(${tryon.id}, event)" title="Избранное">
                        ${favoriteIcon}
                    </button>
                    <a class="gallery-action-btn download-btn" href="${tryon.result_url}" download="tryon-${tryon.id}.png" title="Скачать">
                        ⬇️
                    </a>
                </div>
            </div>
        </div>
    `;
}

async function toggleFavorite(tryonId, event) {
    if (event) event.stopPropagation();

    const tryon = tryons.find(t => t.id === tryonId);
    if (!tryon) return;

    const newState = !tryon.is_favorite;

    try {
        const response = await auth.fetchWithAuth(`/api/user/tryons/${tryonId}/favorite`, {
            method: 'POST',
            body: JSON.stringify({ is_favorite: newState })
        });

        if (response.ok) {
            tryon.is_favorite = newState;
            renderGallery();

            // Update stats
            const statFavorites = document.getElementById('statFavorites');
            const currentCount = parseInt(statFavorites.textContent) || 0;
            statFavorites.textContent = newState ? currentCount + 1 : currentCount - 1;
        } else {
            console.error('Failed to toggle favorite');
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

function openImageModal(tryonId) {
    const tryon = tryons.find(t => t.id === tryonId);
    if (!tryon) return;

    currentTryonId = tryonId;

    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalDate = document.getElementById('modalDate');
    const modalCategory = document.getElementById('modalCategory');
    const modalFavoriteIcon = document.getElementById('modalFavoriteIcon');
    const modalDownloadBtn = document.getElementById('modalDownloadBtn');

    modalImage.src = tryon.result_url;
    modalDownloadBtn.href = tryon.result_url;

    const date = new Date(tryon.created_at);
    modalDate.textContent = date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    const categoryLabels = {
        'tops': 'Верхняя одежда',
        'bottoms': 'Нижняя одежда',
        'one-pieces': 'Цельная одежда',
        'auto': 'Автоопределение'
    };
    modalCategory.textContent = categoryLabels[tryon.category] || tryon.category;

    modalFavoriteIcon.textContent = tryon.is_favorite ? '⭐' : '☆';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeImageModal(event) {
    if (event && event.target !== event.currentTarget) return;

    const modal = document.getElementById('imageModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    currentTryonId = null;
}

async function toggleFavoriteFromModal() {
    if (!currentTryonId) return;

    await toggleFavorite(currentTryonId);

    // Update modal icon
    const tryon = tryons.find(t => t.id === currentTryonId);
    if (tryon) {
        const modalFavoriteIcon = document.getElementById('modalFavoriteIcon');
        modalFavoriteIcon.textContent = tryon.is_favorite ? '⭐' : '☆';
    }
}

function loadMore() {
    loadTryons(false);
}

function setupEventListeners() {
    // Filter buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderGallery();
        });
    });

    // Sort select
    const sortSelect = document.getElementById('sortSelect');
    sortSelect.addEventListener('change', () => {
        const sortOrder = sortSelect.value;
        if (sortOrder === 'oldest') {
            tryons.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        } else {
            tryons.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        }
        renderGallery();
    });

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeImageModal();
        }
    });
}

async function handleLogout() {
    await auth.logout();
    window.location.href = 'index.html';
}
