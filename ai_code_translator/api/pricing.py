"""
Pricing and subscription management for AI Code Translator
"""

from enum import Enum
from datetime import datetime
import sqlite3

class SubscriptionTier(Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class PricingPlan:
    TIERS = {
        SubscriptionTier.BASIC: {
            "price": 29.99,
            "monthly_limit": 1000,
            "features": [
                "Basic language support",
                "Standard response time",
                "Community support"
            ]
        },
        SubscriptionTier.PRO: {
            "price": 99.99,
            "monthly_limit": 5000,
            "features": [
                "Advanced language support",
                "Faster response time",
                "Priority email support",
                "Batch processing"
            ]
        },
        SubscriptionTier.ENTERPRISE: {
            "price": "Custom",
            "monthly_limit": None,  # Unlimited
            "features": [
                "Custom language support",
                "Dedicated support",
                "Custom model training",
                "SLA guarantee",
                "On-premise deployment option"
            ]
        }
    }
    
    @staticmethod
    def get_tier_info(tier: SubscriptionTier) -> dict:
        """Get pricing and feature information for a tier."""
        return PricingPlan.TIERS[tier]
    
    @staticmethod
    def create_subscription(email: str, tier: SubscriptionTier) -> str:
        """Create a new subscription and return API key."""
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        
        # Generate API key
        import secrets
        api_key = secrets.token_urlsafe(32)
        
        # Get tier limits
        tier_info = PricingPlan.get_tier_info(tier)
        
        # Create subscription
        cursor.execute("""
            INSERT INTO api_keys (
                key, 
                email, 
                tier, 
                monthly_limit, 
                used_requests, 
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            api_key,
            email,
            tier.value,
            tier_info["monthly_limit"] or 999999999,  # Use large number for unlimited
            0,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return api_key

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    # Create api_keys table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            tier TEXT NOT NULL,
            monthly_limit INTEGER NOT NULL,
            used_requests INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_reset_at TEXT
        )
    """)
    
    # Create usage_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            characters_processed INTEGER NOT NULL,
            FOREIGN KEY (api_key) REFERENCES api_keys (key)
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Initialize database
    init_db()
