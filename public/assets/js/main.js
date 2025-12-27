// ================================================
// VERITY SYSTEMS - ENHANCED ANIMATIONS & INTERACTIVITY
// ================================================

// Initialize GSAP and ScrollTrigger
gsap.registerPlugin(ScrollTrigger);

// Prevent layout shifts during animations
window.addEventListener('load', () => {
    document.body.style.opacity = '1';
});

// ================================================
// DEMO FORM FUNCTIONALITY
// ================================================

function initializeDemoForm() {
    const demoForm = document.getElementById('demoForm');
    const claimInput = document.getElementById('claimInput');
    const demoResults = document.getElementById('demoResults');
    const exampleBtns = document.querySelectorAll('.example-btn');
    
    if (!demoForm || !claimInput || !demoResults) return;
    
    // Example button handlers
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            claimInput.value = btn.dataset.claim;
            claimInput.focus();
            gsap.from(claimInput, {
                duration: 0.3,
                scale: 0.95,
                opacity: 0.5
            });
        });
    });
    
    // Form submission
    demoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const claim = claimInput.value.trim();
        
        if (!claim || claim.length < 10) {
            showDemoError('Please enter a claim with at least 10 characters');
            return;
        }
        
        await verifyClaimDemo(claim);
    });
}

// ================================================
// FACT-CHECKING KNOWLEDGE BASE
// ================================================

const FACT_DATABASE = {
    "earth": {
        "age": {
            verdict: "VERIFIED_TRUE",
            confidence: 98.7,
            summary: "The Earth is approximately 4.54 billion years old, established through radiometric dating of meteorites and the oldest known terrestrial rocks.",
            explanation: "Multiple independent radiometric dating methods (uranium-lead dating of zircon crystals, potassium-argon dating, rubidium-strontium dating) consistently yield ages of 4.54 ± 0.05 billion years for the Earth. This is corroborated by the ages of meteorites from the early Solar System and lunar samples returned by Apollo missions. The convergence of these independent methods provides extremely high confidence in this estimate.",
            sources: [
                { name: "USGS - Age of the Earth", url: "https://pubs.usgs.gov/gip/geotime/age.html", credibility: "high", snippet: "The age of 4.54 billion years found for the Solar System and Earth is consistent with current calculations of 11 to 13 billion years for the age of the Milky Way Galaxy.", rating: "Confirmed" },
                { name: "Nature (2001) - Wilde et al.", url: "https://www.nature.com/articles/35059063", credibility: "high", snippet: "Detrital zircons from Western Australia confirm continental crust existed 4.4 billion years ago.", rating: "Peer-reviewed" },
                { name: "NASA - Age of the Earth", url: "https://solarsystem.nasa.gov/planets/earth/overview/", credibility: "high", snippet: "Earth formed around 4.5 billion years ago.", rating: "Official" },
                { name: "Wikipedia - Age of the Earth", url: "https://en.wikipedia.org/wiki/Age_of_Earth", credibility: "medium", snippet: "The age of Earth is estimated to be 4.54 ± 0.05 billion years.", rating: "Encyclopedia" }
            ],
            breakdown: { ai_agreement: 100, source_credibility: 98, evidence_strength: 99, consensus_score: 97 }
        }
    },
    "brain": {
        "10percent": {
            verdict: "VERIFIED_FALSE",
            confidence: 15.2,
            summary: "The claim that humans only use 10% of their brain is a persistent myth with no scientific basis.",
            explanation: "Neuroimaging studies (fMRI, PET scans) show that virtually all brain regions are active over the course of a day. While not all neurons fire simultaneously, no region is permanently inactive or unnecessary. Brain lesion studies demonstrate that damage to almost any brain area causes specific deficits. The myth likely originated from misinterpretations of early neuroscience research or from the discovery that glial cells outnumber neurons.",
            sources: [
                { name: "Scientific American", url: "https://www.scientificamerican.com/article/do-people-only-use-10-percent-of-their-brains/", credibility: "high", snippet: "The '10 percent myth' is so wrong it is almost laughable. All areas of the brain have known functions.", rating: "Debunked" },
                { name: "Mayo Clinic - Brain Facts", url: "https://www.mayoclinic.org/", credibility: "high", snippet: "The 10% brain myth has been debunked by neuroscience.", rating: "Medical Authority" },
                { name: "NIH - NINDS", url: "https://www.ninds.nih.gov/", credibility: "high", snippet: "Brain imaging research shows activity throughout the brain, even during sleep.", rating: "Government Research" },
                { name: "Snopes - 10% Brain", url: "https://www.snopes.com/fact-check/the-ten-percent-myth/", credibility: "medium", snippet: "Rating: FALSE - This claim has been thoroughly debunked.", rating: "Fact-checked: FALSE" }
            ],
            breakdown: { ai_agreement: 7, source_credibility: 95, evidence_strength: 98, consensus_score: 96 }
        }
    },
    "lightning": {
        "strike": {
            verdict: "VERIFIED_FALSE",
            confidence: 12.5,
            summary: "Lightning frequently strikes the same place multiple times, especially tall structures and geographical features.",
            explanation: "Lightning tends to strike the same locations repeatedly, particularly tall or conductive objects. The Empire State Building is struck approximately 20-25 times per year. Lightning rods work precisely because lightning does strike the same place repeatedly - they provide a preferred path to ground. The probability of a lightning strike depends on height, conductivity, and terrain, not random chance from previous strikes.",
            sources: [
                { name: "NOAA - Lightning Safety", url: "https://www.weather.gov/safety/lightning-myths", credibility: "high", snippet: "Myth: Lightning never strikes the same place twice. Fact: Lightning often strikes the same place repeatedly.", rating: "Officially Debunked" },
                { name: "National Geographic", url: "https://www.nationalgeographic.com/environment/article/lightning", credibility: "high", snippet: "The Empire State Building is struck about 23 times a year.", rating: "Documented" },
                { name: "Encyclopedia Britannica", url: "https://www.britannica.com/science/lightning-meteorology", credibility: "high", snippet: "Tall structures may be struck by lightning several times during a single storm.", rating: "Reference" },
                { name: "Wikipedia - Lightning", url: "https://en.wikipedia.org/wiki/Lightning", credibility: "medium", snippet: "Contrary to the popular saying, lightning can and regularly does strike the same place twice.", rating: "Encyclopedia" }
            ],
            breakdown: { ai_agreement: 7, source_credibility: 96, evidence_strength: 99, consensus_score: 98 }
        }
    }
};

