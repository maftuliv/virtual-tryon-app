/**
 * Home Dashboard Controller
 * Personalized landing page for logged-in users
 */

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    await auth.checkAuth();

    if (!auth.user) {
        // Redirect to main page if not logged in
        window.location.href = 'index.html';
        return;
    }

    // Load user data and render dashboard
    await initDashboard();
});

async function initDashboard() {
    try {
        // Update user info in UI
        updateUserUI();

        // Load user stats
        await loadUserStats();

        // Load recent tryons (last 6)
        await loadRecentTryons();

    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

function updateUserUI() {
    // Update hero greeting
    const userNameHero = document.getElementById('userNameHero');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    const userStatus = document.getElementById('userStatus');

    const firstName = auth.user.full_name?.split(' ')[0] || auth.user.email.split('@')[0];

    if (userNameHero) {
        userNameHero.textContent = firstName;
    }

    if (userName) {
        userName.textContent = firstName;
    }

    if (userAvatar) {
        if (auth.user.avatar_url) {
            userAvatar.src = auth.user.avatar_url;
        } else {
            // Fallback: generate colored avatar with first letter
            const firstLetter = firstName.charAt(0).toUpperCase();
            userAvatar.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23c084fc'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='0.35em' fill='white' font-size='18' font-weight='600'%3E${firstLetter}%3C/text%3E%3C/svg%3E`;
        }
    }

    if (userStatus) {
        if (auth.user.is_premium) {
            userStatus.textContent = 'Premium';
            userStatus.className = 'user-status-badge premium';
        } else {
            userStatus.textContent = 'Free';
            userStatus.className = 'user-status-badge free';
        }
    }
}

async function loadUserStats() {
    try {
        // Use check-limit endpoint which has correct weekly/monthly logic
        const response = await auth.fetchWithAuth('/api/auth/check-limit');

        if (!response.ok) {
            console.error('Failed to load stats:', response.status);
            return;
        }

        const data = await response.json();

        const statsRemaining = document.getElementById('statsRemaining');
        const statsProgressBar = document.getElementById('statsProgressBar');

        const remaining = data.remaining || 0;
        const used = data.used || 0;
        const limit = data.limit || 50;
        const percentage = limit > 0 ? (used / limit) * 100 : 0;

        if (statsRemaining) {
            if (remaining === 0) {
                statsRemaining.textContent = `Лимит исчерпан`;
            } else {
                statsRemaining.textContent = `${remaining} ${pluralize(remaining, 'примерка', 'примерки', 'примерок')} осталось`;
            }
        }

        if (statsProgressBar) {
            statsProgressBar.style.width = `${percentage}%`;
        }
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

async function loadRecentTryons() {
    const tryonsGrid = document.getElementById('tryonsGrid');
    const tryonsLoading = document.getElementById('tryonsLoading');
    const tryonsEmpty = document.getElementById('tryonsEmpty');

    try {
        const response = await auth.fetchWithAuth('/api/user/tryons?limit=6&offset=0');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Hide loading
        if (tryonsLoading) {
            tryonsLoading.style.display = 'none';
        }

        if (data.success && data.tryons && data.tryons.length > 0) {
            // Hide empty state
            if (tryonsEmpty) {
                tryonsEmpty.style.display = 'none';
            }

            // Render tryons
            const tryonsHTML = data.tryons.map(tryon => createTryonCard(tryon)).join('');
            tryonsGrid.innerHTML = tryonsHTML;

        } else {
            // Show empty state
            if (tryonsEmpty) {
                tryonsEmpty.style.display = 'block';
            }
            tryonsGrid.innerHTML = '';
        }

    } catch (error) {
        console.error('Error loading tryons:', error);

        if (tryonsLoading) {
            tryonsLoading.style.display = 'none';
        }

        if (tryonsEmpty) {
            tryonsEmpty.style.display = 'block';
        }
    }
}

function createTryonCard(tryon) {
    const date = new Date(tryon.created_at);
    const formattedDate = date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short'
    });

    return `
        <div class="tryon-card" onclick="window.location.href='dashboard.html'">
            <img src="${tryon.result_url}" alt="Результат примерки" loading="lazy">
            <div class="tryon-card-overlay">
                <span class="tryon-date">${formattedDate}</span>
            </div>
        </div>
    `;
}

function showWardrobeModal() {
    alert('Функция "Мой гардероб" скоро появится! 👗');
}

function showSubscriptionModal() {
    alert('Функция управления подпиской в разработке! 💎');
}

async function handleLogout() {
    await auth.logout();
    window.location.href = 'index.html';
}

// Helper function for pluralization
function pluralize(number, one, two, five) {
    let n = Math.abs(number);
    n %= 100;
    if (n >= 5 && n <= 20) {
        return five;
    }
    n %= 10;
    if (n === 1) {
        return one;
    }
    if (n >= 2 && n <= 4) {
        return two;
    }
    return five;
}
