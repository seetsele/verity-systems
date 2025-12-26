// Initialize EmailJS - YOU'LL ADD YOUR KEY LATER
// emailjs.init(7GJLL6TdVtkeZAXkx); // UNCOMMENT THIS AFTER SETTING UP EMAILJS

// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Contact form
const contactForm = document.getElementById('contactForm');

contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const button = contactForm.querySelector('button');
    button.textContent = 'Sending...';
    button.disabled = true;
    
    // FOR NOW: Just alert (we'll add EmailJS later)
    alert('Form submitted! (EmailJS will be added next)');
    
    // Reset form
    contactForm.reset();
    button.textContent = 'Send Message';
    button.disabled = false;
    /* UNCOMMENT THIS AFTER SETTING UP EMAILJS:
    
    try {
        await emailjs.send(
            'YOUR_SERVICE_ID',
            'YOUR_TEMPLATE_ID',
            {
                from_name: e.target.name.value,
                from_email: e.target.email.value,
                organization: e.target.organization.value,
                org_type: e.target.type.value,
                message: e.target.message.value
            }
        );
        
        alert('✓ Message sent! We\'ll respond within 24 hours.');
        contactForm.reset();
    } catch (error) {
        alert('Error sending. Please email: contact@veritysystems.app');
    } finally {
        button.textContent = 'Send Message';
        button.disabled = false;
    }
    */
});