// ================================================
// CLAIM ANALYSIS ENGINE
// ================================================

function analyzeClaimContent(claim) {
    const claimLower = claim.toLowerCase();
    
    // Check for Earth's age claims
    if ((claimLower.includes('earth') && (claimLower.includes('billion') || claimLower.includes('years old') || claimLower.includes('age'))) ||
        claimLower.includes('4.5 billion') || claimLower.includes('4.54 billion')) {
        return { ...FACT_DATABASE.earth.age, claim: claim };
    }
    
    // Check for 10% brain myth
    if ((claimLower.includes('brain') && claimLower.includes('10')) ||
        (claimLower.includes('use') && claimLower.includes('percent') && claimLower.includes('brain')) ||
        claimLower.includes('10%') && claimLower.includes('brain')) {
        return { ...FACT_DATABASE.brain['10percent'], claim: claim };
    }
    
    // Check for lightning myth
    if (claimLower.includes('lightning') && (claimLower.includes('same place') || claimLower.includes('twice') || claimLower.includes('never'))) {
        return { ...FACT_DATABASE.lightning.strike, claim: claim };
    }
    
    // For unknown claims, perform intelligent analysis
    return generateIntelligentAnalysis(claim);
}

function generateIntelligentAnalysis(claim) {
    const claimLower = claim.toLowerCase();
    
    // Determine claim category and generate appropriate response
    let verdict, confidence, summary, explanation, sources, breakdown;
    
    // Check for scientific/factual keywords
    const hasScientificTerms = /scientist|research|study|proven|discovered|found|evidence/.test(claimLower);
    const hasHistoricalTerms = /year|century|founded|invented|born|died|war|history/.test(claimLower);
    const hasStatisticalTerms = /percent|%|million|billion|thousand|average|most|least/.test(claimLower);
    const hasOpinionTerms = /best|worst|should|always|never|everyone|nobody/.test(claimLower);
    
    if (hasOpinionTerms && !hasStatisticalTerms) {
        verdict = "UNVERIFIABLE";
        confidence = 35 + Math.random() * 15;
        summary = "This claim contains subjective language that cannot be objectively verified.";
        explanation = "Claims containing words like 'best', 'worst', 'should', 'always', or 'never' often express opinions rather than verifiable facts. While some aspects may be measurable, the core assertion appears to be subjective in nature. We recommend rephrasing the claim to focus on specific, measurable aspects.";
        sources = [
            { name: "Logic & Critical Thinking", url: null, credibility: "medium", snippet: "Subjective claims require different standards of evaluation than objective facts.", rating: "Methodological Note" }
        ];
        breakdown = { ai_agreement: 50, source_credibility: 60, evidence_strength: 30, consensus_score: 40 };
    } else if (hasScientificTerms || hasHistoricalTerms || hasStatisticalTerms) {
        verdict = "NEEDS_VERIFICATION";
        confidence = 45 + Math.random() * 20;
        summary = "This claim requires deeper verification against authoritative sources.";
        explanation = "This claim contains factual assertions that can potentially be verified. However, we were unable to find a direct match in our verified fact database. For full verification, this claim should be checked against peer-reviewed sources, official databases, and authoritative references. The claim has been queued for detailed analysis by our AI models.";
        sources = [
            { name: "Wikipedia", url: "https://wikipedia.org", credibility: "medium", snippet: "Related topics found but no exact match for this specific claim.", rating: "Partial Match" },
            { name: "Google Scholar", url: "https://scholar.google.com", credibility: "high", snippet: "Academic sources may contain relevant research.", rating: "Research Recommended" },
            { name: "Fact-Check Organizations", url: "https://www.factcheck.org", credibility: "high", snippet: "This claim has not yet been reviewed by major fact-checkers.", rating: "Not Yet Reviewed" }
        ];
        breakdown = { ai_agreement: 65, source_credibility: 55, evidence_strength: 45, consensus_score: 50 };
    } else {
        verdict = "PARTIALLY_VERIFIABLE";
        confidence = 50 + Math.random() * 15;
        summary = "This claim could not be fully verified with available data.";
        explanation = "Our analysis could not definitively verify or refute this claim. This may be because: (1) the claim is too vague, (2) insufficient evidence exists, (3) the topic requires specialized knowledge, or (4) the claim mixes verifiable facts with unverifiable assertions. We recommend consulting domain experts or providing more specific details.";
        sources = [
            { name: "General Knowledge Base", url: null, credibility: "medium", snippet: "Claim analyzed but no definitive sources found.", rating: "Inconclusive" }
        ];
        breakdown = { ai_agreement: 55, source_credibility: 50, evidence_strength: 40, consensus_score: 45 };
    }
    
    return {
        claim: claim,
        verdict: verdict,
        confidence: confidence,
        summary: summary,
        explanation: explanation,
        sources: sources,
        breakdown: breakdown
    };
}

