/**
 * Verity Loading Screen - Instagram-style splash screen
 * Include this script in <head> to automatically add loading screen
 */
(function() {
    // Create loading screen HTML
    const loadingHTML = `
    <div id="verity-loading-screen" style="position:fixed;top:0;left:0;width:100%;height:100%;background:#000;z-index:9999;display:flex;align-items:center;justify-content:center;transition:opacity 0.4s ease;">
        <div style="animation:verity-pulse 1.5s ease-in-out infinite;">
            <svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="verityLoadGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#22d3ee"/>
                        <stop offset="50%" stop-color="#6366f1"/>
                        <stop offset="100%" stop-color="#a855f7"/>
                    </linearGradient>
                </defs>
                <path d="M50 8L58 12V28L50 32L42 28V12L50 8Z" fill="url(#verityLoadGrad)" opacity="0.9"/>
                <path d="M50 8C70 8 88 24 92 44L76 48C74 34 63 22 50 22V8Z" fill="url(#verityLoadGrad)" opacity="0.7"/>
                <path d="M92 44C96 64 86 84 68 92L60 78C72 72 80 58 76 48L92 44Z" fill="url(#verityLoadGrad)" opacity="0.5"/>
                <path d="M68 92C48 100 26 92 14 74L28 64C36 76 52 82 60 78L68 92Z" fill="url(#verityLoadGrad)" opacity="0.4"/>
                <path d="M14 74C2 54 8 32 26 18L36 32C24 42 20 58 28 64L14 74Z" fill="url(#verityLoadGrad)" opacity="0.3"/>
                <path d="M26 18C40 6 50 8 50 8V22C50 22 42 20 36 32L26 18Z" fill="url(#verityLoadGrad)" opacity="0.2"/>
                <path d="M35 45L47 57L68 36" stroke="url(#verityLoadGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
        </div>
    </div>
    <style>
        @keyframes verity-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(0.92); opacity: 0.6; }
        }
    </style>`;

    // Insert at start of body
    document.addEventListener('DOMContentLoaded', function() {
        document.body.insertAdjacentHTML('afterbegin', loadingHTML);
    });

    // Hide loading screen when page is fully loaded
    window.addEventListener('load', function() {
        const loader = document.getElementById('verity-loading-screen');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(function() {
                loader.remove();
            }, 400);
        }
    });
})();
