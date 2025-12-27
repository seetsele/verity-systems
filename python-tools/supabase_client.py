"""
Verity Systems - Supabase Python Client
Database and authentication integration for backend services.
"""

import os
import psycopg2
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client

# ================================================
# CONFIGURATION
# ================================================

# Load PostgreSQL connection string from environment variables
# Format: postgresql://username:password@host:port/database
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    os.environ.get('SUPABASE_DATABASE_URL')
)

# For REST API operations (optional)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

# Initialize Supabase client if using REST API
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ================================================
# DATABASE CONNECTION UTILITIES
# ================================================

def get_db_connection():
    """
    Get PostgreSQL database connection from DATABASE_URL.
    Returns a psycopg2 connection object.
    """
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL not configured. "
            "Set DATABASE_URL environment variable with PostgreSQL connection string."
        )
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


# ================================================
# FACT CHECK OPERATIONS
# ================================================

class FactCheckDB:
    """Database operations for fact checks."""
    
    @staticmethod
    def create_fact_check(
        claim: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new fact check record."""
        data = {
            'claim': claim,
            'user_id': user_id,
            'status': 'pending',
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('fact_checks').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_fact_check(
        fact_check_id: str,
        result: str,
        verdict: str,
        confidence: float,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update a fact check with results."""
        data = {
            'result': result,
            'verdict': verdict,
            'confidence': confidence,
            'sources': sources or [],
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('fact_checks').update(data).eq('id', fact_check_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_fact_check(fact_check_id: str) -> Optional[Dict[str, Any]]:
        """Get a fact check by ID."""
        result = supabase.table('fact_checks').select('*').eq('id', fact_check_id).single().execute()
        return result.data
    
    @staticmethod
    def get_user_fact_checks(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get fact checks for a specific user."""
        result = supabase.table('fact_checks')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        return result.data or []
    
    @staticmethod
    def get_pending_fact_checks(limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pending fact checks for processing."""
        result = supabase.table('fact_checks')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at', desc=False)\
            .limit(limit)\
            .execute()
        return result.data or []


# ================================================
# USER OPERATIONS
# ================================================

class UserDB:
    """Database operations for users."""
    
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        result = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return result.data
    
    @staticmethod
    def update_user_profile(
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile."""
        data['updated_at'] = datetime.utcnow().isoformat()
        result = supabase.table('profiles').update(data).eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def increment_usage(user_id: str, count: int = 1) -> None:
        """Increment user's fact check usage count."""
        supabase.rpc('increment_usage', {'user_id': user_id, 'count': count}).execute()


# ================================================
# CONTACT & NEWSLETTER
# ================================================

class ContactDB:
    """Database operations for contact and newsletter."""
    
    @staticmethod
    def save_contact_submission(
        name: str,
        email: str,
        company: Optional[str] = None,
        message: str = ''
    ) -> Dict[str, Any]:
        """Save a contact form submission."""
        data = {
            'name': name,
            'email': email,
            'company': company,
            'message': message,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('contact_submissions').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def subscribe_newsletter(email: str) -> Dict[str, Any]:
        """Subscribe email to newsletter."""
        data = {
            'email': email,
            'subscribed_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        result = supabase.table('newsletter_subscribers').upsert(
            data, 
            on_conflict='email'
        ).execute()
        return result.data[0] if result.data else None


# ================================================
# API USAGE & ANALYTICS
# ================================================

class AnalyticsDB:
    """Database operations for analytics and usage tracking."""
    
    @staticmethod
    def log_api_call(
        endpoint: str,
        user_id: Optional[str] = None,
        response_time_ms: int = 0,
        status_code: int = 200
    ) -> None:
        """Log an API call for analytics."""
        data = {
            'endpoint': endpoint,
            'user_id': user_id,
            'response_time_ms': response_time_ms,
            'status_code': status_code,
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.table('api_logs').insert(data).execute()
    
    @staticmethod
    def get_usage_stats(user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        result = supabase.rpc('get_user_stats', {'p_user_id': user_id}).execute()
        return result.data[0] if result.data else {}


# ================================================
# STORAGE OPERATIONS
# ================================================

class StorageClient:
    """Storage operations for documents."""
    
    BUCKET_NAME = 'documents'
    
    @classmethod
    def upload_document(cls, file_path: str, file_data: bytes, user_id: str) -> str:
        """Upload a document and return its path."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        storage_path = f"{user_id}/{timestamp}_{file_path}"
        
        supabase.storage.from_(cls.BUCKET_NAME).upload(storage_path, file_data)
        return storage_path
    
    @classmethod
    def get_document_url(cls, path: str) -> str:
        """Get public URL for a document."""
        return supabase.storage.from_(cls.BUCKET_NAME).get_public_url(path)
    
    @classmethod
    def delete_document(cls, path: str) -> None:
        """Delete a document from storage."""
        supabase.storage.from_(cls.BUCKET_NAME).remove([path])


# ================================================
# INITIALIZATION CHECK
# ================================================

def verify_connection() -> bool:
    """Verify Supabase connection is working."""
    try:
        # Simple query to test connection
        supabase.table('fact_checks').select('id').limit(1).execute()
        return True
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return False


if __name__ == '__main__':
    # Test connection
    if verify_connection():
        print("✓ Supabase connection successful")
    else:
        print("✗ Supabase connection failed - check your credentials")