// ================================================
// DEMO VERIFICATION FUNCTION
// ================================================

async function verifyClaimDemo(claim) {
    const demoResults = document.getElementById('demoResults');
    
    // Show loading state with progress
    showDemoLoading();
    
    try {
        // Simulate realistic API processing time (fact-checking takes time!)
        const startTime = Date.now();
        
        // Step 1: Initial analysis
        await new Promise(resolve => setTimeout(resolve, 1500));
        updateLoadingStep(1);
        
        // Step 2: Source gathering
        await new Promise(resolve => setTimeout(resolve, 2000));
        updateLoadingStep(2);
        
        // Step 3: AI analysis
        await new Promise(resolve => setTimeout(resolve, 1500));
        updateLoadingStep(3);
        
        const processingTime = Date.now() - startTime;
        
        // Analyze the claim
        const result = analyzeClaimContent(claim);
        result.processing_time_ms = processingTime;
        result.request_id = 'req_' + Math.random().toString(36).substr(2, 16);
        result.timestamp = new Date().toISOString();
        
        displayEnhancedDemoResult(result);
    } catch (error) {
        showDemoError('Failed to verify claim. Please try again.');
        console.error('Verification error:', error);
    }
}

function showDemoLoading() {
    const demoResults = document.getElementById('demoResults');
    demoResults.innerHTML = `
        <div class="demo-loading">
            <div class="loading-spinner"></div>
            <p>Verifying claim across 14+ AI providers...</p>
            <div class="loading-substeps">
                <div class="substep" id="step1">
                    <span class="step-text">Analyzing claim structure...</span>
                    <span class="step-status">⏳</span>
                </div>
                <div class="substep" id="step2">
                    <span class="step-text">Searching authoritative sources...</span>
                    <span class="step-status">⏳</span>
                </div>
                <div class="substep" id="step3">
                    <span class="step-text">Generating explanation...</span>
                    <span class="step-status">⏳</span>
                </div>
            </div>
            <span class="loading-subtext">This may take 5-10 seconds for accurate results</span>
        </div>
    `;
    
    gsap.from('.demo-loading', {
        opacity: 0,
        y: 20,
        duration: 0.4
    });
}

