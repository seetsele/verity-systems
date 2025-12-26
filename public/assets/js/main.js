// ================================================
// VERITY SYSTEMS - GSAP ANIMATIONS
// ================================================

gsap.registerPlugin(ScrollTrigger);

// Prevent animations on first load for smoother experience
const mm = gsap.matchMedia();

// ================================================
// HERO ANIMATIONS
// ================================================

// Animate hero lines on load
function animateHeroTitle() {
    const lines = document.querySelectorAll('.line');
    
    gsap.from(lines, {
        duration: 0.8,
        y: 120,
        opacity: 0,
        stagger: 0.15,
        ease: 'power4.out'
    });
}

// Animate hero buttons
function animateHeroButtons() {
    const buttons = document.querySelectorAll('.hero-buttons .btn');
    
    gsap.from(buttons, {
        duration: 0.8,
        y: 30,
        opacity: 0,
        stagger: 0.2,
        delay: 0.4,
        ease: 'power3.out'
    });
}

// Run hero animations on page load
window.addEventListener('load', () => {
    animateHeroTitle();
    animateHeroButtons();
});

// ================================================
// SCROLL ANIMATIONS
// ================================================

// Service cards animation
const serviceCards = document.querySelectorAll('.service-item');
serviceCards.forEach((card, index) => {
    gsap.from(card, {
        scrollTrigger: {
            trigger: card,
            start: 'top 80%',
            end: 'top 60%',
            scrub: 0.5
        },
        duration: 0.6,
        y: 40,
        opacity: 0,
        ease: 'power3.out'
    });
});

// Process cards animation with stagger
gsap.from('.process-card', {
    scrollTrigger: {
        trigger: '.process',
        start: 'top 75%'
    },
    duration: 0.6,
    y: 40,
    opacity: 0,
    stagger: 0.1,
    ease: 'power3.out'
});

// Feature cards animation
gsap.from('.feature-card', {
    scrollTrigger: {
        trigger: '.features',
        start: 'top 75%'
    },
    duration: 0.6,
    y: 40,
    opacity: 0,
    stagger: 0.08,
    ease: 'power3.out'
});

// Pricing cards animation
gsap.from('.pricing-card', {
    scrollTrigger: {
        trigger: '.pricing',
        start: 'top 75%'
    },
    duration: 0.6,
    y: 40,
    opacity: 0,
    stagger: 0.12,
    ease: 'power3.out'
});

// ================================================
// HOVER ANIMATIONS
// ================================================

// Card hover effects
const allCards = document.querySelectorAll('.service-item, .process-card, .feature-card, .pricing-card');

allCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        gsap.to(this, {
            duration: 0.3,
            y: -8,
            boxShadow: '0 20px 40px rgba(0, 217, 255, 0.1)',
            ease: 'power2.out'
        });
    });

    card.addEventListener('mouseleave', function() {
        gsap.to(this, {
            duration: 0.3,
            y: 0,
            boxShadow: '0 0px 0px rgba(0, 217, 255, 0)',
            ease: 'power2.out'
        });
    });
});

// Button hover effects
const buttons = document.querySelectorAll('.btn');

buttons.forEach(btn => {
    btn.addEventListener('mouseenter', function() {
        gsap.to(this, {
            duration: 0.3,
            y: -2,
            ease: 'power2.out'
        });
    });

    btn.addEventListener('mouseleave', function() {
        gsap.to(this, {
            duration: 0.3,
            y: 0,
            ease: 'power2.out'
        });
    });
});

// ================================================
// SMOOTH SCROLL BEHAVIOR
// ================================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            gsap.to(window, {
                duration: 0.8,
                scrollTo: {
                    y: target,
                    autoKill: false
                },
                ease: 'power2.inOut'
            });
        }
    });
});

// ================================================
// FORM ANIMATIONS
// ================================================

const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    const inputs = contactForm.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            gsap.to(this, {
                duration: 0.3,
                scale: 1.02,
                ease: 'power2.out'
            });
        });

        input.addEventListener('blur', function() {
            gsap.to(this, {
                duration: 0.3,
                scale: 1,
                ease: 'power2.out'
            });
        });
    });

    // Form submission animation
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const button = this.querySelector('button');
        const originalText = button.textContent;
        
        gsap.to(button, {
            duration: 0.3,
            scale: 0.95,
            ease: 'back.out'
        });

        setTimeout(() => {
            button.textContent = '✓ Message Sent!';
            gsap.to(button, {
                duration: 0.3,
                scale: 1,
                ease: 'back.out'
            });

            setTimeout(() => {
                button.textContent = originalText;
                this.reset();
            }, 2000);
        }, 500);
    });
}

// ================================================
// NAVIGATION ACTIVE LINK ANIMATION
// ================================================

const navLinks = document.querySelectorAll('.nav-links a');

window.addEventListener('scroll', () => {
    let current = '';
    
    const sections = document.querySelectorAll('section[id]');
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        
        if (scrollY >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').slice(1) === current) {
            link.classList.add('active');
        }
    });
});

// ================================================
// PARALLAX EFFECT FOR BACKGROUND LOGOS
// ================================================

window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    
    const bgLogos = document.querySelectorAll('.logo-bg');
    bgLogos.forEach((logo, index) => {
        const speed = 0.5 + (index * 0.1);
        gsap.to(logo, {
            duration: 0,
            y: scrolled * speed * 0.1
        });
    });
});

// ================================================
// PAGE LOAD ANIMATION
// ================================================

gsap.from('body', {
    duration: 0.6,
    opacity: 0,
    ease: 'power2.out'
});

console.log('%c✓ Verity Systems Loaded', 'color: #00d9ff; font-size: 14px; font-weight: bold;');
