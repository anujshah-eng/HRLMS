from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic" 
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"