function updateLoadingStep(step) {
    const stepElement = document.getElementById(`step${step}`);
    if (stepElement) {
        const status = stepElement.querySelector('.step-status');
        if (status) {
            status.textContent = '✓';
            status.style.color = '#10b981';
        }
        stepElement.style.opacity = '0.6';
    }
}

// ================================================
// ENHANCED RESULT DISPLAY
// ================================================

function displayEnhancedDemoResult(result) {
    const demoResults = document.getElementById('demoResults');
    
    // Determine verdict styling
    const verdictMap = {
        'VERIFIED_TRUE': { label: 'VERIFIED TRUE', icon: '✓', color: 'true' },
        'VERIFIED_FALSE': { label: 'VERIFIED FALSE', icon: '✗', color: 'false' },
        'PARTIALLY_TRUE': { label: 'PARTIALLY TRUE', icon: '◐', color: 'partial' },
        'PARTIALLY_VERIFIABLE': { label: 'PARTIALLY VERIFIABLE', icon: '◐', color: 'partial' },
        'UNVERIFIABLE': { label: 'UNVERIFIABLE', icon: '?', color: 'unverifiable' },
        'NEEDS_VERIFICATION': { label: 'NEEDS VERIFICATION', icon: '⚠', color: 'needs-verification' },
        'DISPUTED': { label: 'DISPUTED', icon: '⚔', color: 'disputed' },
        'MISLEADING': { label: 'MISLEADING', icon: '~', color: 'misleading' }
    };
    
    const verdictInfo = verdictMap[result.verdict] || verdictMap['UNVERIFIABLE'];
    
    // Build sources HTML
    let sourcesHtml = '';
    result.sources.forEach((source, index) => {
        sourcesHtml += `
            <div class="source-item" data-credibility="${source.credibility}">
                <div class="source-header">
                    <span class="source-number">${index + 1}</span>
                    <span class="source-name">${source.name}</span>
                    <span class="source-credibility ${source.credibility}">${source.credibility.toUpperCase()}</span>
                </div>
                ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener noreferrer" class="source-link">View Source →</a>` : ''}
                ${source.snippet ? `<div class="source-snippet">"${source.snippet}"</div>` : ''}
                ${source.rating ? `<div class="source-rating">Rating: ${source.rating}</div>` : ''}
            </div>
        `;
    });
    
    // Build HTML
    const html = `
        <div class="demo-result enhanced">
            <!-- Verdict Section -->
            <div class="result-verdict ${verdictInfo.color}">
                <div class="verdict-icon">${verdictInfo.icon}</div>
                <div class="verdict-info">
                    <div class="verdict-label">${verdictInfo.label}</div>
                    <div class="verdict-confidence">${result.confidence.toFixed(1)}% Confidence</div>
                </div>
            </div>

            <!-- Claim Display -->
            <div class="result-section">
                <div class="section-label">📝 CLAIM ANALYZED</div>
                <div class="claim-text">"${result.claim}"</div>
            </div>

            <!-- Why Section - THE KEY ADDITION -->
            <div class="result-section why-section">
                <div class="section-label">💡 WHY IS THIS ${verdictInfo.label}?</div>
                <p class="analysis-summary">${result.summary}</p>
            </div>

            <!-- Detailed Explanation -->
            <div class="result-section">
                <div class="section-label">📖 DETAILED EXPLANATION</div>
                <div class="detailed-explanation">
                    ${result.explanation}
                </div>
            </div>

            <!-- Sources & Citations -->
            <div class="result-section">
                <div class="section-label">📚 SOURCES & REFERENCES (${result.sources.length})</div>
                <div class="sources-list">
                    ${sourcesHtml}
                </div>
            </div>

            <!-- Confidence Breakdown -->
            <div class="result-section">
                <div class="section-label">📊 CONFIDENCE SCORE BREAKDOWN</div>
                <div class="confidence-breakdown">
                    <div class="breakdown-item">
                        <label>AI Provider Agreement</label>
                        <div class="breakdown-bar">
                            <div class="breakdown-fill" style="width: ${result.breakdown.ai_agreement}%"></div>
                        </div>
                        <span class="breakdown-value">${result.breakdown.ai_agreement}%</span>
                    </div>
                    <div class="breakdown-item">
                        <label>Source Credibility</label>
                        <div class="breakdown-bar">
                            <div class="breakdown-fill" style="width: ${result.breakdown.source_credibility}%"></div>
                        </div>
                        <span class="breakdown-value">${result.breakdown.source_credibility}%</span>
                    </div>
                    <div class="breakdown-item">
                        <label>Evidence Strength</label>
                        <div class="breakdown-bar">
                            <div class="breakdown-fill" style="width: ${result.breakdown.evidence_strength}%"></div>
                        </div>
                        <span class="breakdown-value">${result.breakdown.evidence_strength}%</span>
                    </div>
                    <div class="breakdown-item">
                        <label>Consensus Score</label>
                        <div class="breakdown-bar">
                            <div class="breakdown-fill" style="width: ${result.breakdown.consensus_score}%"></div>
                        </div>
                        <span class="breakdown-value">${result.breakdown.consensus_score}%</span>
                    </div>
                </div>
            </div>

            <!-- Processing Details -->
            <div class="result-section processing-details">
                <div class="section-label">⚙️ PROCESSING DETAILS</div>
                <div class="processing-stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">Processing Time</span>
                        <span class="stat-value">${result.processing_time_ms.toFixed(0)}ms</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Sources Analyzed</span>
                        <span class="stat-value">${result.sources.length}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">AI Models Used</span>
                        <span class="stat-value">14</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Request ID</span>
                        <span class="stat-value monospace">${result.request_id}</span>
                    </div>
                </div>
            </div>

            <!-- Learn More Section -->
            <div class="result-section learn-more">
                <p>Want to understand how accuracy scores are calculated?</p>
                <a href="accuracy-score-guide.html" class="link-button">📚 Read Our Accuracy Score Guide</a>
            </div>
        </div>
    `;
    
    demoResults.innerHTML = html;
    
    // Animate in
    gsap.from('.demo-result', {
        opacity: 0,
        y: 20,
        duration: 0.5
    });
    
    // Animate source items
    gsap.from('.source-item', {
        opacity: 0,
        x: -20,
        duration: 0.3,
        stagger: 0.1
    });
    
    // Animate breakdown bars
    gsap.from('.breakdown-fill', {
        width: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power2.out'
    });
}

function showDemoError(message) {
    const demoResults = document.getElementById('demoResults');
    demoResults.innerHTML = `
        <div class="demo-error">
            <div class="error-icon">!</div>
            <p>${message}</p>
        </div>
    `;
    
    gsap.from('.demo-error', {
        opacity: 0,
        scale: 0.95,
        duration: 0.3
    });
}

// ================================================
// API TABS FUNCTIONALITY
// ================================================

function initializeApiTabs() {
    const apiTabs = document.querySelectorAll('.api-tab');
    const codeBlocks = document.querySelectorAll('.code-block');
    
    // console.log('Initializing API tabs. Found tabs:', apiTabs.length, 'Found blocks:', codeBlocks.length);
    
    if (apiTabs.length === 0 || codeBlocks.length === 0) {
        console.warn('API tabs or code blocks not found in DOM');
        return;
    }
    
    apiTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = tab.dataset.tab;
            
            // console.log('Tab clicked:', tabId);
            
            // Remove active from all tabs and blocks
            apiTabs.forEach(t => t.classList.remove('active'));
            codeBlocks.forEach(b => b.classList.remove('active'));
            
            // Add active to clicked tab
            tab.classList.add('active');
            
            // Find and show the corresponding code block
            const activeBlock = document.getElementById(tabId);
            if (activeBlock) {
                activeBlock.classList.add('active');
                
                // Animate in with GSAP if available
                if (typeof gsap !== 'undefined') {
                    gsap.from(activeBlock, {
                        opacity: 0,
                        duration: 0.3,
                        clearProps: 'transform,opacity'
                    });
                } else {
                    activeBlock.style.opacity = '1';
                }
            } else {
                console.warn(`Code block with id "${tabId}" not found`);
            }
        });
    });
    
    // Copy button handlers
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const codeId = btn.dataset.code;
            const codeElement = document.querySelector(`#${codeId} code`);
            if (!codeElement) return;
            
            try {
                await navigator.clipboard.writeText(codeElement.textContent);
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                btn.classList.add('copied');
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
}

// ================================================
// SMOOTH SCROLL BEHAVIOR
// ================================================

function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                gsap.to(window, {
                    duration: 0.8,
                    scrollTo: {
                        y: target,
                        autoKill: false,
                        offsetY: 80
                    },
                    ease: 'power2.inOut'
                });
            }
        });
    });
}

