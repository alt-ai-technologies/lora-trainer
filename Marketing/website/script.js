// Mobile Menu Toggle
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');
const navActions = document.querySelector('.nav-actions');

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-open');
        navActions.classList.toggle('mobile-open');
        mobileMenuToggle.classList.toggle('active');
    });
}

// Smooth Scroll for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar Scroll Effect
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

// Intersection Observer for Fade-in Animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .pricing-card, .testimonial-card, .step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    observer.observe(el);
});

// Counter Animation for Stats
const animateCounter = (element, target, duration = 2000) => {
    let start = 0;
    const increment = target / (duration / 16);
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target + (element.textContent.includes('+') ? '+' : '');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start) + (element.textContent.includes('+') ? '+' : '');
        }
    }, 16);
};

// Observe stats for counter animation
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
            const statNumber = entry.target.querySelector('.stat-number');
            if (statNumber) {
                const text = statNumber.textContent;
                const number = parseInt(text.replace(/\D/g, ''));
                if (number) {
                    statNumber.textContent = '0';
                    animateCounter(statNumber, number, 2000);
                    entry.target.classList.add('animated');
                }
            }
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat').forEach(stat => {
    statsObserver.observe(stat);
});

// Form Validation (for future signup forms)
const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
};

// Add click handlers for CTA buttons
document.querySelectorAll('a[href="#signup"]').forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        // In a real implementation, this would open a signup modal or redirect
        console.log('Signup clicked');
        alert('Signup functionality coming soon!');
    });
});

// Add click handlers for demo buttons
document.querySelectorAll('a[href="#demo"]').forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        // In a real implementation, this would open a video modal
        console.log('Demo clicked');
        alert('Demo video coming soon!');
    });
});

// Pricing Card Hover Effect Enhancement
document.querySelectorAll('.pricing-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px) scale(1.02)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
    });
});

// Code Window Syntax Highlighting (basic)
const codeContent = document.querySelector('.code-content code');
if (codeContent) {
    const code = codeContent.textContent;
    // Simple keyword highlighting
    const keywords = ['model:', 'train:', 'dataset_folder:', 'steps:', 'batch_size:'];
    let highlightedCode = code;
    
    keywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword})`, 'g');
        highlightedCode = highlightedCode.replace(regex, '<span style="color: #60a5fa;">$1</span>');
    });
    
    codeContent.innerHTML = highlightedCode;
}

// Console welcome message
console.log('%cLoRA Trainer', 'font-size: 24px; font-weight: bold; color: #6366f1;');
console.log('%cTrain Custom AI Models, Your Way', 'font-size: 14px; color: #6b7280;');
console.log('%cBuilt with ❤️ by the LoRA Trainer team', 'font-size: 12px; color: #9ca3af;');

