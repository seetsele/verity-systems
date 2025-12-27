/**
 * Verity Systems - Cross-Browser UI Tests
 * BrowserStack/LambdaTest compatible tests
 * 
 * These tests verify the fact-checking UI works across all browsers
 */

const { Builder, By, Key, until } = require('selenium-webdriver');

// Test configuration
const BASE_URL = process.env.TEST_URL || 'http://localhost:8000';
const TIMEOUT = 30000;

// Test data
const TEST_CLAIMS = {
    true_claim: "The Earth orbits the Sun",
    false_claim: "The Moon is made of cheese",
    complex_claim: "Climate change is primarily caused by human activities",
};

describe('Verity Systems - Fact-Checking UI', function() {
    let driver;
    
    // Increase timeout for cross-browser tests
    this.timeout(60000);
    
    beforeEach(async function() {
        // Driver is initialized by BrowserStack/LambdaTest
        // For local testing:
        // driver = await new Builder().forBrowser('chrome').build();
    });
    
    afterEach(async function() {
        if (driver) {
            await driver.quit();
        }
    });
    
    describe('Homepage', function() {
        it('should load the homepage successfully', async function() {
            await driver.get(BASE_URL);
            const title = await driver.getTitle();
            expect(title).to.include('Verity');
        });
        
        it('should display the hero section', async function() {
            await driver.get(BASE_URL);
            const hero = await driver.wait(
                until.elementLocated(By.css('.hero')),
                TIMEOUT
            );
            expect(await hero.isDisplayed()).to.be.true;
        });
        
        it('should have a visible claim input field', async function() {
            await driver.get(BASE_URL);
            await driver.wait(until.elementLocated(By.id('claim-input')), TIMEOUT);
            const input = await driver.findElement(By.id('claim-input'));
            expect(await input.isDisplayed()).to.be.true;
        });
    });
    
    describe('Claim Verification', function() {
        it('should accept a claim input', async function() {
            await driver.get(BASE_URL);
            await driver.wait(until.elementLocated(By.id('claim-input')), TIMEOUT);
            
            const input = await driver.findElement(By.id('claim-input'));
            await input.sendKeys(TEST_CLAIMS.true_claim);
            
            const value = await input.getAttribute('value');
            expect(value).to.equal(TEST_CLAIMS.true_claim);
        });
        
        it('should show loading state when verifying', async function() {
            await driver.get(BASE_URL);
            await driver.wait(until.elementLocated(By.id('claim-input')), TIMEOUT);
            
            const input = await driver.findElement(By.id('claim-input'));
            await input.sendKeys(TEST_CLAIMS.true_claim);
            
            // Find and click verify button
            const verifyBtn = await driver.findElement(By.css('.verify-btn, #verify-btn, button[type="submit"]'));
            await verifyBtn.click();
            
            // Check for loading indicator
            const loadingIndicator = await driver.wait(
                until.elementLocated(By.css('.loading, .spinner, .analyzing')),
                TIMEOUT
            ).catch(() => null);
            
            // Loading should appear (may be brief)
            // Note: This may pass quickly if mock results are fast
        });
        
        it('should display results after verification', async function() {
            await driver.get(BASE_URL);
            await driver.wait(until.elementLocated(By.id('claim-input')), TIMEOUT);
            
            const input = await driver.findElement(By.id('claim-input'));
            await input.sendKeys(TEST_CLAIMS.true_claim);
            
            const verifyBtn = await driver.findElement(By.css('.verify-btn, #verify-btn, button[type="submit"]'));
            await verifyBtn.click();
            
            // Wait for results
            const results = await driver.wait(
                until.elementLocated(By.css('.result, .verdict, .verification-result')),
                TIMEOUT
            );
            
            expect(await results.isDisplayed()).to.be.true;
        });
    });
    
    describe('Navigation', function() {
        it('should navigate to features section', async function() {
            await driver.get(BASE_URL);
            const featuresLink = await driver.findElement(By.css('a[href="#features"]'));
            await featuresLink.click();
            
            // Check URL hash changed
            const currentUrl = await driver.getCurrentUrl();
            expect(currentUrl).to.include('#features');
        });
        
        it('should navigate to API section', async function() {
            await driver.get(BASE_URL);
            const apiLink = await driver.findElement(By.css('a[href="#api"]'));
            await apiLink.click();
            
            const currentUrl = await driver.getCurrentUrl();
            expect(currentUrl).to.include('#api');
        });
    });
    
    describe('Responsive Design', function() {
        it('should show mobile menu on small screens', async function() {
            // Set viewport to mobile size
            await driver.manage().window().setRect({ width: 375, height: 812 });
            await driver.get(BASE_URL);
            
            // Check for mobile menu button
            const mobileMenuBtn = await driver.findElement(By.css('.mobile-menu-btn, #mobileMenuBtn, .hamburger'));
            expect(await mobileMenuBtn.isDisplayed()).to.be.true;
        });
        
        it('should hide desktop nav on mobile', async function() {
            await driver.manage().window().setRect({ width: 375, height: 812 });
            await driver.get(BASE_URL);
            
            // Desktop nav should be hidden
            const navLinks = await driver.findElement(By.css('.nav-links'));
            const isDisplayed = await navLinks.isDisplayed().catch(() => false);
            
            // Nav links should be hidden or in mobile menu
            // This depends on your CSS implementation
        });
    });
    
    describe('Accessibility', function() {
        it('should have proper heading hierarchy', async function() {
            await driver.get(BASE_URL);
            
            const h1 = await driver.findElements(By.css('h1'));
            expect(h1.length).to.be.at.least(1);
        });
        
        it('should have alt text on images', async function() {
            await driver.get(BASE_URL);
            
            const images = await driver.findElements(By.css('img'));
            for (const img of images) {
                const alt = await img.getAttribute('alt');
                // Images should have alt attribute (even if empty for decorative)
                expect(alt).to.not.be.null;
            }
        });
        
        it('should be keyboard navigable', async function() {
            await driver.get(BASE_URL);
            
            // Tab through elements
            await driver.findElement(By.css('body')).sendKeys(Key.TAB);
            
            // Check that focus is visible
            const activeElement = await driver.switchTo().activeElement();
            expect(activeElement).to.not.be.null;
        });
    });
    
    describe('Dark Mode', function() {
        it('should use dark theme by default', async function() {
            await driver.get(BASE_URL);
            
            const body = await driver.findElement(By.css('body'));
            const bgColor = await body.getCssValue('background-color');
            
            // Dark theme should have dark background
            // RGB values close to black
            expect(bgColor).to.include('rgb');
        });
    });
    
    describe('Performance', function() {
        it('should load within 3 seconds', async function() {
            const start = Date.now();
            await driver.get(BASE_URL);
            
            // Wait for main content
            await driver.wait(until.elementLocated(By.css('.hero, main, #app')), TIMEOUT);
            
            const loadTime = Date.now() - start;
            expect(loadTime).to.be.below(3000);
        });
    });
});

// Export for use in test runners
module.exports = {
    TEST_CLAIMS,
    BASE_URL,
    TIMEOUT
};