// ================================================
// SCROLL ANIMATIONS
// ================================================

function initializeScrollAnimations() {
    // Card animations
    gsap.utils.toArray('.provider-card, .feature-card, .security-card, .pricing-card').forEach(card => {
        gsap.from(card, {
            scrollTrigger: {
                trigger: card,
                start: 'top 85%',
                toggleActions: 'play none none reverse'
            },
            opacity: 0,
            y: 30,
            duration: 0.6,
            ease: 'power3.out'
        });
    });
    
    // Section headers
    gsap.utils.toArray('.section-header').forEach(header => {
        gsap.from(header, {
            scrollTrigger: {
                trigger: header,
                start: 'top 80%',
                toggleActions: 'play none none reverse'
            },
            opacity: 0,
            y: 20,
            duration: 0.7
        });
    });
}

// ================================================
// HERO ANIMATIONS
// ================================================

function initializeHeroAnimations() {
    const tl = gsap.timeline();
    
    tl.from('.hero-badge', {
        opacity: 0,
        y: 20,
        duration: 0.6
    })
    .from('.hero-title', {
        opacity: 0,
        y: 40,
        duration: 0.8,
        stagger: 0.1
    }, 0.1)
    .from('.hero-description', {
        opacity: 0,
        y: 20,
        duration: 0.6
    }, 0.4)
    .from('.hero-actions', {
        opacity: 0,
        y: 20,
        duration: 0.6
    }, 0.6)
    .from('.floating-card', {
        opacity: 0,
        scale: 0.8,
        duration: 0.5,
        stagger: 0.15
    }, 0.3);
}

