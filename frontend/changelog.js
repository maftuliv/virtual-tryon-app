// Timeline Slider Logic
let currentSlide = 0;
const slides = document.querySelectorAll('.timeline-item');
const totalSlides = slides.length;

const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const progressBar = document.getElementById('progressBar');
const timelineDots = document.getElementById('timelineDots');

// Create dots
function createDots() {
    slides.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.className = 'timeline-dot';
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        timelineDots.appendChild(dot);
    });
}

// Update UI
function updateUI() {
    // Update slides
    slides.forEach((slide, index) => {
        slide.classList.remove('active', 'prev');
        if (index === currentSlide) {
            slide.classList.add('active');
        } else if (index < currentSlide) {
            slide.classList.add('prev');
        }
    });

    // Update progress bar
    const progress = ((currentSlide + 1) / totalSlides) * 100;
    progressBar.style.width = `${progress}%`;

    // Update dots
    const dots = document.querySelectorAll('.timeline-dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });

    // Update buttons
    prevBtn.disabled = currentSlide === 0;
    nextBtn.disabled = currentSlide === totalSlides - 1;
}

// Navigation functions
function nextSlide() {
    if (currentSlide < totalSlides - 1) {
        currentSlide++;
        updateUI();
    }
}

function prevSlide() {
    if (currentSlide > 0) {
        currentSlide--;
        updateUI();
    }
}

function goToSlide(index) {
    currentSlide = index;
    updateUI();
}

// Event listeners
prevBtn.addEventListener('click', prevSlide);
nextBtn.addEventListener('click', nextSlide);

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        prevSlide();
    } else if (e.key === 'ArrowRight') {
        nextSlide();
    }
});

// Touch/swipe support
let touchStartX = 0;
let touchEndX = 0;

const slider = document.getElementById('timelineSlider');

slider.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
});

slider.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swipe left - next slide
            nextSlide();
        } else {
            // Swipe right - previous slide
            prevSlide();
        }
    }
}

// Auto-play (optional)
let autoplayInterval;
const autoplayDelay = 5000; // 5 seconds

function startAutoplay() {
    autoplayInterval = setInterval(() => {
        if (currentSlide < totalSlides - 1) {
            nextSlide();
        } else {
            currentSlide = 0;
            updateUI();
        }
    }, autoplayDelay);
}

function stopAutoplay() {
    clearInterval(autoplayInterval);
}

// Stop autoplay on user interaction
[prevBtn, nextBtn, slider].forEach(element => {
    element.addEventListener('click', stopAutoplay);
    element.addEventListener('touchstart', stopAutoplay);
});

// Initialize
createDots();
updateUI();

// Optional: Start autoplay (commented out by default)
// startAutoplay();

console.log('📜 Changelog page loaded. Use arrow keys or swipe to navigate!');
