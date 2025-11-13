// API Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000'
    : 'https://virtual-tryon-app-production.up.railway.app';

// Global state
let allFeedbacks = [];
let currentFilter = 'all';
let isAuthenticated = false;

// Admin password (в продакшене лучше хранить на backend)
const ADMIN_PASSWORD = 'admin2025';

// Load feedback stats on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if already authenticated
    const savedAuth = sessionStorage.getItem('stats_auth');
    if (savedAuth === 'true') {
        isAuthenticated = true;
        showStatsInterface();
        loadFeedbackStats();
    }
});

// Check password
function checkPassword(event) {
    event.preventDefault();

    const passwordInput = document.getElementById('passwordInput');
    const passwordError = document.getElementById('passwordError');
    const password = passwordInput.value;

    if (password === ADMIN_PASSWORD) {
        // Correct password
        isAuthenticated = true;
        sessionStorage.setItem('stats_auth', 'true');
        passwordError.style.display = 'none';
        showStatsInterface();
        loadFeedbackStats();
    } else {
        // Wrong password
        passwordError.style.display = 'block';
        passwordInput.value = '';
        passwordInput.focus();
    }
}

// Show stats interface
function showStatsInterface() {
    document.getElementById('passwordProtection').style.display = 'none';
    document.querySelector('.stats-header').style.display = 'block';
}

// Load feedback statistics
async function loadFeedbackStats() {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const statsContent = document.getElementById('statsContent');

    // Show loading
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    statsContent.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/api/feedback/list`);

        if (!response.ok) {
            throw new Error(`Ошибка загрузки: ${response.status}`);
        }

        const data = await response.json();
        console.log('Feedback data:', data);

        // Extract feedbacks array based on source
        if (data.source === 'database') {
            allFeedbacks = data.feedbacks || [];
        } else {
            // Convert file format to feedback format
            allFeedbacks = (data.files || [])
                .filter(f => !f.error)
                .map(f => ({
                    rating: f.rating,
                    comment: f.comment,
                    timestamp: f.timestamp,
                    session_id: null
                }));
        }

        // Display statistics
        displayStats(allFeedbacks);

        // Show content
        loadingState.style.display = 'none';
        statsContent.style.display = 'block';

    } catch (error) {
        console.error('Error loading feedback:', error);

        // Show error
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        document.getElementById('errorMessage').textContent = error.message;
    }
}

// Display statistics
function displayStats(feedbacks) {
    // Calculate summary stats
    const totalCount = feedbacks.length;
    const withComments = feedbacks.filter(f => f.comment && f.comment.trim()).length;

    // Calculate average rating
    const avgRating = totalCount > 0
        ? (feedbacks.reduce((sum, f) => sum + f.rating, 0) / totalCount).toFixed(1)
        : '0.0';

    // Count today's feedbacks
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayCount = feedbacks.filter(f => {
        const feedbackDate = new Date(f.timestamp);
        feedbackDate.setHours(0, 0, 0, 0);
        return feedbackDate.getTime() === today.getTime();
    }).length;

    // Update summary cards
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('avgRating').textContent = avgRating;
    document.getElementById('withComments').textContent = withComments;
    document.getElementById('todayCount').textContent = todayCount;

    // Display rating distribution
    displayRatingChart(feedbacks);

    // Display feedback list
    displayFeedbackList(feedbacks, currentFilter);
}

// Display rating distribution chart
function displayRatingChart(feedbacks) {
    const ratingCounts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };

    feedbacks.forEach(f => {
        if (f.rating >= 1 && f.rating <= 5) {
            ratingCounts[f.rating]++;
        }
    });

    const maxCount = Math.max(...Object.values(ratingCounts), 1);
    const chartContainer = document.getElementById('ratingChart');
    chartContainer.innerHTML = '';

    // Create bars for each rating (5 to 1)
    for (let rating = 5; rating >= 1; rating--) {
        const count = ratingCounts[rating];
        const percentage = (count / maxCount) * 100;

        const barItem = document.createElement('div');
        barItem.className = 'rating-bar-item';

        const label = document.createElement('div');
        label.className = 'rating-label';
        label.textContent = '⭐'.repeat(rating);

        const barContainer = document.createElement('div');
        barContainer.className = 'rating-bar-container';

        const barFill = document.createElement('div');
        barFill.className = 'rating-bar-fill';
        barFill.style.width = '0%'; // Start at 0 for animation

        // Animate after a small delay
        setTimeout(() => {
            barFill.style.width = `${percentage}%`;
            if (percentage > 15) {
                barFill.textContent = `${count}`;
            }
        }, 100 + (5 - rating) * 100);

        const countLabel = document.createElement('div');
        countLabel.className = 'rating-count';
        countLabel.textContent = `${count} отзывов`;

        barContainer.appendChild(barFill);
        barItem.appendChild(label);
        barItem.appendChild(barContainer);
        barItem.appendChild(countLabel);
        chartContainer.appendChild(barItem);
    }
}

// Display feedback list
function displayFeedbackList(feedbacks, filter = 'all') {
    const listContainer = document.getElementById('feedbackList');
    listContainer.innerHTML = '';

    // Filter feedbacks
    let filteredFeedbacks = feedbacks;
    if (filter !== 'all') {
        filteredFeedbacks = feedbacks.filter(f => f.rating === parseInt(filter));
    }

    // Sort by timestamp (newest first)
    filteredFeedbacks.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    // Display empty state if no feedbacks
    if (filteredFeedbacks.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">Нет отзывов для отображения</div>
            </div>
        `;
        return;
    }

    // Create feedback items
    filteredFeedbacks.forEach(feedback => {
        const item = document.createElement('div');
        item.className = 'feedback-item';

        const header = document.createElement('div');
        header.className = 'feedback-header';

        const rating = document.createElement('div');
        rating.className = 'feedback-rating';
        rating.textContent = '⭐'.repeat(feedback.rating);

        const date = document.createElement('div');
        date.className = 'feedback-date';
        date.textContent = formatDate(feedback.timestamp);

        header.appendChild(rating);
        header.appendChild(date);

        const comment = document.createElement('div');
        if (feedback.comment && feedback.comment.trim()) {
            comment.className = 'feedback-comment';
            comment.textContent = feedback.comment;
        } else {
            comment.className = 'feedback-comment feedback-no-comment';
            comment.textContent = 'Без комментария';
        }

        item.appendChild(header);
        item.appendChild(comment);

        // Add session ID if available
        if (feedback.session_id) {
            const session = document.createElement('div');
            session.className = 'feedback-session';
            session.textContent = `Session: ${feedback.session_id}`;
            item.appendChild(session);
        }

        listContainer.appendChild(item);
    });
}

// Filter feedback by rating
function filterFeedback(filter) {
    currentFilter = filter;

    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });

    // Display filtered list
    displayFeedbackList(allFeedbacks, filter);
}

// Format date to readable string
function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
        return 'Только что';
    } else if (diffMins < 60) {
        return `${diffMins} мин назад`;
    } else if (diffHours < 24) {
        return `${diffHours} ч назад`;
    } else if (diffDays < 7) {
        return `${diffDays} дн назад`;
    } else {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${day}.${month}.${year} ${hours}:${minutes}`;
    }
}