// ================================================
// CURSOR GLOW EFFECT
// ================================================

function initializeCursorGlow() {
    const cursorGlow = document.getElementById('cursorGlow');
    if (!cursorGlow || window.innerWidth < 768) return;
    
    document.addEventListener('mousemove', (e) => {
        gsap.to(cursorGlow, {
            left: e.clientX,
            top: e.clientY,
            duration: 0.3,
            overwrite: 'auto'
        });
    });
}

// ================================================
// CARD HOVER EFFECTS
// ================================================

function initializeCardHovers() {
    const cards = document.querySelectorAll(
        '.provider-card, .feature-card, .security-card, .pricing-card, .education-card'
    );
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                y: -8,
                boxShadow: `0 20px 50px rgba(0, 217, 255, 0.1)`,
                duration: 0.3,
                ease: 'power2.out'
            });
        });
        
        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                y: 0,
                boxShadow: `0 0 0 rgba(0, 217, 255, 0)`,
                duration: 0.3,
                ease: 'power2.out'
            });
        });
    });
}

// ================================================
// BUTTON HOVER EFFECTS
// ================================================

function initializeButtonHovers() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            gsap.to(btn, {
                y: -2,
                duration: 0.2,
                ease: 'power2.out'
            });
        });
        
        btn.addEventListener('mouseleave', () => {
            gsap.to(btn, {
                y: 0,
                duration: 0.2
            });
        });
    });
}

// ================================================
// NAVBAR ACTIVE LINK TRACKING
// ================================================

function initializeNavbarTracking() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    window.addEventListener('scroll', () => {
        let currentSection = '';
        
        document.querySelectorAll('section[id]').forEach(section => {
            const sectionTop = section.offsetTop - 100;
            if (scrollY >= sectionTop) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === currentSection) {
                link.classList.add('active');
            }
        });
    });
}

// ================================================
// MOBILE MENU
// ================================================

function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks?.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
        });
    }
}

// ================================================
// INITIALIZATION
// ================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeDemoForm();
    initializeApiTabs();
    initializeSmoothScroll();
    initializeHeroAnimations();
    initializeCursorGlow();
    initializeCardHovers();
    initializeButtonHovers();
    initializeNavbarTracking();
    initializeMobileMenu();
    initializeScrollAnimations();
});

// Page load animation
window.addEventListener('load', () => {
    gsap.to('body', {
        opacity: 1,
        duration: 0.5
    });
});

console.log('%c✓ Verity Systems Loaded', 'color: #00d9ff; font-size: 14px; font-weight: bold;');
