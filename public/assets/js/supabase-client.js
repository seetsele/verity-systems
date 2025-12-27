// ================================================
// VERITY SYSTEMS - SUPABASE CLIENT
// ================================================

// Supabase Configuration
// Replace these with your actual Supabase project credentials
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Initialize Supabase client
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ================================================
// AUTHENTICATION HELPERS
// ================================================

const VerityAuth = {
    // Sign up with email and password
    async signUp(email, password, metadata = {}) {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata
            }
        });
        return { data, error };
    },

    // Sign in with email and password
    async signIn(email, password) {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });
        return { data, error };
    },

    // Sign out
    async signOut() {
        const { error } = await supabase.auth.signOut();
        return { error };
    },

    // Get current user
    async getCurrentUser() {
        const { data: { user }, error } = await supabase.auth.getUser();
        return { user, error };
    },

    // Get current session
    async getSession() {
        const { data: { session }, error } = await supabase.auth.getSession();
        return { session, error };
    },

    // Listen to auth state changes
    onAuthStateChange(callback) {
        return supabase.auth.onAuthStateChange((event, session) => {
            callback(event, session);
        });
    },

    // Password reset
    async resetPassword(email) {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`
        });
        return { data, error };
    }
};

// ================================================
// DATABASE HELPERS
// ================================================

const VerityDB = {
    // Fact check submissions
    async submitFactCheck(claim, userId = null) {
        const { data, error } = await supabase
            .from('fact_checks')
            .insert({
                claim,
                user_id: userId,
                status: 'pending',
                created_at: new Date().toISOString()
            })
            .select();
        return { data, error };
    },

    // Get user's fact check history
    async getFactCheckHistory(userId) {
        const { data, error } = await supabase
            .from('fact_checks')
            .select('*')
            .eq('user_id', userId)
            .order('created_at', { ascending: false });
        return { data, error };
    },

    // Get single fact check by ID
    async getFactCheck(id) {
        const { data, error } = await supabase
            .from('fact_checks')
            .select('*')
            .eq('id', id)
            .single();
        return { data, error };
    },

    // Contact form submissions
    async submitContactForm(formData) {
        const { data, error } = await supabase
            .from('contact_submissions')
            .insert({
                name: formData.name,
                email: formData.email,
                company: formData.company,
                message: formData.message,
                created_at: new Date().toISOString()
            })
            .select();
        return { data, error };
    },

    // Newsletter signup
    async subscribeNewsletter(email) {
        const { data, error } = await supabase
            .from('newsletter_subscribers')
            .upsert({
                email,
                subscribed_at: new Date().toISOString()
            }, { onConflict: 'email' })
            .select();
        return { data, error };
    }
};

// ================================================
// REAL-TIME SUBSCRIPTIONS
// ================================================

const VerityRealtime = {
    // Subscribe to fact check updates
    subscribeToFactCheck(factCheckId, callback) {
        return supabase
            .channel(`fact_check:${factCheckId}`)
            .on('postgres_changes', {
                event: 'UPDATE',
                schema: 'public',
                table: 'fact_checks',
                filter: `id=eq.${factCheckId}`
            }, callback)
            .subscribe();
    },

    // Unsubscribe from channel
    unsubscribe(channel) {
        supabase.removeChannel(channel);
    }
};

// ================================================
// STORAGE HELPERS
// ================================================

const VerityStorage = {
    // Upload document for fact-checking
    async uploadDocument(file, userId) {
        const fileName = `${userId}/${Date.now()}_${file.name}`;
        const { data, error } = await supabase.storage
            .from('documents')
            .upload(fileName, file);
        return { data, error };
    },

    // Get document URL
    getDocumentUrl(path) {
        const { data } = supabase.storage
            .from('documents')
            .getPublicUrl(path);
        return data.publicUrl;
    },

    // Delete document
    async deleteDocument(path) {
        const { error } = await supabase.storage
            .from('documents')
            .remove([path]);
        return { error };
    }
};

// Export for use in other modules
window.VeritySupabase = {
    client: supabase,
    auth: VerityAuth,
    db: VerityDB,
    realtime: VerityRealtime,
    storage: VerityStorage
};

console.log('Verity Supabase client initialized');
