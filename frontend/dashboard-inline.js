/**
 * Inline Dashboard Logic
 * Shows dashboard on main page for logged-in users
 */

// ============================================================
// DASHBOARD / UPLOAD INTERFACE TOGGLE
// ============================================================

function showDashboard() {
    // Hide upload interface
    const heroSection = document.querySelector('.hero-section');
    const stepperNav = document.querySelector('.stepper-nav');
    const uploadSection = document.querySelector('.upload-section-main');
    const sidebar = document.querySelector('.sidebar-section');

    if (heroSection) heroSection.style.display = 'none';
    if (stepperNav) stepperNav.style.display = 'none';
    if (uploadSection) uploadSection.style.display = 'none';
    if (sidebar) sidebar.style.display = 'none';

    // Show dashboard
    const dashboard = document.getElementById('userDashboard');
    if (dashboard) {
        dashboard.style.display = 'block';
        // Initialize dashboard data
        initDashboard();
    }
}

function showUploadInterface() {
    // Show upload interface
    const heroSection = document.querySelector('.hero-section');
    const stepperNav = document.querySelector('.stepper-nav');
    const uploadSection = document.querySelector('.upload-section-main');
    const sidebar = document.querySelector('.sidebar-section');

    if (heroSection) heroSection.style.display = 'block';
    if (stepperNav) stepperNav.style.display = 'block';
    if (uploadSection) uploadSection.style.display = 'block';
    if (sidebar) sidebar.style.display = 'block';

    // Hide dashboard
    const dashboard = document.getElementById('userDashboard');
    if (dashboard) dashboard.style.display = 'none';
}

// Dashboard initialization
async function initDashboard() {
    try {
        // Update user info
        updateDashboardUI();

        // Load stats
        await loadDashboardStats();

        // Load recent tryons
        await loadDashboardTryons();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

function updateDashboardUI() {
    if (!auth.user) return;

    const firstName = auth.user.full_name?.split(' ')[0] || auth.user.email.split('@')[0];

    // Update greeting
    const greetingName = document.getElementById('dashboardGreetingName');
    if (greetingName) greetingName.textContent = firstName;

    // Update user pill
    const userPillName = document.getElementById('dashboardUserName');
    const userPillAvatar = document.getElementById('dashboardUserAvatar');
    const userPillBadge = document.getElementById('dashboardUserBadge');

    if (userPillName) userPillName.textContent = firstName;

    if (userPillAvatar) {
        const firstLetter = firstName.charAt(0).toUpperCase();
        userPillAvatar.textContent = firstLetter;
    }

    if (userPillBadge) {
        userPillBadge.textContent = auth.user.is_premium ? 'Premium' : 'Free';
    }
}

async function loadDashboardStats() {
    try {
        const response = await auth.fetchWithAuth('/api/auth/check-limit');
        if (!response.ok) return;

        const data = await response.json();

        const remaining = data.remaining || 0;
        const used = data.used || 0;
        const limit = data.limit || 50;
        const percentage = limit > 0 ? (used / limit) * 100 : 0;

        // Update premium count
        const premiumCount = document.getElementById('dashboardPremiumCount');
        if (premiumCount) {
            premiumCount.textContent = remaining + ' примерок осталось в этом месяце';
        }

        // Update progress bar
        const progressBar = document.querySelector('.premium-progress-fill');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

async function loadDashboardTryons() {
    try {
        const response = await auth.fetchWithAuth('/api/user/tryons?limit=4&offset=0');
        if (!response.ok) return;

        const data = await response.json();

        const tryonsContainer = document.getElementById('dashboardTryonsContainer');
        if (!tryonsContainer) return;

        if (data.success && data.tryons && data.tryons.length > 0) {
            const tryonsHTML = data.tryons.map(tryon => createDashboardTryonCard(tryon)).join('');
            tryonsContainer.innerHTML = tryonsHTML;
        } else {
            tryonsContainer.innerHTML = '<div class="tryon-card"><div class="tryon-thumb">Нет примерок</div></div>';
        }
    } catch (error) {
        console.error('Error loading dashboard tryons:', error);
    }
}

function createDashboardTryonCard(tryon) {
    const date = new Date(tryon.created_at);
    const formattedDate = date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    const title = tryon.title || 'Примерка';

    return '<div class="tryon-card">' +
        '<div class="tryon-thumb" style="background-image: url(\'' + tryon.result_url + '\'); background-size: cover; background-position: center;"></div>' +
        '<div class="tryon-body">' +
        '<div class="tryon-name">' + title + '</div>' +
        '<div class="tryon-date">' + formattedDate + '</div>' +
        '<div class="tryon-actions">' +
        '<button class="btn-small btn-small-solid" onclick="window.location.href=\'dashboard.html\'">Открыть</button>' +
        '<a class="btn-small btn-small-outline" href="' + tryon.result_url + '" download>Скачать</a>' +
        '</div>' +
        '</div>' +
        '</div>';
}

function createNewLook() {
    // Switch to upload interface to create a new look
    showUploadInterface();
    // Scroll to upload section
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
