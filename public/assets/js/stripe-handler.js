/**
 * Verity Systems - Stripe Integration
 * Frontend payment processing and subscription management
 */

class VerityStripeHandler {
    constructor(publishableKey, apiEndpoint = '/v1') {
        this.publishableKey = publishableKey;
        this.apiEndpoint = apiEndpoint;
        this.stripe = Stripe(publishableKey);
    }

    /**
     * Initialize Stripe elements for payment
     */
    async initializePaymentElement(elementId) {
        try {
            const elements = this.stripe.elements();
            const paymentElement = elements.create('payment');
            paymentElement.mount(`#${elementId}`);
            return { elements, paymentElement };
        } catch (error) {
            console.error('Failed to initialize payment element:', error);
            throw error;
        }
    }

    /**
     * Create a checkout session for subscription
     */
    async createCheckoutSession(planId, userEmail) {
        try {
            const response = await fetch(`${this.apiEndpoint}/checkout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    price_id: planId,
                    customer_email: userEmail
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Redirect to Checkout
            if (data.session_id) {
                return await this.stripe.redirectToCheckout({
                    sessionId: data.session_id
                });
            }
            
            return data;
        } catch (error) {
            console.error('Failed to create checkout session:', error);
            throw error;
        }
    }

    /**
     * Handle subscription creation
     */
    async handleSubscriptionCreation(sessionId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/subscription/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to confirm subscription:', error);
            throw error;
        }
    }

    /**
     * Cancel subscription
     */
    async cancelSubscription(subscriptionId, atPeriodEnd = true) {
        try {
            const response = await fetch(`${this.apiEndpoint}/subscription/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    subscription_id: subscriptionId,
                    at_period_end: atPeriodEnd
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to cancel subscription:', error);
            throw error;
        }
    }

    /**
     * Update subscription plan
     */
    async updateSubscription(subscriptionId, newPriceId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/subscription/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    subscription_id: subscriptionId,
                    price_id: newPriceId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to update subscription:', error);
            throw error;
        }
    }

    /**
     * Get subscription details
     */
    async getSubscription(subscriptionId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/subscription/${subscriptionId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get subscription:', error);
            throw error;
        }
    }

    /**
     * Get invoices
     */
    async getInvoices() {
        try {
            const response = await fetch(`${this.apiEndpoint}/invoices`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get invoices:', error);
            throw error;
        }
    }

    /**
     * Get payment methods
     */
    async getPaymentMethods() {
        try {
            const response = await fetch(`${this.apiEndpoint}/payment-methods`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get payment methods:', error);
            throw error;
        }
    }

    /**
     * Update default payment method
     */
    async updatePaymentMethod(paymentMethodId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/payment-method/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    payment_method_id: paymentMethodId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to update payment method:', error);
            throw error;
        }
    }

    /**
     * Get auth token from local storage or cookie
     */
    getAuthToken() {
        // Try localStorage first
        const token = localStorage.getItem('authToken');
        if (token) return token;
        
        // Fallback to cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'authToken') return value;
        }
        
        return null;
    }

    /**
     * Set auth token
     */
    setAuthToken(token) {
        localStorage.setItem('authToken', token);
        document.cookie = `authToken=${token}; path=/; secure; sameSite=Strict`;
    }

    /**
     * Clear auth token
     */
    clearAuthToken() {
        localStorage.removeItem('authToken');
        document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }
}

// Initialize Stripe handler if publishable key is available
let stripeHandler = null;
if (window.STRIPE_PUBLISHABLE_KEY) {
    stripeHandler = new VerityStripeHandler(window.STRIPE_PUBLISHABLE_KEY);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VerityStripeHandler, stripeHandler };
}
