from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
from passlib.context import CryptContext
from jose import JWTError, jwt
import json
import asyncio

# Emergent Integrations for AI
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'hackster-ai-secret-key-for-jwt-tokens-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Emergent LLM Key for AI
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'hackster_db')]
    print(f"✅ MongoDB configured with URL: {mongo_url[:20]}...")  # Log first 20 chars for debugging
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Create a dummy client for now
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(title="Hackster Health Platform API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

class UserLevel(str, Enum):
    MEMBER = "member"
    CONTRIBUTOR = "contributor" 
    HACKSTER_PRO = "hackster_pro"
    ADMIN = "admin"

class PostCategory(str, Enum):
    GENERAL = "general"
    NUTRITION = "nutrition"
    SUPPLEMENTS = "supplements"
    RECOVERY = "recovery"
    SLEEP = "sleep"
    TECHNOLOGY = "technology"
    EXERCISE = "exercise"
    MINDFULNESS = "mindfulness"

class ReactionType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    TRIED_THIS = "tried_this"
    HELPFUL = "helpful"
    RESULTS = "results"
    ON_POINT = "on_point"

class UserRole(str, Enum):
    MEMBER = "member"
    COACH = "coach"
    ADMIN = "admin"

class SupplementCategory(str, Enum):
    VITAMIN = "vitamin"
    MINERAL = "mineral"
    AMINO_ACID = "amino_acid"
    MULTIVITAMIN = "multivitamin"
    DEVICE = "device"
    BIOHACK = "biohack"

class DemographicTarget(str, Enum):
    MEN = "men"
    WOMEN = "women"
    ATHLETES = "athletes"
    SENIORS = "seniors"
    YOUNG_ADULTS = "young_adults"

class HealthTestProvider(str, Enum):
    FUNCTION_HEALTH = "function_health"
    THORNE = "thorne"

# ============== NEW MARKETPLACE ENUMS ==============
class VendorStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"

class ProductCategory(str, Enum):
    SUPPLEMENTS = "supplements"
    VITAMINS = "vitamins"
    MINERALS = "minerals"
    ADAPTOGENS = "adaptogens"
    AMINO_ACIDS = "amino_acids"
    PROBIOTICS = "probiotics"
    NOOTROPICS = "nootropics"
    SLEEP_AIDS = "sleep_aids"
    ENERGY = "energy"
    RECOVERY = "recovery"
    DEVICES = "devices"
    LAB_TESTS = "lab_tests"
    APPAREL = "apparel"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class WishlistVisibility(str, Enum):
    PRIVATE = "private"
    FRIENDS = "friends"
    COMMUNITY = "community"
    PUBLIC = "public"

class HealthGoal(str, Enum):
    ENERGY = "energy"
    SLEEP = "sleep"
    FOCUS = "focus"
    LONGEVITY = "longevity"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    WEIGHT_MANAGEMENT = "weight_management"
    STRESS_MANAGEMENT = "stress_management"
    IMMUNE_SUPPORT = "immune_support"
    GUT_HEALTH = "gut_health"
    HORMONE_BALANCE = "hormone_balance"
    SKIN_HEALTH = "skin_health"
    HEART_HEALTH = "heart_health"

# Data Models
class HealthTest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: HealthTestProvider
    description: str
    price_range: str
    test_type: str
    recommended_for: List[str]
    url: Optional[str] = None

class Supplement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    brand: str
    category: SupplementCategory
    priority: int
    description: str
    benefits: List[str]
    dosage: str
    price_range: str
    demographic_targets: List[DemographicTarget]
    product_url: Optional[str] = None

class BiohackingTip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    category: str
    description: str
    instructions: List[str]
    difficulty_level: str
    time_required: str
    cost: str = "Free"

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    role: UserRole = UserRole.MEMBER
    level: UserLevel = UserLevel.MEMBER
    reputation_score: int = 0
    posts_count: int = 0
    comments_count: int = 0
    reactions_received: int = 0
    age: Optional[int] = None
    gender: Optional[str] = None
    goals: List[str] = []
    current_supplements: List[str] = []
    health_conditions: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    title: str
    content: str
    category: PostCategory
    image_url: Optional[str] = None
    youtube_url: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    reaction_counts: Dict[str, int] = Field(default_factory=dict)
    comments_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    user_id: str
    username: str
    content: str
    upvotes: int = 0
    downvotes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Reaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    reaction_type: ReactionType
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(UserProfile):
    hashed_password: str

class PostCreate(BaseModel):
    title: str
    content: str
    category: PostCategory
    image_url: Optional[str] = None
    youtube_url: Optional[str] = None

class CommentCreate(BaseModel):
    post_id: str
    content: str

class ReactionCreate(BaseModel):
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    reaction_type: ReactionType

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.MEMBER
    age: Optional[int] = None
    gender: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class HealthAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    responses: Dict[str, Any]
    recommended_tests: List[str]
    recommended_supplements: List[str]
    score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============== MARKETPLACE MODELS ==============
class FulfillmentType(str, Enum):
    AFFILIATE = "affiliate"              # Public tracked affiliate link -> vendor checkout
    PRACTITIONER_ORDER = "practitioner_order"  # Ordered via Hackster practitioner account (e.g. Standard Process, Apex)

class Vendor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: str
    logo_url: Optional[str] = None
    website: str
    affiliate_url_pattern: Optional[str] = None  # e.g., "https://thorne.com/products/dp/{product_id}?aff=hackster"
    commission_rate: float = 0.10  # 10% default
    status: VendorStatus = VendorStatus.ACTIVE
    contact_email: Optional[str] = None
    shipping_info: str = "Ships within 2-5 business days"
    return_policy: str = "30-day return policy"
    categories: List[ProductCategory] = []
    # ----- Affiliate / fulfillment configuration (network-agnostic) -----
    fulfillment_type: FulfillmentType = FulfillmentType.AFFILIATE
    network: Optional[str] = None            # e.g. "impact", "shareasale", "refersion", "cj", "direct" (informational)
    tracking_param: str = "aff"              # query param used to attribute the sale (editable per vendor)
    tracking_value: str = "hackster"         # your affiliate/partner id value for this vendor
    subid_param: Optional[str] = "subId"     # optional param to pass per-click/per-user subID for reporting
    add_to_cart_pattern: Optional[str] = None  # optional multi-item deep link, e.g. "https://vendor.com/cart/add?items={items}"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketplaceProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    vendor_name: str
    sku: Optional[str] = None
    name: str
    slug: str
    description: str
    short_description: Optional[str] = None
    category: ProductCategory
    subcategory: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    currency: str = "USD"
    image_url: Optional[str] = None
    images: List[str] = []
    affiliate_url: Optional[str] = None
    benefits: List[str] = []
    ingredients: Optional[str] = None
    dosage_instructions: Optional[str] = None
    warnings: Optional[str] = None
    health_goals: List[HealthGoal] = []
    demographic_targets: List[DemographicTarget] = []
    rating: float = 0.0
    review_count: int = 0
    stock_status: str = "in_stock"
    is_featured: bool = False
    is_ai_recommended: bool = False
    priority_score: int = 0  # For AI recommendations ranking
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    vendor_id: str
    vendor_name: str
    quantity: int = 1
    price: float
    image_url: Optional[str] = None

class ShoppingCart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    subtotal: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    vendor_id: str
    vendor_name: str
    quantity: int
    price: float
    subtotal: float

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float = 0.0
    tax: float = 0.0
    total: float
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: Dict[str, str] = {}
    billing_address: Dict[str, str] = {}
    tracking_numbers: Dict[str, str] = {}  # vendor_id -> tracking_number
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============== AFFILIATE TRACKING MODELS ==============
class AffiliateClick(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    product_id: str
    product_name: str
    vendor_id: str
    vendor_name: str
    source: str = "marketplace"     # marketplace | stack | chat | questionnaire | recommendation
    tracked_url: str
    price: float = 0.0
    commission_rate: float = 0.0
    est_commission: float = 0.0
    converted: bool = False
    conversion_value: float = 0.0
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = 1

class StackCheckoutRequest(BaseModel):
    items: List[CheckoutItem]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source: str = "stack"

class PractitionerOrderItem(BaseModel):
    product_id: str
    product_name: str
    vendor_id: str
    vendor_name: str
    quantity: int = 1
    price: float = 0.0

class PractitionerOrderStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

class PractitionerOrderRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    items: List[PractitionerOrderItem] = []
    vendors: List[str] = []
    estimated_total: float = 0.0
    notes: Optional[str] = None
    status: PractitionerOrderStatus = PractitionerOrderStatus.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PractitionerOrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    items: List[CheckoutItem]
    user_id: Optional[str] = None

class ConversionReport(BaseModel):
    click_id: Optional[str] = None
    product_id: Optional[str] = None
    order_value: float = 0.0

# ============== WISHLIST / STACK MODELS ==============
class WishlistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    vendor_name: str
    price: float
    image_url: Optional[str] = None
    priority: int = 0  # 1=high, 2=medium, 3=low
    notes: Optional[str] = None
    is_purchased: bool = False
    purchased_by: Optional[str] = None  # For gift registry functionality
    added_at: datetime = Field(default_factory=datetime.utcnow)

class HacksterStack(BaseModel):
    """User's personalized biohacking product wishlist/stack"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    name: str = "My Hackster Stack"
    description: Optional[str] = None
    visibility: WishlistVisibility = WishlistVisibility.PRIVATE
    health_goals: List[HealthGoal] = []
    items: List[WishlistItem] = []
    total_value: float = 0.0
    is_ai_generated: bool = False
    share_token: Optional[str] = None  # Unique token for sharing
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class StackComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stack_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StackLike(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stack_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============== AI QUESTIONNAIRE MODELS ==============
class QuestionnaireQuestion(BaseModel):
    id: str
    question: str
    question_type: str  # "single_choice", "multiple_choice", "scale", "text"
    options: Optional[List[str]] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    category: str  # "demographics", "lifestyle", "health_goals", "current_health", "diet"

class QuestionnaireResponse(BaseModel):
    question_id: str
    answer: Any

class AIQuestionnaireSubmission(BaseModel):
    responses: List[QuestionnaireResponse]

class AIRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    questionnaire_session_id: str
    health_score: int  # 0-100
    primary_goals: List[HealthGoal]
    recommended_products: List[Dict[str, Any]]  # List of product recommendations with reasons
    recommended_lab_tests: List[Dict[str, Any]]
    recommended_coaches: List[Dict[str, Any]] = []  # Top matched health coaches
    lifestyle_tips: List[str]
    personalized_summary: str
    ai_reasoning: str  # Detailed AI analysis
    coach_match_specialties: List[str] = []  # Goal/specialty keywords used to match coaches
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LabResultUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: str  # "function_health", "superpower", "quest", "labcorp", "other"
    test_date: datetime
    biomarkers: Dict[str, Any]  # {"vitamin_d": {"value": 45, "unit": "ng/mL", "reference_range": "30-100"}}
    file_url: Optional[str] = None
    notes: Optional[str] = None
    ai_analysis: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Coach(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Link to user account
    name: str
    credentials: List[str]
    specialties: List[str]
    location: str
    bio: str
    hourly_rate: str
    availability: str
    contact_info: Dict[str, str]
    rating: float = 0.0
    total_reviews: int = 0
    profile_image: Optional[str] = None
    website: Optional[str] = None
    years_experience: Optional[int] = None
    is_approved: bool = False  # For admin approval
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CoachProfileCreate(BaseModel):
    name: str
    bio: str
    specialties: List[str]
    location: str
    hourly_rate: str
    availability: str
    credentials: List[str] = []
    contact_info: Dict[str, str] = {}
    profile_image: Optional[str] = None
    website: Optional[str] = None
    years_experience: Optional[int] = None

class CoachProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    location: Optional[str] = None
    hourly_rate: Optional[str] = None
    availability: Optional[str] = None
    credentials: Optional[List[str]] = None
    contact_info: Optional[Dict[str, str]] = None
    profile_image: Optional[str] = None
    website: Optional[str] = None
    years_experience: Optional[int] = None

# Create request models
class UserProfileCreate(BaseModel):
    email: EmailStr
    age: Optional[int] = None
    gender: Optional[str] = None
    goals: List[str] = []

class HealthAssessmentCreate(BaseModel):
    user_id: str
    responses: Dict[str, Any]

# ============== MARKETPLACE REQUEST MODELS ==============
class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1

class UpdateCartItemRequest(BaseModel):
    quantity: int

class CreateStackRequest(BaseModel):
    name: str = "My Hackster Stack"
    description: Optional[str] = None
    visibility: WishlistVisibility = WishlistVisibility.PRIVATE
    health_goals: List[HealthGoal] = []

class AddToStackRequest(BaseModel):
    product_id: str
    priority: int = 0
    notes: Optional[str] = None

class StackCommentCreate(BaseModel):
    content: str

class LabResultUploadRequest(BaseModel):
    provider: str
    test_date: str  # ISO format
    biomarkers: Dict[str, Any]
    notes: Optional[str] = None

# Authentication utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return UserProfile(**user.dict())

async def require_admin(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Dependency that ensures the current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def build_tracked_url(product: dict, vendor: dict, subid: Optional[str] = None) -> str:
    """Build a network-agnostic tracked affiliate URL for a product.
    Uses the product's explicit affiliate_url if present, else the vendor's
    affiliate_url_pattern, else the vendor website. Injects the vendor's
    tracking param/value and an optional subID for per-click attribution.
    """
    from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

    base = product.get("affiliate_url")
    if not base:
        pattern = vendor.get("affiliate_url_pattern")
        slug = product.get("slug") or product.get("id")
        if pattern:
            base = pattern.replace("{product_slug}", str(slug)).replace("{product_id}", str(product.get("id")))
        else:
            base = vendor.get("website") or "https://hackster.ai"

    try:
        parsed = urlparse(base)
        query = dict(parse_qsl(parsed.query))
        # Ensure the vendor tracking param/value is present (network-agnostic)
        tracking_param = vendor.get("tracking_param") or "aff"
        tracking_value = vendor.get("tracking_value") or "hackster"
        query[tracking_param] = tracking_value
        # Attach optional subID for per-click / per-user reporting
        subid_param = vendor.get("subid_param") or "subId"
        if subid_param and subid:
            query[subid_param] = subid
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return base


# ============== AI RECOMMENDATION ENGINE ==============
async def generate_ai_recommendations(user_responses: List[QuestionnaireResponse], user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
    """Generate personalized product recommendations using GPT"""
    
    if not EMERGENT_LLM_KEY:
        # Return mock recommendations if no API key
        return {
            "health_score": 75,
            "primary_goals": ["energy", "longevity"],
            "recommended_products": [
                {"product_id": "vitamin_d3_k2", "name": "Vitamin D-5,000", "brand": "Thorne", "reason": "Essential for immune and bone health", "priority": 1},
                {"product_id": "magnesium", "name": "Magnesium Bisglycinate", "brand": "Thorne", "reason": "Supports sleep and recovery", "priority": 2},
                {"product_id": "stemregen-mobilize", "name": "STEMREGEN® Mobilize", "brand": "StemRegen", "reason": "Supports endothelial health and stem cell delivery for longevity", "priority": 3}
            ],
            "recommended_lab_tests": [
                {"test_id": "biowell-scan", "name": "Bio-Well GDV Energy Scan", "provider": "bio-well", "reason": "Establish baseline bioenergy, stress and adaptation levels"}
            ],
            "lifestyle_tips": [
                "Get 10-30 minutes of morning sunlight",
                "Practice box breathing for stress management",
                "End showers with 30-60 seconds of cold water"
            ],
            "personalized_summary": "Based on your responses, we recommend focusing on foundational health with Vitamin D3+K2 and Magnesium, plus a Bio-Well baseline scan.",
            "ai_reasoning": "Mock response - API key not configured",
            "coach_match_specialties": ["longevity", "energy", "weight management"]
        }
    
    # Format responses for AI
    responses_text = "\n".join([f"Q: {r.question_id} - A: {r.answer}" for r in user_responses])
    
    user_context = ""
    if user_profile:
        user_context = f"\nUser Info: Age: {user_profile.age or 'Unknown'}, Gender: {user_profile.gender or 'Unknown'}, Goals: {', '.join(user_profile.goals)}"
    
    system_prompt = """You are an expert biohacking and health optimization AI assistant for Hackster.ai.
    Your role is to analyze user health questionnaire responses and provide personalized supplement, device,
    and lifestyle recommendations focused on FOUR PRIORITY GOALS:
      1. INCREASE ENERGY
      2. IMPROVE VITALITY / LONGEVITY
      3. BOOST IMMUNE SYSTEM
      4. WEIGHT LOSS / METABOLIC HEALTH

    You have deep knowledge of these partner brands and their product lines:

    🟣 THORNE (premium science-backed supplements):
      - Vitamin D-5,000, Magnesium Bisglycinate, Super EPA (omega-3), Ashwagandha (Sensoril),
        Basic Nutrients 2/Day (multivitamin), Berberine, NiaCel 400 (NAD+/NR), CoQ10,
        B-Complex #12, Curcumin Phytosome, Whey Isolate, Mediclear-SGS (detox/weight)

    🟢 APEX ENERGETICS (practitioner-grade clinical supplements):
      - Adaptocrine (adrenal/stress support), Glutathione Recycler, Methyl-SP (methylation),
        Resvero Active (resveratrol), Oxicell (topical glutathione), Strengtia (probiotic),
        Turmero Active (curcumin), Glysen Synergy (blood sugar/weight)

    🟠 STANDARD PROCESS (whole-food based supplements):
      - Catalyn (foundational multivitamin), Cataplex A (vitamin A complex), Immuplex (immune),
        Cataplex E, Cyruta Plus (vascular), Tuna Omega-3 Oil, Thymex (thymus), Cardio-Plus

    🟡 BIO-WELL (bioenergy/biofield assessment, GDV technology):
      - Bio-Well GDV Camera (at-home energy scanner) — establishes baseline vitality, stress
        and adaptation. Recommend for ESTABLISHING BASELINE, especially for vitality/longevity goals.
      - Bio-Well Pro Coaching Scan — done with a certified practitioner.

    🔵 CURAWAVES (frequency-based device — Rife/square-wave electrotherapy; NOT a PEMF device):
      - CuraWaves Wave Therapy Device — 400+ pre-programmed frequency sessions targeting
        weight management, energy, sleep, pain/inflammation, circulation, detoxification.
      - CuraWaves Premium Bundle — includes coaching + FREEDOM Wellness Program.
      Recommend for users with weight-loss goals, low energy, or wanting frequency-based
      non-invasive support.

    🟤 STEMREGEN (plant-based stem cell mobilizers):
      - STEMREGEN® Mobilize — supports blood flow, endothelial glycocalyx, stem cell circulation.
      - STEMREGEN® Release — supports stem cell release from bone marrow.
      - STEMREGEN® RegenerEnd (senolytic) — supports clearing senescent cells for longevity.
      Recommend especially for VITALITY/LONGEVITY and recovery goals.

    Other tools: Function Health labs, Oura Ring for sleep/recovery tracking.

    IMPORTANT recommendation rules:
    - Match products to the user's PRIMARY goal first, then secondary goals.
    - Always include 4-7 recommended products with a mix of foundational supplements AND at least
      one device/assessment (Bio-Well or CuraWaves) when relevant.
    - For LONGEVITY/VITALITY goals: include StemRegen Mobilize and/or NiaCel.
    - For WEIGHT LOSS goals: include Berberine, Mediclear-SGS, Glysen Synergy, or CuraWaves.
    - For IMMUNE goals: include Vitamin D-5,000, Immuplex, Thymex, Curcumin Phytosome.
    - For ENERGY: include CoQ10, B-Complex, Adaptocrine, Magnesium.

    Always respond with valid JSON in this exact format:
    {
        "health_score": <number 0-100>,
        "primary_goals": ["energy" | "longevity" | "immune_support" | "weight_management" | ...],
        "recommended_products": [
            {"product_id": "id", "name": "Product Name", "brand": "Brand", "reason": "Why recommended", "priority": 1}
        ],
        "recommended_lab_tests": [
            {"test_id": "id", "name": "Test Name", "provider": "provider", "reason": "Why needed"}
        ],
        "lifestyle_tips": ["tip1", "tip2", "tip3"],
        "personalized_summary": "2-3 sentence summary of recommendations",
        "ai_reasoning": "Detailed analysis of user's responses and why these recommendations were made",
        "coach_match_specialties": ["longevity", "weight management", "energy", "immune"]
    }

    The "coach_match_specialties" field should list 2-4 keywords matching the user's main goals so we can
    pair them with the right health coach (e.g. "longevity", "weight management", "energy", "immune",
    "bioenergy", "frequency therapy", "stem cell", "stress").

    Base your recommendations on evidence-based health science and biohacking best practices."""
    
    user_prompt = f"""Please analyze the following health questionnaire responses and provide personalized recommendations:
    
    {responses_text}
    {user_context}
    
    Consider the user's PRIMARY health goal first (Energy, Vitality/Longevity, Immune, or Weight Loss),
    then secondary goals, current lifestyle, and concerns. Provide 4-7 product recommendations spanning
    Thorne, Apex Energetics, Standard Process, Bio-Well, CuraWaves, and/or StemRegen — choose what truly
    matches their goals. Suggest practical lifestyle tips and list the coach specialties that best
    match this person."""
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hackster-questionnaire-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.1")
        
        message = UserMessage(text=user_prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        # Try to extract JSON from the response
        response_text = str(response)
        
        # Find JSON in response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            return result
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        logging.error(f"AI recommendation error: {e}")
        # Return default recommendations on error
        return {
            "health_score": 70,
            "primary_goals": ["energy", "longevity"],
            "recommended_products": [
                {"product_id": "vitamin-d-5000", "name": "Vitamin D-5,000", "brand": "Thorne", "reason": "Essential for most people, supports immune function and bone health", "priority": 1},
                {"product_id": "magnesium-bisglycinate", "name": "Magnesium Bisglycinate", "brand": "Thorne", "reason": "Supports sleep, recovery, and over 300 enzymatic processes", "priority": 2},
                {"product_id": "super-epa", "name": "Super EPA", "brand": "Thorne", "reason": "Supports brain health and reduces inflammation", "priority": 3},
                {"product_id": "stemregen-mobilize", "name": "STEMREGEN® Mobilize", "brand": "StemRegen", "reason": "Supports stem cell circulation for vitality and longevity", "priority": 4},
                {"product_id": "biowell-gdv-camera", "name": "Bio-Well GDV Camera", "brand": "Bio-Well", "reason": "Establish a bioenergy baseline to track your progress", "priority": 5}
            ],
            "recommended_lab_tests": [
                {"test_id": "comprehensive_panel", "name": "Comprehensive Metabolic Panel", "provider": "function_health", "reason": "Establish baseline health metrics"}
            ],
            "lifestyle_tips": [
                "Get 10-30 minutes of morning sunlight within 1 hour of waking",
                "Practice 5 minutes of box breathing daily for stress management",
                "End showers with 30-60 seconds of cold water to boost energy"
            ],
            "personalized_summary": "We recommend starting with foundational supplements (Vitamin D3+K2 and Magnesium), a bioenergy baseline scan, and StemRegen Mobilize for vitality.",
            "ai_reasoning": f"Error generating AI response: {str(e)}. Providing default evidence-based recommendations.",
            "coach_match_specialties": ["longevity", "energy", "weight management"]
        }

# Initialize sample data
async def initialize_sample_data():
    """Initialize the database with sample health tests, supplements, and biohacks"""
    
    # Sample Health Tests
    health_tests = [
        {
            "name": "Comprehensive Metabolic Panel",
            "provider": "function_health",
            "description": "Complete blood work covering 110+ biomarkers including vitamins, minerals, hormones, and metabolic markers",
            "price_range": "$499-699",
            "test_type": "Blood Test",
            "recommended_for": ["Everyone seeking baseline health metrics", "Biohacking beginners", "Annual health optimization"],
            "url": "https://functionhealth.com"
        },
        {
            "name": "Personalized Nutrition Test",
            "provider": "thorne",
            "description": "Genetic testing combined with biomarker analysis for personalized supplement recommendations",
            "price_range": "$149-299",
            "test_type": "Genetic + Blood",
            "recommended_for": ["Supplement optimization", "Genetic-based nutrition", "Personalized health plans"],
            "url": "https://thorne.com"
        }
    ]
    
    # Sample Supplements
    supplements = [
        {
            "name": "Vitamin D3 + K2",
            "brand": "Thorne",
            "category": "vitamin",
            "priority": 1,
            "description": "Essential for immune function, bone health, and cardiovascular support",
            "benefits": ["Immune system support", "Bone health", "Mood regulation", "Cardiovascular health"],
            "dosage": "2000-5000 IU daily",
            "price_range": "$25-35",
            "demographic_targets": ["men", "women", "athletes", "seniors"],
            "product_url": "https://thorne.com/products/dp/vitamin-d-k2"
        },
        {
            "name": "Vitamin A",
            "brand": "Standard Process",
            "category": "vitamin",
            "priority": 2,
            "description": "Critical for vision, immune function, and cellular health",
            "benefits": ["Vision support", "Immune function", "Skin health", "Antioxidant protection"],
            "dosage": "5000-10000 IU daily",
            "price_range": "$20-30",
            "demographic_targets": ["men", "women", "young_adults"],
            "product_url": "https://standardprocess.com"
        },
        {
            "name": "Magnesium Bisglycinate",
            "brand": "Thorne",
            "category": "mineral",
            "priority": 4,
            "description": "Highly absorbable magnesium for 300+ enzymatic reactions, sleep, and recovery",
            "benefits": ["Better sleep", "Muscle recovery", "Stress reduction", "Energy production"],
            "dosage": "200-400mg before bed",
            "price_range": "$30-40",
            "demographic_targets": ["athletes", "men", "women"],
            "product_url": "https://thorne.com/products/dp/magnesium-bisglycinate"
        },
        {
            "name": "Essential Amino Acids",
            "brand": "Apex Energetics",
            "category": "amino_acid",
            "priority": 5,
            "description": "Complete amino acid profile for muscle building and neurotransmitter support",
            "benefits": ["Muscle protein synthesis", "Recovery", "Mood support", "Energy"],
            "dosage": "10-15g daily",
            "price_range": "$40-60",
            "demographic_targets": ["athletes", "men", "women"],
            "product_url": "https://apexenergetics.com"
        },
        {
            "name": "Men's Multivitamin Elite",
            "brand": "Thorne",
            "category": "multivitamin",
            "priority": 6,
            "description": "Comprehensive multivitamin designed specifically for active men",
            "benefits": ["Nutrient gaps coverage", "Energy support", "Antioxidant protection", "Testosterone support"],
            "dosage": "3 capsules daily with meals",
            "price_range": "$45-55",
            "demographic_targets": ["men", "athletes"],
            "product_url": "https://thorne.com/products/dp/mens-multi-50"
        },
        {
            "name": "Women's Multivitamin Elite",
            "brand": "Thorne",
            "category": "multivitamin",
            "priority": 6,
            "description": "Comprehensive multivitamin designed specifically for active women",
            "benefits": ["Iron support", "Bone health", "Energy metabolism", "Hormonal balance"],
            "dosage": "3 capsules daily with meals",
            "price_range": "$45-55",
            "demographic_targets": ["women"],
            "product_url": "https://thorne.com/products/dp/womens-multi-50"
        },
        {
            "name": "Oura Ring Gen 3",
            "brand": "Oura",
            "category": "device",
            "priority": 7,
            "description": "Advanced sleep and recovery tracking with heart rate variability monitoring",
            "benefits": ["Sleep optimization", "Recovery tracking", "HRV monitoring", "Activity tracking"],
            "dosage": "Wear 24/7",
            "price_range": "$299-399",
            "demographic_targets": ["men", "women", "athletes"],
            "product_url": "https://ouraring.com"
        }
    ]
    
    # Sample Biohacking Tips
    biohacks = [
        {
            "title": "Cold Shower Protocol",
            "category": "Recovery",
            "description": "End your shower with 30-90 seconds of cold water to boost metabolism and recovery",
            "instructions": [
                "Start with warm shower as normal",
                "Gradually turn water to cold for last 30 seconds",
                "Breathe deeply and stay calm",
                "Gradually increase duration to 90 seconds",
                "Practice daily for best results"
            ],
            "difficulty_level": "Beginner",
            "time_required": "1-2 minutes",
            "cost": "Free"
        },
        {
            "title": "Morning Sun Exposure",
            "category": "Circadian Rhythm",
            "description": "Get 10-30 minutes of morning sunlight to optimize circadian rhythm and vitamin D production",
            "instructions": [
                "Step outside within 30 minutes of waking",
                "Face east toward the sun",
                "Avoid sunglasses for first 10 minutes",
                "Expose as much skin as comfortable",
                "Combine with light movement or meditation"
            ],
            "difficulty_level": "Beginner",
            "time_required": "10-30 minutes",
            "cost": "Free"
        },
        {
            "title": "Box Breathing Protocol",
            "category": "Stress Management",
            "description": "4-4-4-4 breathing pattern to activate parasympathetic nervous system",
            "instructions": [
                "Inhale for 4 counts",
                "Hold breath for 4 counts",
                "Exhale for 4 counts",
                "Hold empty for 4 counts",
                "Repeat for 5-10 cycles"
            ],
            "difficulty_level": "Beginner",
            "time_required": "2-5 minutes",
            "cost": "Free"
        }
    ]
    
    # Sample Coaches — including Laura Zook (Hackster founder/lead coach)
    coaches = [
        {
            "name": "Laura Zook",
            "credentials": ["Certified Health Coach", "Hackster Founder", "Bioenergy Practitioner", "FREEDOM Method Coach"],
            "specialties": ["Longevity", "Vitality", "Bioenergy", "Frequency Therapy", "Weight Management", "Energy", "Immune Support", "Stem Cell Health"],
            "location": "United States (Virtual)",
            "bio": "Founder of Hackster.ai and a certified health coach focused on helping busy professionals optimize energy, vitality, and longevity. Laura works with partner technologies like Bio-Well bioenergy scans, CuraWaves frequency therapy, and StemRegen to design personalized stacks. She uses the proprietary F.R.E.E.D.O.M. Method to align mind, body, and spirit.",
            "hourly_rate": "$175-250",
            "availability": "Mon-Fri 9AM-5PM CT (Virtual sessions)",
            "contact_info": {"email": "laura@hackster.ai", "phone": "(555) 010-0001"},
            "rating": 5.0,
            "total_reviews": 86,
            "years_experience": 10,
            "profile_image": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://hackster.ai/coaches/laura-zook"
        },
        {
            "name": "Dr. Sarah Martinez",
            "credentials": ["PhD Nutrition Science", "Certified Functional Medicine Practitioner"],
            "specialties": ["Hormone Optimization", "Gut Health", "Weight Management", "Weight Loss"],
            "location": "Los Angeles, CA",
            "bio": "15+ years helping clients optimize health through personalized nutrition and lifestyle interventions, with a special focus on sustainable weight loss and metabolic health.",
            "hourly_rate": "$150-200",
            "availability": "Mon-Fri 9AM-6PM PST",
            "contact_info": {"email": "sarah@hackstercoach.com", "phone": "(555) 123-4567"},
            "rating": 4.9,
            "total_reviews": 127,
            "years_experience": 15,
            "profile_image": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://sarahmartinez-wellness.com"
        },
        {
            "name": "Mike Chen",
            "credentials": ["NASM-CPT", "Precision Nutrition Level 2", "Wim Hof Method Instructor"],
            "specialties": ["Athletic Performance", "Cold Therapy", "Breathwork", "Energy", "Recovery"],
            "location": "Austin, TX",
            "bio": "Former professional athlete turned biohacking coach specializing in performance, energy, and recovery optimization using cold therapy, breathwork, and frequency-based devices.",
            "hourly_rate": "$100-150",
            "availability": "Tue-Sat 6AM-8PM CST",
            "contact_info": {"email": "mike@hackstercoach.com", "phone": "(555) 987-6543"},
            "rating": 4.8,
            "total_reviews": 89,
            "years_experience": 8,
            "profile_image": "https://images.unsplash.com/photo-1568602471122-7832951cc4c5?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://mikechen-performance.com"
        },
        {
            "name": "Dr. Lisa Thompson",
            "credentials": ["MD", "Functional Medicine Certified", "Biohacking Institute Graduate"],
            "specialties": ["Longevity", "Biohacking", "Sleep Optimization", "Stress Management", "Vitality", "Stem Cell Health"],
            "location": "New York, NY",
            "bio": "Medical doctor specializing in longevity and biohacking protocols. Integrates StemRegen, Bio-Well bioenergy scans, and advanced lab testing to help clients optimize their healthspan.",
            "hourly_rate": "$200-300",
            "availability": "Mon-Thu 10AM-4PM EST",
            "contact_info": {"email": "lisa@longevityhub.com", "phone": "(555) 234-5678"},
            "rating": 4.95,
            "total_reviews": 203,
            "years_experience": 12,
            "profile_image": "https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://longevityhub.com"
        },
        {
            "name": "Dr. James Okafor",
            "credentials": ["MD", "Integrative Medicine", "Bio-Well Certified Practitioner"],
            "specialties": ["Immune Support", "Bioenergy", "Longevity", "Vitality", "Stress Management"],
            "location": "Atlanta, GA (Virtual available)",
            "bio": "Integrative MD with deep experience in immune optimization and bioenergy assessment. Uses Bio-Well GDV scanning, targeted nutraceuticals, and lifestyle protocols for resilient immunity and healthspan.",
            "hourly_rate": "$180-240",
            "availability": "Mon-Fri 11AM-7PM EST",
            "contact_info": {"email": "james@hackster.ai", "phone": "(555) 010-0002"},
            "rating": 4.9,
            "total_reviews": 71,
            "years_experience": 14,
            "profile_image": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://hackster.ai/coaches/james-okafor"
        },
        {
            "name": "Maya Patel",
            "credentials": ["RD", "CSSD", "Functional Nutrition Coach"],
            "specialties": ["Weight Loss", "Weight Management", "Metabolic Health", "Gut Health", "Energy", "Nutrition"],
            "location": "Denver, CO (Virtual)",
            "bio": "Registered dietitian and metabolic-health specialist. Helps clients lose weight sustainably with personalized nutrition, blood-sugar balancing, and targeted supplementation including Berberine and CuraWaves protocols.",
            "hourly_rate": "$120-170",
            "availability": "Mon-Fri 8AM-6PM MT",
            "contact_info": {"email": "maya@hackster.ai", "phone": "(555) 010-0003"},
            "rating": 4.85,
            "total_reviews": 102,
            "years_experience": 9,
            "profile_image": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400",
            "is_approved": True,
            "is_active": True,
            "website": "https://hackster.ai/coaches/maya-patel"
        }
    ]
    
    # Insert sample data if collections are empty
    if await db.health_tests.count_documents({}) == 0:
        health_test_docs = [HealthTest(**test).dict() for test in health_tests]
        await db.health_tests.insert_many(health_test_docs)
    
    if await db.supplements.count_documents({}) == 0:
        supplement_docs = [Supplement(**supp).dict() for supp in supplements]
        await db.supplements.insert_many(supplement_docs)
    
    if await db.biohacks.count_documents({}) == 0:
        biohack_docs = [BiohackingTip(**tip).dict() for tip in biohacks]
        await db.biohacks.insert_many(biohack_docs)
    
    if await db.coaches.count_documents({}) == 0:
        coach_docs = [Coach(**coach).dict() for coach in coaches]
        await db.coaches.insert_many(coach_docs)
    else:
        # Upsert new coaches by name (e.g. Laura Zook, James Okafor, Maya Patel) without
        # duplicating existing ones
        for coach in coaches:
            existing = await db.coaches.find_one({"name": coach["name"]})
            if not existing:
                doc = Coach(**coach).dict()
                await db.coaches.insert_one(doc)
    
    # Sample Community Posts
    if await db.posts.count_documents({}) == 0:
        sample_posts = [
            {
                "user_id": "sample_user_1",
                "username": "BiohackerPro",
                "title": "My 30-Day Cold Exposure Journey - Incredible Results!",
                "content": "Started with 30-second cold showers and worked up to 3-minute ice baths. The mental clarity and energy boost has been incredible. Here's what I learned:\n\n1. Week 1-2: Focus on breathing and staying calm\n2. Week 3-4: Gradually increase duration\n3. Week 5+: Ice baths for maximum benefits\n\nThe key is consistency and proper breathing techniques. Would love to hear about others' experiences!",
                "category": "recovery",
                "upvotes": 24,
                "downvotes": 2,
                "reaction_counts": {"tried_this": 8, "helpful": 12, "results": 5},
                "comments_count": 7,
                "created_at": datetime.utcnow()
            },
            {
                "user_id": "sample_user_2", 
                "username": "OptimizeDaily",
                "title": "Vitamin D3 + K2 Protocol Results After 3 Months",
                "content": "After 3 months on this protocol, my energy levels have improved significantly. Blood work shows optimal vitamin D levels for the first time in years.\n\nProtocol:\n- 5000 IU Vitamin D3 daily\n- 200mcg Vitamin K2 (MK-7)\n- Taken with healthy fats\n\nResults:\n- Energy up 40%\n- Better sleep quality\n- Improved mood\n- Optimal blood levels (72 ng/mL)\n\nHighly recommend getting baseline testing first!",
                "category": "supplements",
                "upvotes": 18,
                "downvotes": 1,
                "reaction_counts": {"helpful": 15, "on_point": 7, "results": 9},
                "comments_count": 12,
                "created_at": datetime.utcnow()
            },
            {
                "user_id": "sample_user_3",
                "username": "SleepOptimizer",
                "title": "Sleep Tracking Data: What 6 Months of Oura Ring Taught Me",
                "content": "Been tracking my sleep with Oura Ring for 6 months. Here are the biggest insights:\n\n🔍 Key Findings:\n- Room temperature matters MORE than I thought (65-67°F optimal)\n- Blue light blockers actually work (HRV improved 15%)\n- Magnesium timing is crucial (2 hours before bed)\n- Weekend sleep debt is real\n\n📊 Average improvements:\n- Deep sleep: +23%\n- REM sleep: +18%\n- Sleep efficiency: 91%\n- Resting HR: -8 BPM\n\nHappy to share my complete protocol if anyone's interested!",
                "category": "sleep",
                "upvotes": 31,
                "downvotes": 0,
                "reaction_counts": {"helpful": 22, "results": 15, "tried_this": 6},
                "comments_count": 18,
                "created_at": datetime.utcnow()
            }
        ]
        
        for post_data in sample_posts:
            post = Post(**post_data)
            await db.posts.insert_one(post.dict())
    
    # Sample Users with levels
    if await db.users.count_documents({"username": {"$in": ["BiohackerPro", "OptimizeDaily", "SleepOptimizer"]}}) == 0:
        sample_users = [
            {
                "email": "biohacker@hackster.ai",
                "username": "BiohackerPro", 
                "hashed_password": get_password_hash("password123"),
                "role": "member",
                "level": "contributor",
                "reputation_score": 125,
                "posts_count": 15,
                "comments_count": 42,
                "reactions_received": 89
            },
            {
                "email": "optimizer@hackster.ai",
                "username": "OptimizeDaily",
                "hashed_password": get_password_hash("password123"),
                "role": "member", 
                "level": "hackster_pro",
                "reputation_score": 285,
                "posts_count": 28,
                "comments_count": 67,
                "reactions_received": 156
            },
            {
                "email": "sleepoptimizer@hackster.ai",
                "username": "SleepOptimizer",
                "hashed_password": get_password_hash("password123"),
                "role": "member",
                "level": "hackster_pro", 
                "reputation_score": 340,
                "posts_count": 35,
                "comments_count": 89,
                "reactions_received": 201
            }
        ]
        
        for user_data in sample_users:
            user = UserInDB(**user_data)
            await db.users.insert_one(user.dict())
    
    # ============== MARKETPLACE SAMPLE DATA ==============
    # Sample Vendors (upsert by slug so new vendors get added on restart)
    if True:
        sample_vendors = [
            {
                "name": "Thorne",
                "slug": "thorne",
                "description": "Science-backed supplements with the highest quality standards. Trusted by healthcare practitioners worldwide.",
                "logo_url": "https://cdn.thorne.com/logo.png",
                "website": "https://thorne.com",
                "affiliate_url_pattern": "https://thorne.com/products/dp/{product_slug}?aff=hackster",
                "commission_rate": 0.15,
                "status": "active",
                "shipping_info": "Free shipping on orders $50+. Ships within 1-2 business days.",
                "return_policy": "60-day satisfaction guarantee",
                "categories": ["supplements", "vitamins", "minerals", "amino_acids", "probiotics"]
            },
            {
                "name": "Apex Energetics",
                "slug": "apex-energetics",
                "description": "Practitioner-grade supplements designed for optimal therapeutic outcomes.",
                "logo_url": "https://apexenergetics.com/logo.png",
                "website": "https://apexenergetics.com",
                "affiliate_url_pattern": "https://apexenergetics.com/products/{product_slug}?ref=hackster",
                "commission_rate": 0.12,
                "status": "active",
                "shipping_info": "Ships within 2-3 business days.",
                "return_policy": "30-day return policy",
                "categories": ["supplements", "adaptogens", "amino_acids"]
            },
            {
                "name": "Standard Process",
                "slug": "standard-process",
                "description": "Whole food-based supplements made from organically grown ingredients.",
                "logo_url": "https://standardprocess.com/logo.png",
                "website": "https://standardprocess.com",
                "affiliate_url_pattern": "https://standardprocess.com/products/{product_slug}?partner=hackster",
                "commission_rate": 0.10,
                "status": "active",
                "shipping_info": "Ships within 2-4 business days.",
                "return_policy": "30-day return policy",
                "categories": ["supplements", "vitamins", "minerals"]
            },
            {
                "name": "Oura",
                "slug": "oura",
                "description": "Advanced wearable technology for sleep and recovery tracking.",
                "logo_url": "https://ouraring.com/logo.png",
                "website": "https://ouraring.com",
                "affiliate_url_pattern": "https://ouraring.com/product/{product_slug}?ref=hackster",
                "commission_rate": 0.08,
                "status": "active",
                "shipping_info": "Free shipping. Ships within 3-5 business days.",
                "return_policy": "30-day return policy",
                "categories": ["devices"]
            },
            {
                "name": "Bio-Well",
                "slug": "bio-well",
                "description": "Non-invasive bioenergy assessment using Gas Discharge Visualization (GDV) technology. Scans fingertips to map your energy field, stress response, and overall vitality.",
                "logo_url": "https://bio-well.com/logo.png",
                "website": "https://bio-well.com",
                "affiliate_url_pattern": "https://bio-well.com/products/{product_slug}?ref=hackster",
                "commission_rate": 0.10,
                "status": "active",
                "shipping_info": "Ships within 5-7 business days.",
                "return_policy": "30-day return policy",
                "categories": ["devices", "lab_tests"]
            },
            {
                "name": "CuraWaves",
                "slug": "curawaves",
                "description": "Frequency-based wellness device using square-wave (Rife-style) electrotherapy with 400+ pre-programmed sessions for energy, weight management, sleep, pain, and detoxification. NOT a PEMF device.",
                "logo_url": "https://curawaves.com/logo.png",
                "website": "https://curawaves.com",
                "affiliate_url_pattern": "https://curawaves.com/products/{product_slug}?ref=hackster",
                "commission_rate": 0.12,
                "status": "active",
                "shipping_info": "Free US shipping. Ships within 3-5 business days.",
                "return_policy": "30-day return policy with coaching support",
                "categories": ["devices", "recovery", "energy"]
            },
            {
                "name": "StemRegen",
                "slug": "stemregen",
                "description": "Plant-based stem cell mobilizers and longevity supplements that support your body's natural stem cell release, migration, and circulation for recovery and healthspan.",
                "logo_url": "https://stemregen.co/logo.png",
                "website": "https://stemregen.co",
                "affiliate_url_pattern": "https://stemregen.co/products/{product_slug}?ref=hackster",
                "commission_rate": 0.15,
                "status": "active",
                "shipping_info": "Free shipping on orders $100+. Ships within 1-3 business days.",
                "return_policy": "60-day satisfaction guarantee",
                "categories": ["supplements", "recovery"]
            }
        ]
        
        for vendor_data in sample_vendors:
            vendor = Vendor(**vendor_data)
            doc = vendor.dict()
            await db.vendors.update_one(
                {"slug": doc["slug"]},
                {"$setOnInsert": doc},
                upsert=True
            )

        # Standard Process & Apex Energetics are fulfilled via Hackster's practitioner
        # accounts (Laura places the orders) rather than a public affiliate link.
        await db.vendors.update_one(
            {"slug": "apex-energetics"},
            {"$set": {"fulfillment_type": "practitioner_order"}}
        )
        await db.vendors.update_one(
            {"slug": "standard-process"},
            {"$set": {"fulfillment_type": "practitioner_order"}}
        )

    # Seed the platform admin account (idempotent)
    admin_email = "lzook@plzcompany.com"
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin_user = UserInDB(
            email=admin_email,
            username="lauraadmin",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("HacksterAdmin2025!"),
        )
        await db.users.insert_one(admin_user.dict())
        logging.info("Seeded admin user lzook@plzcompany.com")
    else:
        # Ensure the account always has admin role
        await db.users.update_one({"email": admin_email}, {"$set": {"role": "admin"}})

    # Seed a demo member with a pre-populated mixed-vendor stack (for one-click checkout demo/testing)
    demo_email = "demo@hackster.ai"
    demo = await db.users.find_one({"email": demo_email})
    if not demo:
        demo_user = UserInDB(
            email=demo_email,
            username="demohacker",
            role=UserRole.MEMBER,
            hashed_password=get_password_hash("Demo12345!"),
        )
        await db.users.insert_one(demo_user.dict())
        demo = demo_user.dict()
    demo_id = demo["id"]
    existing_stack = await db.stacks.find_one({"user_id": demo_id})
    if not existing_stack:
        wanted_slugs = ["vitamin-d-5000", "magnesium-bisglycinate", "resvero-active"]
        stack_items = []
        for slug in wanted_slugs:
            p = await db.marketplace_products.find_one({"slug": slug})
            if p:
                stack_items.append(WishlistItem(
                    product_id=p["id"],
                    product_name=p["name"],
                    vendor_name=p["vendor_name"],
                    price=(p.get("sale_price") or p["price"]),
                    image_url=p.get("image_url"),
                    priority=1,
                ).dict())
        if stack_items:
            demo_stack = HacksterStack(
                user_id=demo_id,
                username="demohacker",
                name="My Wellness Stack",
                description="A demo stack spanning affiliate and practitioner-order vendors.",
                share_token=str(uuid.uuid4())[:8],
                items=stack_items,
                total_value=sum(i["price"] for i in stack_items),
                is_ai_generated=True,
            )
            await db.stacks.insert_one(demo_stack.dict())
            logging.info("Seeded demo member + wellness stack")
    
    # Sample Marketplace Products (upsert by slug so new products get added on restart)
    if True:
        sample_products = [
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "D138",
                "name": "Vitamin D-5,000",
                "slug": "vitamin-d-5000",
                "description": "Each capsule contains 5,000 IU of vitamin D3 to maintain healthy levels of vitamin D for bone, immune, and cardiovascular health.",
                "short_description": "5,000 IU vitamin D3 for immune and bone support",
                "category": "vitamins",
                "price": 19.00,
                "sale_price": None,
                "image_url": "https://d1vo8zfysxy97v.cloudfront.net/media/product/d138__v6d6301b3870baca3936f42dd3ac197ac421e097e.png",
                "affiliate_url": "https://thorne.com/products/dp/vitamin-d-5000?aff=hackster",
                "benefits": ["Immune system support", "Bone health", "Cardiovascular support", "Mood regulation"],
                "dosage_instructions": "Take 1 capsule daily or as recommended by your health professional",
                "health_goals": ["immune_support", "energy", "longevity"],
                "demographic_targets": ["men", "women", "athletes", "seniors"],
                "rating": 4.9,
                "review_count": 2547,
                "is_featured": True,
                "priority_score": 95,
                "tags": ["vitamin d", "immune", "bones", "bestseller"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "M284",
                "name": "Magnesium Bisglycinate",
                "slug": "magnesium-bisglycinate",
                "description": "Highly absorbable magnesium chelate that promotes restful sleep, helps muscles relax, and supports stress management.",
                "short_description": "Highly absorbable magnesium for sleep and relaxation",
                "category": "minerals",
                "price": 25.00,
                "sale_price": None,
                "image_url": "https://d1vo8zfysxy97v.cloudfront.net/media/product/m284__v722511088310a527d9bd4f32ff1f8a38e3e4fa0f.png",
                "affiliate_url": "https://thorne.com/products/dp/magnesium-bisglycinate?aff=hackster",
                "benefits": ["Better sleep quality", "Muscle relaxation", "Stress reduction", "Energy production"],
                "dosage_instructions": "Take 1-2 capsules daily, preferably in the evening",
                "health_goals": ["sleep", "stress_management", "athletic_performance"],
                "demographic_targets": ["men", "women", "athletes"],
                "rating": 4.8,
                "review_count": 1823,
                "is_featured": True,
                "priority_score": 90,
                "tags": ["magnesium", "sleep", "relaxation", "recovery"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SP608NC",
                "name": "Super EPA",
                "slug": "super-epa",
                "description": "High-concentration EPA fish oil for cardiovascular, brain, and joint support with superior absorption.",
                "short_description": "High-potency omega-3 EPA for heart and brain health",
                "category": "supplements",
                "price": 40.00,
                "sale_price": None,
                "image_url": "https://d1vo8zfysxy97v.cloudfront.net/media/product/sp608nc__v85ffd3158c5fcd199d35f8f66966125217d62306.png",
                "affiliate_url": "https://thorne.com/products/dp/super-epa?aff=hackster",
                "benefits": ["Heart health", "Brain function", "Joint support", "Anti-inflammatory"],
                "dosage_instructions": "Take 2-3 gelcaps daily with food",
                "health_goals": ["heart_health", "focus", "longevity"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.7,
                "review_count": 1456,
                "is_featured": True,
                "priority_score": 85,
                "tags": ["omega-3", "fish oil", "EPA", "heart health"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF828",
                "name": "Ashwagandha",
                "slug": "ashwagandha",
                "description": "Clinically studied Sensoril ashwagandha for stress resilience, mental clarity, and hormonal balance.",
                "short_description": "Premium ashwagandha for stress and adaptogen support",
                "category": "adaptogens",
                "price": 21.00,
                "sale_price": None,
                "image_url": "https://d1vo8zfysxy97v.cloudfront.net/media/product/sf828__v859970c678922ca16ed2a0f883614b8a597361b3.png",
                "affiliate_url": "https://thorne.com/products/dp/ashwagandha?aff=hackster",
                "benefits": ["Stress resilience", "Mental clarity", "Energy levels", "Sleep quality"],
                "dosage_instructions": "Take 1 capsule two times daily",
                "health_goals": ["stress_management", "energy", "focus", "sleep"],
                "demographic_targets": ["men", "women", "athletes"],
                "rating": 4.8,
                "review_count": 987,
                "is_featured": True,
                "priority_score": 88,
                "tags": ["ashwagandha", "adaptogen", "stress", "energy"]
            },
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-EAA",
                "name": "Essential Amino Acids Complex",
                "slug": "essential-amino-acids",
                "description": "Complete spectrum of essential amino acids for muscle protein synthesis and neurotransmitter support.",
                "short_description": "Complete EAA formula for muscle and brain support",
                "category": "amino_acids",
                "price": 54.00,
                "sale_price": 48.00,
                "image_url": "https://apexenergetics.com/images/eaa-complex.png",
                "affiliate_url": "https://apexenergetics.com/products/essential-amino-acids?ref=hackster",
                "benefits": ["Muscle recovery", "Protein synthesis", "Mood support", "Energy production"],
                "dosage_instructions": "Mix 1 scoop with water, take 1-2 times daily",
                "health_goals": ["athletic_performance", "energy", "focus"],
                "demographic_targets": ["athletes", "men", "women"],
                "rating": 4.6,
                "review_count": 342,
                "is_featured": False,
                "priority_score": 75,
                "tags": ["amino acids", "EAA", "muscle", "recovery"]
            },
            {
                "vendor_id": "standard-process",
                "vendor_name": "Standard Process",
                "sku": "SP-VA",
                "name": "Cataplex A",
                "slug": "cataplex-a",
                "description": "Whole food vitamin A complex derived from organic carrots for vision, immune, and skin health.",
                "short_description": "Whole food vitamin A for vision and immune support",
                "category": "vitamins",
                "price": 28.00,
                "sale_price": None,
                "image_url": "https://standardprocess.com/images/cataplex-a.png",
                "affiliate_url": "https://standardprocess.com/products/cataplex-a?partner=hackster",
                "benefits": ["Vision support", "Immune function", "Skin health", "Antioxidant protection"],
                "dosage_instructions": "Take 1 tablet 3 times daily with meals",
                "health_goals": ["immune_support", "skin_health"],
                "demographic_targets": ["men", "women"],
                "rating": 4.5,
                "review_count": 567,
                "is_featured": False,
                "priority_score": 70,
                "tags": ["vitamin a", "vision", "immune", "whole food"]
            },
            {
                "vendor_id": "oura",
                "vendor_name": "Oura",
                "sku": "OURA-G3",
                "name": "Oura Ring Generation 3",
                "slug": "oura-ring-gen3",
                "description": "Advanced health tracking ring with sleep analysis, readiness scores, and activity tracking.",
                "short_description": "Premium sleep and recovery tracking wearable",
                "category": "devices",
                "price": 299.00,
                "sale_price": None,
                "image_url": "https://ouraring.com/images/oura-ring-gen3.png",
                "affiliate_url": "https://ouraring.com/product/oura-ring-gen3?ref=hackster",
                "benefits": ["Sleep tracking", "HRV monitoring", "Activity tracking", "Recovery scores"],
                "dosage_instructions": "Wear 24/7 for best tracking results",
                "health_goals": ["sleep", "athletic_performance", "longevity"],
                "demographic_targets": ["men", "women", "athletes"],
                "rating": 4.7,
                "review_count": 15234,
                "is_featured": True,
                "priority_score": 92,
                "tags": ["wearable", "sleep tracker", "HRV", "biohacking"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF674",
                "name": "NiaCel 400",
                "slug": "niacel-400",
                "description": "Nicotinamide riboside (NR) for cellular energy, healthy aging, and NAD+ support.",
                "short_description": "NAD+ precursor for cellular energy and longevity",
                "category": "supplements",
                "price": 68.00,
                "sale_price": None,
                "image_url": "https://d1vo8zfysxy97v.cloudfront.net/media/product/niacel.png",
                "affiliate_url": "https://thorne.com/products/dp/niacel-400?aff=hackster",
                "benefits": ["Cellular energy", "Healthy aging", "Brain function", "Metabolic support"],
                "dosage_instructions": "Take 1 capsule twice daily",
                "health_goals": ["longevity", "energy", "focus"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.6,
                "review_count": 678,
                "is_featured": True,
                "priority_score": 82,
                "tags": ["NAD+", "NR", "longevity", "cellular health"]
            },

            # ===== Additional Thorne products =====
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF722",
                "name": "CoQ10",
                "slug": "coq10",
                "description": "Ubiquinone CoQ10 supports cellular energy (ATP) production and cardiovascular health.",
                "short_description": "CoQ10 for cellular energy and heart health",
                "category": "supplements",
                "price": 38.00,
                "image_url": "https://www.thorne.com/images/coq10.png",
                "affiliate_url": "https://thorne.com/products/dp/coq10?aff=hackster",
                "benefits": ["Cellular energy", "Heart health", "Antioxidant"],
                "dosage_instructions": "Take 1 capsule twice daily with food",
                "health_goals": ["energy", "heart_health", "longevity"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.7, "review_count": 845, "is_featured": True, "priority_score": 86,
                "tags": ["CoQ10", "energy", "heart", "longevity"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "B252",
                "name": "B-Complex #12",
                "slug": "b-complex-12",
                "description": "Comprehensive B-vitamin complex with active methylated forms of B12 and folate for energy production.",
                "short_description": "Methylated B-complex for energy & methylation",
                "category": "vitamins",
                "price": 26.00,
                "image_url": "https://www.thorne.com/images/b-complex-12.png",
                "affiliate_url": "https://thorne.com/products/dp/b-complex-12?aff=hackster",
                "benefits": ["Energy production", "Nervous system support", "Methylation"],
                "dosage_instructions": "Take 1 capsule daily with breakfast",
                "health_goals": ["energy", "focus", "stress_management"],
                "demographic_targets": ["men", "women"],
                "rating": 4.8, "review_count": 1102, "is_featured": True, "priority_score": 87,
                "tags": ["B-complex", "methylated", "energy"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF767",
                "name": "Basic Nutrients 2/Day",
                "slug": "basic-nutrients-2-day",
                "description": "Comprehensive daily multivitamin with optimal levels of foundational vitamins & minerals — only two capsules per day.",
                "short_description": "All-in-one foundational multivitamin",
                "category": "vitamins",
                "price": 32.00,
                "image_url": "https://www.thorne.com/images/basic-nutrients.png",
                "affiliate_url": "https://thorne.com/products/dp/basic-nutrients-2-day?aff=hackster",
                "benefits": ["Foundational nutrition", "Energy", "Immune support"],
                "dosage_instructions": "Take 2 capsules daily with food",
                "health_goals": ["energy", "immune_support", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.8, "review_count": 1690, "is_featured": True, "priority_score": 90,
                "tags": ["multivitamin", "foundational", "energy"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF811",
                "name": "Berberine",
                "slug": "berberine-thorne",
                "description": "Berberine supports healthy blood sugar, cholesterol, and metabolic balance — a key tool for weight management.",
                "short_description": "Metabolic + blood-sugar support for weight loss",
                "category": "supplements",
                "price": 42.00,
                "image_url": "https://www.thorne.com/images/berberine.png",
                "affiliate_url": "https://thorne.com/products/dp/berberine?aff=hackster",
                "benefits": ["Blood sugar balance", "Metabolic support", "Weight management"],
                "dosage_instructions": "Take 1 capsule twice daily with meals",
                "health_goals": ["weight_management", "heart_health", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.7, "review_count": 723, "is_featured": True, "priority_score": 84,
                "tags": ["berberine", "weight loss", "metabolic"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF918",
                "name": "Curcumin Phytosome",
                "slug": "curcumin-phytosome",
                "description": "Highly bioavailable curcumin (Meriva®) for systemic inflammation, joint, and immune support.",
                "short_description": "Bioavailable curcumin for inflammation & immune",
                "category": "supplements",
                "price": 56.00,
                "image_url": "https://www.thorne.com/images/curcumin-phytosome.png",
                "affiliate_url": "https://thorne.com/products/dp/curcumin-phytosome?aff=hackster",
                "benefits": ["Anti-inflammatory", "Immune support", "Joint health"],
                "dosage_instructions": "Take 2 capsules twice daily",
                "health_goals": ["immune_support", "longevity", "heart_health"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.8, "review_count": 612, "is_featured": False, "priority_score": 80,
                "tags": ["curcumin", "anti-inflammatory", "immune"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "WP010",
                "name": "Whey Protein Isolate",
                "slug": "whey-protein-isolate",
                "description": "Grass-fed whey isolate for lean muscle maintenance and weight-management support.",
                "short_description": "Clean whey for body composition & energy",
                "category": "supplements",
                "price": 48.00,
                "image_url": "https://www.thorne.com/images/whey-isolate.png",
                "affiliate_url": "https://thorne.com/products/dp/whey-protein-isolate?aff=hackster",
                "benefits": ["Lean muscle", "Satiety", "Recovery"],
                "dosage_instructions": "1 scoop with water or milk, 1-2 times daily",
                "health_goals": ["weight_management", "athletic_performance", "energy"],
                "demographic_targets": ["men", "women", "athletes"],
                "rating": 4.7, "review_count": 998, "is_featured": False, "priority_score": 78,
                "tags": ["protein", "whey", "weight loss"]
            },
            {
                "vendor_id": "thorne",
                "vendor_name": "Thorne",
                "sku": "SF802",
                "name": "MediClear-SGS",
                "slug": "mediclear-sgs",
                "description": "Functional medicine detox & weight-management shake with rice/pea protein, fiber, and broccoli-seed extract.",
                "short_description": "Detox + weight-management daily shake",
                "category": "supplements",
                "price": 79.00,
                "image_url": "https://www.thorne.com/images/mediclear-sgs.png",
                "affiliate_url": "https://thorne.com/products/dp/mediclear-sgs?aff=hackster",
                "benefits": ["Detox support", "Weight management", "Gut health"],
                "dosage_instructions": "Mix 2 scoops with 8-10 oz water once daily",
                "health_goals": ["weight_management", "gut_health", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.6, "review_count": 412, "is_featured": False, "priority_score": 76,
                "tags": ["detox", "weight loss", "shake"]
            },

            # ===== Apex Energetics extra products =====
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-K12",
                "name": "Adaptocrine",
                "slug": "adaptocrine",
                "description": "Adaptogen blend (rhodiola, ashwagandha, eleuthero) for adrenal resilience, stress, and sustained energy.",
                "short_description": "Adaptogen blend for stress & energy",
                "category": "adaptogens",
                "price": 46.00,
                "image_url": "https://apexenergetics.com/images/adaptocrine.png",
                "affiliate_url": "https://apexenergetics.com/products/adaptocrine?ref=hackster",
                "benefits": ["Adrenal support", "Sustained energy", "Stress resilience"],
                "dosage_instructions": "Take 2 capsules with breakfast",
                "health_goals": ["energy", "stress_management"],
                "demographic_targets": ["men", "women"],
                "rating": 4.7, "review_count": 256, "is_featured": True, "priority_score": 82,
                "tags": ["adaptogens", "energy", "stress"]
            },
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-K61",
                "name": "Glutathione Recycler",
                "slug": "glutathione-recycler",
                "description": "Targeted nutrients (NAC, alpha-lipoic acid, milk thistle) to support glutathione recycling for detox and immune defense.",
                "short_description": "Glutathione + antioxidant for detox & immune",
                "category": "supplements",
                "price": 39.00,
                "image_url": "https://apexenergetics.com/images/glutathione-recycler.png",
                "affiliate_url": "https://apexenergetics.com/products/glutathione-recycler?ref=hackster",
                "benefits": ["Detox support", "Antioxidant", "Immune support"],
                "dosage_instructions": "Take 2 capsules twice daily",
                "health_goals": ["immune_support", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.6, "review_count": 188, "is_featured": False, "priority_score": 78,
                "tags": ["glutathione", "antioxidant", "immune"]
            },
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-K15",
                "name": "Resvero Active",
                "slug": "resvero-active",
                "description": "High-potency liquid trans-resveratrol with quercetin for longevity, vascular, and metabolic support.",
                "short_description": "Resveratrol liquid for longevity",
                "category": "supplements",
                "price": 64.00,
                "image_url": "https://apexenergetics.com/images/resvero-active.png",
                "affiliate_url": "https://apexenergetics.com/products/resvero-active?ref=hackster",
                "benefits": ["Longevity support", "Vascular health", "Antioxidant"],
                "dosage_instructions": "1 teaspoon daily",
                "health_goals": ["longevity", "heart_health"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.7, "review_count": 211, "is_featured": True, "priority_score": 85,
                "tags": ["resveratrol", "longevity", "antiaging"]
            },
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-K23",
                "name": "Glysen Synergy",
                "slug": "glysen-synergy",
                "description": "Botanical blend supporting healthy blood-sugar regulation, insulin sensitivity, and metabolic balance.",
                "short_description": "Blood sugar & insulin support for weight loss",
                "category": "supplements",
                "price": 52.00,
                "image_url": "https://apexenergetics.com/images/glysen-synergy.png",
                "affiliate_url": "https://apexenergetics.com/products/glysen-synergy?ref=hackster",
                "benefits": ["Blood sugar balance", "Insulin sensitivity", "Weight management"],
                "dosage_instructions": "Take 2 capsules with each meal",
                "health_goals": ["weight_management", "heart_health"],
                "demographic_targets": ["men", "women"],
                "rating": 4.6, "review_count": 174, "is_featured": False, "priority_score": 77,
                "tags": ["blood sugar", "weight loss", "metabolic"]
            },
            {
                "vendor_id": "apex-energetics",
                "vendor_name": "Apex Energetics",
                "sku": "AE-K38",
                "name": "Strengtia (Probiotic)",
                "slug": "strengtia-probiotic",
                "description": "Multi-strain probiotic supporting GI and immune health.",
                "short_description": "Probiotic for gut & immune support",
                "category": "probiotics",
                "price": 42.00,
                "image_url": "https://apexenergetics.com/images/strengtia.png",
                "affiliate_url": "https://apexenergetics.com/products/strengtia?ref=hackster",
                "benefits": ["Gut health", "Immune support", "Digestion"],
                "dosage_instructions": "Take 1 capsule daily",
                "health_goals": ["gut_health", "immune_support"],
                "demographic_targets": ["men", "women"],
                "rating": 4.7, "review_count": 220, "is_featured": False, "priority_score": 76,
                "tags": ["probiotic", "gut", "immune"]
            },

            # ===== Standard Process extra products =====
            {
                "vendor_id": "standard-process",
                "vendor_name": "Standard Process",
                "sku": "SP-CAT",
                "name": "Catalyn",
                "slug": "catalyn",
                "description": "Whole-food foundational multivitamin from organically grown ingredients.",
                "short_description": "Whole-food daily multivitamin",
                "category": "vitamins",
                "price": 26.00,
                "image_url": "https://standardprocess.com/images/catalyn.png",
                "affiliate_url": "https://standardprocess.com/products/catalyn?partner=hackster",
                "benefits": ["Foundational nutrition", "Energy", "Immune support"],
                "dosage_instructions": "Take 3 tablets per meal",
                "health_goals": ["energy", "immune_support", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.6, "review_count": 412, "is_featured": False, "priority_score": 78,
                "tags": ["multivitamin", "whole food"]
            },
            {
                "vendor_id": "standard-process",
                "vendor_name": "Standard Process",
                "sku": "SP-IMP",
                "name": "Immuplex",
                "slug": "immuplex",
                "description": "Comprehensive whole-food immune-support formula with zinc, copper, and key vitamins.",
                "short_description": "Whole-food immune support",
                "category": "supplements",
                "price": 34.00,
                "image_url": "https://standardprocess.com/images/immuplex.png",
                "affiliate_url": "https://standardprocess.com/products/immuplex?partner=hackster",
                "benefits": ["Immune support", "Antioxidant", "Whole-food nutrients"],
                "dosage_instructions": "Take 2 capsules per meal",
                "health_goals": ["immune_support"],
                "demographic_targets": ["men", "women"],
                "rating": 4.7, "review_count": 521, "is_featured": True, "priority_score": 83,
                "tags": ["immune", "whole food"]
            },
            {
                "vendor_id": "standard-process",
                "vendor_name": "Standard Process",
                "sku": "SP-CE",
                "name": "Cataplex E",
                "slug": "cataplex-e",
                "description": "Whole-food vitamin E complex supporting cardiovascular function and circulation.",
                "short_description": "Vitamin E complex for circulation",
                "category": "vitamins",
                "price": 24.00,
                "image_url": "https://standardprocess.com/images/cataplex-e.png",
                "affiliate_url": "https://standardprocess.com/products/cataplex-e?partner=hackster",
                "benefits": ["Cardiovascular support", "Antioxidant"],
                "dosage_instructions": "Take 1 tablet 3 times daily",
                "health_goals": ["heart_health", "longevity"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.5, "review_count": 198, "is_featured": False, "priority_score": 70,
                "tags": ["vitamin e", "circulation"]
            },
            {
                "vendor_id": "standard-process",
                "vendor_name": "Standard Process",
                "sku": "SP-THY",
                "name": "Thymex",
                "slug": "thymex",
                "description": "Thymus protomorphogen and bovine thymus PMG for supporting immune cell function.",
                "short_description": "Thymus support for immune function",
                "category": "supplements",
                "price": 36.00,
                "image_url": "https://standardprocess.com/images/thymex.png",
                "affiliate_url": "https://standardprocess.com/products/thymex?partner=hackster",
                "benefits": ["Immune cell support", "Thymus support"],
                "dosage_instructions": "Take 2 tablets per meal",
                "health_goals": ["immune_support"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.5, "review_count": 142, "is_featured": False, "priority_score": 72,
                "tags": ["thymus", "immune"]
            },

            # ===== Bio-Well products =====
            {
                "vendor_id": "bio-well",
                "vendor_name": "Bio-Well",
                "sku": "BW-GDV",
                "name": "Bio-Well GDV Camera",
                "slug": "biowell-gdv-camera",
                "description": "At-home bioenergy scanner using Gas Discharge Visualization (GDV) technology. Place your fingertips on the sensor for a non-invasive scan that maps your energy field, stress response, organ-system balance, and overall vitality. Includes Bio-Well software subscription.",
                "short_description": "GDV bioenergy scanner — map your energy field at home",
                "category": "devices",
                "price": 2495.00,
                "image_url": "https://bio-well.com/images/gdv-camera.png",
                "affiliate_url": "https://bio-well.com/products/gdv-camera?ref=hackster",
                "benefits": ["Bioenergy baseline", "Stress tracking", "Vitality scoring", "Organ-system map"],
                "dosage_instructions": "Take a 10-finger scan 1-3x per week to track changes",
                "health_goals": ["longevity", "stress_management", "energy"],
                "demographic_targets": ["men", "women"],
                "rating": 4.6, "review_count": 187, "is_featured": True, "priority_score": 94,
                "tags": ["bioenergy", "biofield", "GDV", "baseline", "device"]
            },
            {
                "vendor_id": "bio-well",
                "vendor_name": "Bio-Well",
                "sku": "BW-SCAN",
                "name": "Bio-Well Pro Coaching Scan",
                "slug": "biowell-pro-scan",
                "description": "One-on-one Bio-Well bioenergy scan and interpretation with a certified Hackster practitioner. Full body-energy report and personalized recommendations.",
                "short_description": "Practitioner-led GDV scan + report",
                "category": "lab_tests",
                "price": 199.00,
                "image_url": "https://bio-well.com/images/pro-scan.png",
                "affiliate_url": "https://bio-well.com/services/pro-scan?ref=hackster",
                "benefits": ["Expert interpretation", "Bioenergy baseline", "Personalized protocol"],
                "dosage_instructions": "Recommended every 3-6 months",
                "health_goals": ["longevity", "stress_management", "energy"],
                "demographic_targets": ["men", "women"],
                "rating": 4.8, "review_count": 64, "is_featured": False, "priority_score": 80,
                "tags": ["bioenergy", "scan", "service", "baseline"]
            },

            # ===== CuraWaves products =====
            {
                "vendor_id": "curawaves",
                "vendor_name": "CuraWaves",
                "sku": "CW-DEVICE",
                "name": "CuraWaves Wave Therapy Device",
                "slug": "curawaves-device",
                "description": "Frequency-based wellness device (square-wave / Rife-style electrotherapy) with 400+ pre-programmed sessions for weight management, energy, sleep, pain & inflammation, circulation, and detoxification. Sessions of 15, 30, 45, or 60 minutes. Includes the FREEDOM Wellness Program. NOTE: This is NOT a PEMF device — it uses square-wave frequency currents.",
                "short_description": "Frequency device — 400+ Rife-style protocols",
                "category": "devices",
                "price": 4995.00,
                "image_url": "https://curawaves.com/images/wave-device.png",
                "affiliate_url": "https://curawaves.com/products/wave-device?ref=hackster",
                "benefits": ["Weight management programs", "Energy & vitality", "Pain & inflammation", "Detoxification", "Sleep support"],
                "dosage_instructions": "Use 15-60 min sessions, 3-5x per week per chosen protocol",
                "health_goals": ["weight_management", "energy", "longevity", "stress_management"],
                "demographic_targets": ["men", "women"],
                "rating": 4.7, "review_count": 96, "is_featured": True, "priority_score": 91,
                "tags": ["frequency", "rife", "electrotherapy", "weight loss", "device"]
            },
            {
                "vendor_id": "curawaves",
                "vendor_name": "CuraWaves",
                "sku": "CW-PREMIUM",
                "name": "CuraWaves Premium Bundle + Coaching",
                "slug": "curawaves-premium-bundle",
                "description": "The Wave Therapy device plus 1:1 health-coach onboarding, live & virtual training, and the FREEDOM Wellness Program for mind-body-spirit balance.",
                "short_description": "Wave Therapy + 1:1 coaching bundle",
                "category": "devices",
                "price": 6495.00,
                "image_url": "https://curawaves.com/images/premium-bundle.png",
                "affiliate_url": "https://curawaves.com/products/premium-bundle?ref=hackster",
                "benefits": ["Personalized protocols", "Health-coach support", "FREEDOM program", "Lifetime updates"],
                "dosage_instructions": "Personalized with coach",
                "health_goals": ["weight_management", "energy", "longevity"],
                "demographic_targets": ["men", "women"],
                "rating": 4.8, "review_count": 41, "is_featured": True, "priority_score": 88,
                "tags": ["frequency", "bundle", "coaching", "weight loss"]
            },

            # ===== StemRegen products =====
            {
                "vendor_id": "stemregen",
                "vendor_name": "StemRegen",
                "sku": "SR-MOB",
                "name": "STEMREGEN® Mobilize",
                "slug": "stemregen-mobilize",
                "description": "Patented blend (AFA, fucoidan, olive extract, NAC, sumac) that supports blood flow, endothelial glycocalyx, and the circulation of your body's own stem cells.",
                "short_description": "Stem cell circulation for recovery & longevity",
                "category": "supplements",
                "price": 79.00,
                "image_url": "https://stemregen.co/images/mobilize.png",
                "affiliate_url": "https://stemregen.co/products/mobilize?ref=hackster",
                "benefits": ["Stem cell circulation", "Endothelial health", "Recovery", "Longevity"],
                "dosage_instructions": "Take 1 stick pack or 2 capsules daily on an empty stomach",
                "health_goals": ["longevity", "athletic_performance", "heart_health"],
                "demographic_targets": ["men", "women", "athletes", "seniors"],
                "rating": 4.8, "review_count": 312, "is_featured": True, "priority_score": 93,
                "tags": ["stem cells", "longevity", "recovery", "AFA"]
            },
            {
                "vendor_id": "stemregen",
                "vendor_name": "StemRegen",
                "sku": "SR-REL",
                "name": "STEMREGEN® Release",
                "slug": "stemregen-release",
                "description": "Supports the release of stem cells from bone marrow with AFA, fucoidan, sea buckthorn, panax notoginseng, beta-glucan, and fractionated colostrum.",
                "short_description": "Bone-marrow stem-cell release support",
                "category": "supplements",
                "price": 89.00,
                "image_url": "https://stemregen.co/images/release.png",
                "affiliate_url": "https://stemregen.co/products/release?ref=hackster",
                "benefits": ["Stem cell release", "Immune support", "Longevity", "Recovery"],
                "dosage_instructions": "Take 2 capsules daily on an empty stomach",
                "health_goals": ["longevity", "immune_support", "athletic_performance"],
                "demographic_targets": ["men", "women", "athletes", "seniors"],
                "rating": 4.7, "review_count": 224, "is_featured": True, "priority_score": 88,
                "tags": ["stem cells", "AFA", "longevity"]
            },
            {
                "vendor_id": "stemregen",
                "vendor_name": "StemRegen",
                "sku": "SR-REGEN",
                "name": "STEMREGEN® RegenerEnd (Senolytic)",
                "slug": "stemregen-regenerend",
                "description": "Senolytic blend to support the natural clearance of senescent ('zombie') cells for healthy aging and tissue rejuvenation.",
                "short_description": "Senolytic support for healthy aging",
                "category": "supplements",
                "price": 95.00,
                "image_url": "https://stemregen.co/images/regenerend.png",
                "affiliate_url": "https://stemregen.co/products/regenerend?ref=hackster",
                "benefits": ["Senescent cell clearance", "Healthy aging", "Longevity"],
                "dosage_instructions": "Take 2 capsules monthly on a fasting day",
                "health_goals": ["longevity"],
                "demographic_targets": ["men", "women", "seniors"],
                "rating": 4.6, "review_count": 138, "is_featured": False, "priority_score": 82,
                "tags": ["senolytic", "longevity", "anti-aging"]
            }
        ]
        
        for product_data in sample_products:
            product = MarketplaceProduct(**product_data)
            doc = product.dict()
            await db.marketplace_products.update_one(
                {"slug": doc["slug"]},
                {"$setOnInsert": doc},
                upsert=True
            )
    
    # Hackster Health Goals Assessment — v2 (force update on restart)
    questionnaire_v2 = {
        "id": "biohacking-assessment-v2",
        "name": "Hackster Health Goals Assessment",
        "description": "A short, science-based assessment that maps you to the right Hackster Stack — supplements, devices, and a coach matched to your goals.",
        "questions": [
            # === Section 1 — About You ===
            {
                "id": "age_range",
                "question": "What is your age range?",
                "question_type": "single_choice",
                "options": ["18-29", "30-39", "40-49", "50-59", "60-69", "70+"],
                "category": "About You"
            },
            {
                "id": "gender",
                "question": "What is your biological sex?",
                "question_type": "single_choice",
                "options": ["Female", "Male", "Other / Prefer not to say"],
                "category": "About You"
            },
            {
                "id": "height_weight_goal",
                "question": "How would you describe your current body composition?",
                "question_type": "single_choice",
                "options": [
                    "I'm at a healthy weight and want to maintain",
                    "I want to lose 5-15 lbs",
                    "I want to lose 15-30 lbs",
                    "I want to lose 30+ lbs",
                    "I want to gain lean muscle"
                ],
                "category": "About You"
            },

            # === Section 2 — Your Primary Goal ===
            {
                "id": "primary_goal",
                "question": "What is your #1 health priority right now?",
                "question_type": "single_choice",
                "options": [
                    "Increase Energy",
                    "Improve Vitality / Longevity",
                    "Boost Immune System",
                    "Weight Loss / Metabolic Health"
                ],
                "category": "Primary Goal"
            },
            {
                "id": "primary_goal_why",
                "question": "Why is this your top priority? (one sentence)",
                "question_type": "text",
                "category": "Primary Goal"
            },
            {
                "id": "secondary_goals",
                "question": "Which of these matter to you as SECONDARY goals? (select all that apply)",
                "question_type": "multiple_choice",
                "options": [
                    "More Energy",
                    "Better Sleep",
                    "Longevity / Anti-aging",
                    "Stronger Immune System",
                    "Weight Loss",
                    "Mental Focus / Brain Health",
                    "Stress Resilience",
                    "Gut Health",
                    "Hormone Balance",
                    "Athletic Performance / Recovery",
                    "Healthier Skin",
                    "Heart Health"
                ],
                "category": "Primary Goal"
            },

            # === Section 3 — Current Baseline ===
            {
                "id": "energy_level",
                "question": "How would you rate your typical daily energy? (1 = exhausted, 10 = abundant)",
                "question_type": "scale",
                "scale_min": 1,
                "scale_max": 10,
                "category": "Current Baseline"
            },
            {
                "id": "sleep_quality",
                "question": "How would you rate your sleep quality? (1 = poor, 10 = excellent)",
                "question_type": "scale",
                "scale_min": 1,
                "scale_max": 10,
                "category": "Current Baseline"
            },
            {
                "id": "stress_level",
                "question": "How would you rate your daily stress? (1 = very low, 10 = overwhelming)",
                "question_type": "scale",
                "scale_min": 1,
                "scale_max": 10,
                "category": "Current Baseline"
            },
            {
                "id": "immune_resilience",
                "question": "How often do you get colds or feel run-down?",
                "question_type": "single_choice",
                "options": [
                    "Rarely (1x a year or less)",
                    "Occasionally (2-3x a year)",
                    "Often (4-6x a year)",
                    "Very often (monthly or more)"
                ],
                "category": "Current Baseline"
            },
            {
                "id": "metabolic_signals",
                "question": "Do you experience any of these? (select all that apply)",
                "question_type": "multiple_choice",
                "options": [
                    "Cravings for sugar / carbs",
                    "Energy crashes after meals",
                    "Belly fat hard to lose",
                    "Brain fog",
                    "Trouble losing weight despite effort",
                    "None of these"
                ],
                "category": "Current Baseline"
            },
            {
                "id": "health_concerns",
                "question": "Any specific health concerns? (select all that apply)",
                "question_type": "multiple_choice",
                "options": [
                    "None",
                    "Fatigue / low energy",
                    "Poor sleep",
                    "Frequent illness",
                    "Inflammation / joint pain",
                    "Mood / anxiety",
                    "Blood sugar",
                    "Thyroid",
                    "Hormonal imbalance",
                    "Gut / digestion",
                    "Heart / cholesterol"
                ],
                "category": "Current Baseline"
            },

            # === Section 4 — Lifestyle ===
            {
                "id": "exercise_frequency",
                "question": "How often do you exercise?",
                "question_type": "single_choice",
                "options": ["Never", "1-2 times/week", "3-4 times/week", "5+ times/week", "Daily"],
                "category": "Lifestyle"
            },
            {
                "id": "diet_type",
                "question": "Which best describes your diet?",
                "question_type": "single_choice",
                "options": [
                    "Standard American Diet",
                    "Mostly Healthy / Whole Foods",
                    "Mediterranean",
                    "Keto / Low Carb",
                    "Vegan / Vegetarian",
                    "Carnivore",
                    "Intermittent Fasting",
                    "Other"
                ],
                "category": "Lifestyle"
            },
            {
                "id": "current_supplements",
                "question": "Which supplements do you currently take? (select all that apply)",
                "question_type": "multiple_choice",
                "options": ["None", "Multivitamin", "Vitamin D", "Magnesium", "Omega-3 / Fish Oil", "Probiotics", "Protein Powder", "Adaptogens (Ashwagandha, Rhodiola)", "NAD+ / NR", "Berberine", "Other"],
                "category": "Lifestyle"
            },

            # === Section 5 — Preferences ===
            {
                "id": "openness_to_devices",
                "question": "How open are you to using wellness devices (e.g., bioenergy scanners, frequency therapy)?",
                "question_type": "single_choice",
                "options": [
                    "Very open — I love biohacking tools",
                    "Curious — open to learning",
                    "Maybe later — supplements first",
                    "Not interested"
                ],
                "category": "Preferences"
            },
            {
                "id": "wants_baseline_scan",
                "question": "Would you like a Bio-Well bioenergy scan to establish a baseline before optimizing?",
                "question_type": "single_choice",
                "options": ["Yes, definitely", "Maybe", "No"],
                "category": "Preferences"
            },
            {
                "id": "wants_coach",
                "question": "Are you interested in working with a Hackster health coach?",
                "question_type": "single_choice",
                "options": [
                    "Yes — I want a coach to guide me",
                    "Maybe — show me coach options",
                    "No — I'll self-direct for now"
                ],
                "category": "Preferences"
            },
            {
                "id": "budget",
                "question": "Monthly budget for supplements & wellness products?",
                "question_type": "single_choice",
                "options": ["Under $50", "$50-100", "$100-200", "$200-500", "$500+"],
                "category": "Preferences"
            }
        ]
    }

    # Force-replace the active questionnaire so users always see the latest version
    await db.questionnaire_templates.delete_many({"id": {"$in": ["biohacking-assessment-v1", "biohacking-assessment-v2"]}})
    await db.questionnaire_templates.insert_one(questionnaire_v2)

# Authentication API Routes
@api_router.post("/auth/register", response_model=dict)
async def register_user(user_data: UserRegister):
    """Register a new user (member or coach)"""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if username is taken
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
   
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    
    user_in_db = UserInDB(
        **user_dict,
        hashed_password=hashed_password
    )
    
    # Insert user into database
    await db.users.insert_one(user_in_db.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserProfile(**user_in_db.dict())
    }

@api_router.post("/auth/login", response_model=dict)
async def login_user(user_credentials: UserLogin):
    """Login an existing user"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserProfile(**user.dict())
    }

@api_router.get("/auth/me", response_model=UserProfile)
async def get_current_user_info(current_user: UserProfile = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Community API Routes
@api_router.get("/posts", response_model=List[Post])
async def get_posts(
    category: Optional[PostCategory] = None,
    limit: int = 20,
    offset: int = 0
):
    """Get community posts with optional category filtering"""
    query = {}
    if category:
        query["category"] = category
    
    posts = await db.posts.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    return [Post(**post) for post in posts]

@api_router.get("/posts/public/{post_id}", response_model=Post)
async def get_public_post(post_id: str):
    """Get a specific post by ID - PUBLIC ACCESS (no authentication required)"""
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return Post(**post)

@api_router.get("/posts/public/{post_id}/comments", response_model=List[Comment])
async def get_public_post_comments(post_id: str):
    """Get comments for a specific post - PUBLIC ACCESS (no authentication required)"""
    comments = await db.comments.find({"post_id": post_id}).sort("created_at", 1).to_list(100)
    return [Comment(**comment) for comment in comments]

@api_router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, current_user: UserProfile = Depends(get_current_user)):
    """Create a new community post"""
    post = Post(
        user_id=current_user.id,
        username=current_user.username,
        **post_data.dict()
    )
    
    # Insert post
    await db.posts.insert_one(post.dict())
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"posts_count": 1}}
    )
    
    return post

@api_router.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: str):
    """Get a specific post by ID"""
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return Post(**post)

@api_router.get("/posts/{post_id}/comments", response_model=List[Comment])
async def get_post_comments(post_id: str):
    """Get comments for a specific post"""
    comments = await db.comments.find({"post_id": post_id}).sort("created_at", 1).to_list(100)
    return [Comment(**comment) for comment in comments]

@api_router.post("/comments", response_model=Comment)
async def create_comment(comment_data: CommentCreate, current_user: UserProfile = Depends(get_current_user)):
    """Create a new comment on a post"""
    # Verify post exists
    post = await db.posts.find_one({"id": comment_data.post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = Comment(
        user_id=current_user.id,
        username=current_user.username,
        **comment_data.dict()
    )
    
    # Insert comment
    await db.comments.insert_one(comment.dict())
    
    # Update post comment count
    await db.posts.update_one(
        {"id": comment_data.post_id},
        {"$inc": {"comments_count": 1}}
    )
    
    # Update user stats
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"comments_count": 1}}
    )
    
    return comment

@api_router.post("/reactions", response_model=dict)
async def create_reaction(reaction_data: ReactionCreate, current_user: UserProfile = Depends(get_current_user)):
    """React to a post or comment"""
    # Check if user already reacted
    existing_reaction = await db.reactions.find_one({
        "user_id": current_user.id,
        "post_id": reaction_data.post_id,
        "comment_id": reaction_data.comment_id
    })
    
    if existing_reaction:
        # Update existing reaction
        await db.reactions.update_one(
            {"id": existing_reaction["id"]},
            {"$set": {"reaction_type": reaction_data.reaction_type}}
        )
    else:
        # Create new reaction
        reaction = Reaction(
            user_id=current_user.id,
            **reaction_data.dict()
        )
        await db.reactions.insert_one(reaction.dict())
    
    # Update reaction counts
    if reaction_data.post_id:
        await update_post_reaction_counts(reaction_data.post_id)
    
    return {"message": "Reaction updated successfully"}

async def update_post_reaction_counts(post_id: str):
    """Update reaction counts for a post"""
    reactions = await db.reactions.find({"post_id": post_id}).to_list(1000)
    
    reaction_counts = {}
    upvotes = 0
    downvotes = 0
    
    for reaction in reactions:
        reaction_type = reaction["reaction_type"]
        if reaction_type == "upvote":
            upvotes += 1
        elif reaction_type == "downvote":
            downvotes += 1
        else:
            reaction_counts[reaction_type] = reaction_counts.get(reaction_type, 0) + 1
    
    await db.posts.update_one(
        {"id": post_id},
        {"$set": {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "reaction_counts": reaction_counts
        }}
    )

async def update_user_level(user_id: str):
    """Update user level based on activity and reputation"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return
    
    total_activity = user.get("posts_count", 0) + user.get("comments_count", 0)
    reputation = user.get("reputation_score", 0)
    
    new_level = UserLevel.MEMBER
    if total_activity >= 10 and reputation >= 50:
        new_level = UserLevel.CONTRIBUTOR
    if total_activity >= 50 and reputation >= 200:
        new_level = UserLevel.HACKSTER_PRO
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"level": new_level}}
    )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Hackster Health Platform API", "version": "1.0.0"}

@api_router.get("/health-tests", response_model=List[HealthTest])
async def get_health_tests():
    """Get all recommended health tests"""
    tests = await db.health_tests.find().to_list(100)
    return [HealthTest(**test) for test in tests]

@api_router.get("/supplements", response_model=List[Supplement])
async def get_supplements(
    category: Optional[SupplementCategory] = None,
    demographic: Optional[DemographicTarget] = None,
    limit: int = 50
):
    """Get supplements with optional filtering"""
    query = {}
    if category:
        query["category"] = category
    if demographic:
        query["demographic_targets"] = demographic
    
    supplements = await db.supplements.find(query).sort("priority", 1).limit(limit).to_list(limit)
    return [Supplement(**supp) for supp in supplements]

@api_router.get("/supplements/priority", response_model=List[Supplement])
async def get_priority_supplements():
    """Get supplements ordered by priority"""
    supplements = await db.supplements.find().sort("priority", 1).limit(10).to_list(10)
    return [Supplement(**supp) for supp in supplements]

@api_router.get("/biohacks", response_model=List[BiohackingTip])
async def get_biohacks(category: Optional[str] = None):
    """Get free biohacking tips"""
    query = {}
    if category:
        query["category"] = category
    
    biohacks = await db.biohacks.find(query).to_list(100)
    return [BiohackingTip(**tip) for tip in biohacks]

@api_router.get("/coaches", response_model=List[Coach])
async def get_coaches(specialty: Optional[str] = None, location: Optional[str] = None):
    """Get list of available coaches"""
    query = {"is_approved": True, "is_active": True}
    if specialty:
        query["specialties"] = {"$in": [specialty]}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    
    coaches = await db.coaches.find(query).sort("rating", -1).to_list(100)
    return [Coach(**coach) for coach in coaches]

@api_router.post("/coaches", response_model=Coach)
async def create_coach_profile(coach_data: CoachProfileCreate, current_user: UserProfile = Depends(get_current_user)):
    """Create a coach profile (authenticated coaches only). Auto-approved during beta.
    Idempotent: if the user already has a coach profile, the existing one is returned."""
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Only coaches can create coach profiles")

    # Idempotent: return existing profile instead of erroring
    existing_coach = await db.coaches.find_one({"user_id": current_user.id})
    if existing_coach:
        return Coach(**existing_coach)

    coach_profile = Coach(
        user_id=current_user.id,
        is_approved=True,  # Beta: auto-approve. Toggle off when leaving beta.
        is_active=True,
        **coach_data.dict()
    )

    await db.coaches.insert_one(coach_profile.dict())
    return coach_profile


@api_router.get("/coaches/me", response_model=Optional[Coach])
async def get_my_coach_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get the current authenticated coach's own profile (returns null if not created yet)."""
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Only coaches can access this endpoint")
    coach = await db.coaches.find_one({"user_id": current_user.id})
    if not coach:
        return None
    return Coach(**coach)


@api_router.patch("/coaches/me", response_model=Coach)
async def update_my_coach_profile(coach_update: CoachProfileUpdate, current_user: UserProfile = Depends(get_current_user)):
    """Update the current authenticated coach's profile (their own only)."""
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Only coaches can update coach profiles")
    coach = await db.coaches.find_one({"user_id": current_user.id})
    if not coach:
        raise HTTPException(status_code=404, detail="Coach profile not found. Create one first.")
    update_data = {k: v for k, v in coach_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    await db.coaches.update_one({"id": coach["id"]}, {"$set": update_data})
    updated = await db.coaches.find_one({"id": coach["id"]})
    return Coach(**updated)

@api_router.get("/coaches/{coach_id}", response_model=Coach)
async def get_coach_profile(coach_id: str):
    """Get a specific coach profile"""
    coach = await db.coaches.find_one({"id": coach_id})
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return Coach(**coach)

@api_router.get("/coaches/user/{user_id}", response_model=Coach)
async def get_coach_by_user(user_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get coach profile by user ID (for profile editing)"""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    coach = await db.coaches.find_one({"user_id": user_id})
    if not coach:
        raise HTTPException(status_code=404, detail="Coach profile not found")
    return Coach(**coach)

@api_router.put("/coaches/{coach_id}", response_model=Coach)
async def update_coach_profile(coach_id: str, coach_update: CoachProfileUpdate, current_user: UserProfile = Depends(get_current_user)):
    """Update coach profile (coach owner or admin only)"""
    coach = await db.coaches.find_one({"id": coach_id})
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    # Check permissions
    if coach["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Update fields
    update_data = {k: v for k, v in coach_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.coaches.update_one(
        {"id": coach_id},
        {"$set": update_data}
    )
    
    updated_coach = await db.coaches.find_one({"id": coach_id})
    return Coach(**updated_coach)

@api_router.delete("/coaches/{coach_id}")
async def delete_coach_profile(coach_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Delete coach profile (coach owner or admin only)"""
    coach = await db.coaches.find_one({"id": coach_id})
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    # Check permissions
    if coach["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    await db.coaches.delete_one({"id": coach_id})
    return {"message": "Coach profile deleted successfully"}

# Admin endpoints for coach management
@api_router.get("/admin/coaches", response_model=List[Coach])
async def get_all_coaches_admin(current_user: UserProfile = Depends(get_current_user)):
    """Get all coaches including pending approval (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    coaches = await db.coaches.find({}).sort("created_at", -1).to_list(1000)
    return [Coach(**coach) for coach in coaches]

@api_router.put("/admin/coaches/{coach_id}/approve")
async def approve_coach(coach_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Approve a coach profile (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.coaches.update_one(
        {"id": coach_id},
        {"$set": {"is_approved": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    return {"message": "Coach approved successfully"}

@api_router.put("/admin/coaches/{coach_id}/deactivate")
async def deactivate_coach(coach_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Deactivate a coach profile (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.coaches.update_one(
        {"id": coach_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    return {"message": "Coach deactivated successfully"}

@api_router.get("/admin/coaches/export/emails")
async def export_coach_emails(current_user: UserProfile = Depends(get_current_user)):
    """Export coach emails for marketing campaigns (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all coaches with their user information
    coaches = await db.coaches.find({}).to_list(1000)
    coach_emails = []
    
    for coach in coaches:
        # Get user email from user_id
        if coach.get("user_id"):
            user = await db.users.find_one({"id": coach["user_id"]})
            if user:
                coach_emails.append({
                    "name": coach.get("name", ""),
                    "email": user.get("email", ""),
                    "location": coach.get("location", ""),
                    "specialties": coach.get("specialties", []),
                    "is_approved": coach.get("is_approved", False),
                    "is_active": coach.get("is_active", True),
                    "created_at": coach.get("created_at", ""),
                    "last_updated": coach.get("updated_at", "")
                })
        
        # Also check contact_info for email if no user_id
        if not coach.get("user_id") and coach.get("contact_info", {}).get("email"):
            coach_emails.append({
                "name": coach.get("name", ""),
                "email": coach["contact_info"]["email"],
                "location": coach.get("location", ""),
                "specialties": coach.get("specialties", []),
                "is_approved": coach.get("is_approved", False),
                "is_active": coach.get("is_active", True),
                "created_at": coach.get("created_at", ""),
                "last_updated": coach.get("updated_at", "")
            })
    
    return {
        "total_coaches": len(coach_emails),
        "approved_coaches": len([c for c in coach_emails if c["is_approved"]]),
        "active_coaches": len([c for c in coach_emails if c["is_active"]]),
        "coach_emails": coach_emails
    }

@api_router.post("/users", response_model=UserProfile)
async def create_user_profile(user_data: UserProfileCreate, current_user: UserProfile = Depends(get_current_user)):
    """Update user profile (authenticated)"""
    # Update the current user's profile
    update_data = user_data.dict()
    await db.users.update_one(
        {"email": current_user.email},
        {"$set": update_data}
    )
    
    # Return updated user
    updated_user = await get_user_by_email(current_user.email)
    return UserProfile(**updated_user.dict())

@api_router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get user profile by ID (authenticated)"""
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**user_doc)

@api_router.post("/assessments", response_model=HealthAssessment)
async def create_health_assessment(assessment_data: HealthAssessmentCreate, current_user: UserProfile = Depends(get_current_user)):
    """Create a health assessment and get recommendations (authenticated)"""
    # Ensure the assessment is for the current user
    assessment_data.user_id = current_user.id
    
    # This would contain logic to analyze responses and generate recommendations
    # For now, we'll create a basic assessment with sample recommendations
    assessment_dict = assessment_data.dict()
    assessment_dict.update({
        "recommended_tests": ["comprehensive_metabolic_panel"],
        "recommended_supplements": ["vitamin_d3_k2", "magnesium_bisglycinate"],
        "score": 75  # Sample score
    })
    
    assessment = HealthAssessment(**assessment_dict)
    
    await db.assessments.insert_one(assessment.dict())
    return assessment

@api_router.get("/assessments/{user_id}", response_model=List[HealthAssessment])
async def get_user_assessments(user_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get all assessments for a user (authenticated)"""
    # Users can only access their own assessments
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    assessments = await db.assessments.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return [HealthAssessment(**assessment) for assessment in assessments]

# ============== MARKETPLACE API ROUTES ==============

# Vendors
@api_router.get("/vendors", response_model=List[Vendor])
async def get_vendors():
    """Get all active vendors"""
    vendors = await db.vendors.find({"status": "active"}).to_list(100)
    return [Vendor(**vendor) for vendor in vendors]

@api_router.get("/vendors/{vendor_slug}", response_model=Vendor)
async def get_vendor(vendor_slug: str):
    """Get a specific vendor by slug"""
    vendor = await db.vendors.find_one({"slug": vendor_slug})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return Vendor(**vendor)

# Products
@api_router.get("/products", response_model=List[MarketplaceProduct])
async def get_products(
    category: Optional[ProductCategory] = None,
    vendor_id: Optional[str] = None,
    health_goal: Optional[HealthGoal] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "priority_score",
    limit: int = 50,
    offset: int = 0
):
    """Get marketplace products with filtering and search"""
    query = {}
    
    if category:
        query["category"] = category
    if vendor_id:
        query["vendor_id"] = vendor_id
    if health_goal:
        query["health_goals"] = health_goal
    if featured is not None:
        query["is_featured"] = featured
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query:
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search.lower()]}}
        ]
    
    sort_field = "priority_score" if sort_by == "priority_score" else sort_by
    sort_order = -1 if sort_by in ["priority_score", "rating", "review_count"] else 1
    
    products = await db.marketplace_products.find(query).sort(sort_field, sort_order).skip(offset).limit(limit).to_list(limit)
    return [MarketplaceProduct(**product) for product in products]

@api_router.get("/products/featured", response_model=List[MarketplaceProduct])
async def get_featured_products(limit: int = 10):
    """Get featured products"""
    products = await db.marketplace_products.find({"is_featured": True}).sort("priority_score", -1).limit(limit).to_list(limit)
    return [MarketplaceProduct(**product) for product in products]

@api_router.get("/products/{product_slug}", response_model=MarketplaceProduct)
async def get_product(product_slug: str):
    """Get a specific product by slug"""
    product = await db.marketplace_products.find_one({"slug": product_slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return MarketplaceProduct(**product)

@api_router.get("/products/by-goal/{health_goal}", response_model=List[MarketplaceProduct])
async def get_products_by_goal(health_goal: HealthGoal, limit: int = 10):
    """Get products recommended for a specific health goal"""
    products = await db.marketplace_products.find({"health_goals": health_goal}).sort("priority_score", -1).limit(limit).to_list(limit)
    return [MarketplaceProduct(**product) for product in products]

# Shopping Cart
@api_router.get("/cart", response_model=ShoppingCart)
async def get_cart(current_user: UserProfile = Depends(get_current_user)):
    """Get current user's shopping cart"""
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        # Create empty cart
        new_cart = ShoppingCart(user_id=current_user.id)
        await db.carts.insert_one(new_cart.dict())
        return new_cart
    return ShoppingCart(**cart)

@api_router.post("/cart/items", response_model=ShoppingCart)
async def add_to_cart(item_request: AddToCartRequest, current_user: UserProfile = Depends(get_current_user)):
    """Add item to shopping cart"""
    # Get product details
    product = await db.marketplace_products.find_one({"id": item_request.product_id})
    if not product:
        # Try by slug
        product = await db.marketplace_products.find_one({"slug": item_request.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get or create cart
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        cart = ShoppingCart(user_id=current_user.id).dict()
        await db.carts.insert_one(cart)
    
    # Check if item already in cart
    existing_item = None
    for idx, item in enumerate(cart.get("items", [])):
        if item["product_id"] == product["id"]:
            existing_item = (idx, item)
            break
    
    if existing_item:
        # Update quantity
        idx, item = existing_item
        item["quantity"] += item_request.quantity
        cart["items"][idx] = item
    else:
        # Add new item
        cart_item = CartItem(
            product_id=product["id"],
            product_name=product["name"],
            vendor_id=product["vendor_id"],
            vendor_name=product["vendor_name"],
            quantity=item_request.quantity,
            price=product.get("sale_price") or product["price"],
            image_url=product.get("image_url")
        )
        cart["items"].append(cart_item.dict())
    
    # Update subtotal
    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])
    cart["subtotal"] = subtotal
    cart["updated_at"] = datetime.utcnow()
    
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": cart}
    )
    
    return ShoppingCart(**cart)

@api_router.put("/cart/items/{item_id}", response_model=ShoppingCart)
async def update_cart_item(item_id: str, update_request: UpdateCartItemRequest, current_user: UserProfile = Depends(get_current_user)):
    """Update cart item quantity"""
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    item_found = False
    for idx, item in enumerate(cart["items"]):
        if item["id"] == item_id:
            if update_request.quantity <= 0:
                cart["items"].pop(idx)
            else:
                cart["items"][idx]["quantity"] = update_request.quantity
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    # Update subtotal
    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])
    cart["subtotal"] = subtotal
    cart["updated_at"] = datetime.utcnow()
    
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": cart}
    )
    
    return ShoppingCart(**cart)

@api_router.delete("/cart/items/{item_id}", response_model=ShoppingCart)
async def remove_from_cart(item_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Remove item from cart"""
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart["items"] = [item for item in cart["items"] if item["id"] != item_id]
    
    # Update subtotal
    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])
    cart["subtotal"] = subtotal
    cart["updated_at"] = datetime.utcnow()
    
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": cart}
    )
    
    return ShoppingCart(**cart)

@api_router.delete("/cart", response_model=dict)
async def clear_cart(current_user: UserProfile = Depends(get_current_user)):
    """Clear all items from cart"""
    await db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": {"items": [], "subtotal": 0, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Cart cleared"}

# ============== HACKSTER STACK (WISHLIST) API ROUTES ==============

@api_router.get("/stacks", response_model=List[HacksterStack])
async def get_public_stacks(
    health_goal: Optional[HealthGoal] = None,
    limit: int = 20,
    offset: int = 0
):
    """Get public/community stacks"""
    query = {"visibility": {"$in": ["community", "public"]}}
    if health_goal:
        query["health_goals"] = health_goal
    
    stacks = await db.stacks.find(query).sort("likes_count", -1).skip(offset).limit(limit).to_list(limit)
    return [HacksterStack(**stack) for stack in stacks]

@api_router.get("/stacks/my", response_model=List[HacksterStack])
async def get_my_stacks(current_user: UserProfile = Depends(get_current_user)):
    """Get current user's stacks"""
    stacks = await db.stacks.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [HacksterStack(**stack) for stack in stacks]

@api_router.post("/stacks", response_model=HacksterStack)
async def create_stack(stack_request: CreateStackRequest, current_user: UserProfile = Depends(get_current_user)):
    """Create a new Hackster Stack"""
    share_token = str(uuid.uuid4())[:8]
    
    stack = HacksterStack(
        user_id=current_user.id,
        username=current_user.username,
        share_token=share_token,
        **stack_request.dict()
    )
    
    await db.stacks.insert_one(stack.dict())
    return stack

@api_router.get("/stacks/{stack_id}", response_model=HacksterStack)
async def get_stack(stack_id: str, current_user: Optional[UserProfile] = None):
    """Get a specific stack"""
    stack = await db.stacks.find_one({"id": stack_id})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")
    
    stack_obj = HacksterStack(**stack)
    
    # Check visibility
    if stack_obj.visibility == WishlistVisibility.PRIVATE:
        if not current_user or stack_obj.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="This stack is private")
    
    return stack_obj

@api_router.get("/stacks/share/{share_token}", response_model=HacksterStack)
async def get_stack_by_share_token(share_token: str):
    """Get a stack by its share token (for gift registry)"""
    stack = await db.stacks.find_one({"share_token": share_token})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")
    return HacksterStack(**stack)

@api_router.post("/stacks/{stack_id}/items", response_model=HacksterStack)
async def add_to_stack(stack_id: str, item_request: AddToStackRequest, current_user: UserProfile = Depends(get_current_user)):
    """Add product to a stack"""
    stack = await db.stacks.find_one({"id": stack_id, "user_id": current_user.id})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found or access denied")
    
    # Get product details
    product = await db.marketplace_products.find_one({"id": item_request.product_id})
    if not product:
        product = await db.marketplace_products.find_one({"slug": item_request.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if already in stack
    for item in stack["items"]:
        if item["product_id"] == product["id"]:
            raise HTTPException(status_code=400, detail="Product already in stack")
    
    wishlist_item = WishlistItem(
        product_id=product["id"],
        product_name=product["name"],
        vendor_name=product["vendor_name"],
        price=product.get("sale_price") or product["price"],
        image_url=product.get("image_url"),
        priority=item_request.priority,
        notes=item_request.notes
    )
    
    stack["items"].append(wishlist_item.dict())
    stack["total_value"] = sum(item["price"] for item in stack["items"])
    stack["updated_at"] = datetime.utcnow()
    
    await db.stacks.update_one(
        {"id": stack_id},
        {"$set": stack}
    )
    
    return HacksterStack(**stack)

@api_router.delete("/stacks/{stack_id}/items/{item_id}", response_model=HacksterStack)
async def remove_from_stack(stack_id: str, item_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Remove item from a stack"""
    stack = await db.stacks.find_one({"id": stack_id, "user_id": current_user.id})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found or access denied")
    
    stack["items"] = [item for item in stack["items"] if item["id"] != item_id]
    stack["total_value"] = sum(item["price"] for item in stack["items"])
    stack["updated_at"] = datetime.utcnow()
    
    await db.stacks.update_one(
        {"id": stack_id},
        {"$set": stack}
    )
    
    return HacksterStack(**stack)

@api_router.post("/stacks/{stack_id}/like", response_model=dict)
async def like_stack(stack_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Like/unlike a stack"""
    existing_like = await db.stack_likes.find_one({"stack_id": stack_id, "user_id": current_user.id})
    
    if existing_like:
        await db.stack_likes.delete_one({"id": existing_like["id"]})
        await db.stacks.update_one({"id": stack_id}, {"$inc": {"likes_count": -1}})
        return {"message": "Like removed", "liked": False}
    else:
        like = StackLike(stack_id=stack_id, user_id=current_user.id)
        await db.stack_likes.insert_one(like.dict())
        await db.stacks.update_one({"id": stack_id}, {"$inc": {"likes_count": 1}})
        return {"message": "Stack liked", "liked": True}

@api_router.post("/stacks/{stack_id}/comments", response_model=StackComment)
async def add_stack_comment(stack_id: str, comment_request: StackCommentCreate, current_user: UserProfile = Depends(get_current_user)):
    """Add comment to a stack"""
    stack = await db.stacks.find_one({"id": stack_id})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")
    
    comment = StackComment(
        stack_id=stack_id,
        user_id=current_user.id,
        username=current_user.username,
        content=comment_request.content
    )
    
    await db.stack_comments.insert_one(comment.dict())
    await db.stacks.update_one({"id": stack_id}, {"$inc": {"comments_count": 1}})
    
    return comment

@api_router.get("/stacks/{stack_id}/comments", response_model=List[StackComment])
async def get_stack_comments(stack_id: str):
    """Get comments for a stack"""
    comments = await db.stack_comments.find({"stack_id": stack_id}).sort("created_at", -1).to_list(100)
    return [StackComment(**comment) for comment in comments]

# Mark item as purchased (for gift registry)
@api_router.put("/stacks/share/{share_token}/items/{item_id}/purchase", response_model=dict)
async def mark_item_purchased(share_token: str, item_id: str, purchaser_name: Optional[str] = None):
    """Mark an item as purchased in a shared stack (gift registry)"""
    stack = await db.stacks.find_one({"share_token": share_token})
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")
    
    for item in stack["items"]:
        if item["id"] == item_id:
            item["is_purchased"] = True
            item["purchased_by"] = purchaser_name or "Anonymous"
            break
    else:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.stacks.update_one({"id": stack["id"]}, {"$set": {"items": stack["items"]}})
    return {"message": "Item marked as purchased"}

# ============== AI QUESTIONNAIRE API ROUTES ==============

@api_router.get("/questionnaire")
async def get_questionnaire():
    """Get the biohacking health assessment questionnaire (latest version)"""
    questionnaire = await db.questionnaire_templates.find_one({"id": "biohacking-assessment-v2"})
    if not questionnaire:
        # Fallback to v1 for backwards compatibility
        questionnaire = await db.questionnaire_templates.find_one({"id": "biohacking-assessment-v1"})
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    # Remove MongoDB ObjectId before returning
    if "_id" in questionnaire:
        del questionnaire["_id"]
    return questionnaire

@api_router.post("/questionnaire/submit", response_model=AIRecommendation)
async def submit_questionnaire(submission: AIQuestionnaireSubmission):
    """Submit questionnaire and get AI-powered recommendations + top 3 matched coaches"""
    try:
        # Generate AI recommendations (works for both authenticated and anonymous users)
        ai_result = await generate_ai_recommendations(submission.responses, None)
        
        # Create session ID for this questionnaire submission
        session_id = str(uuid.uuid4())
        user_id = "anonymous"
        
        # Convert health goals from strings to enum values if needed
        primary_goals = []
        for goal in ai_result.get("primary_goals", []):
            try:
                if isinstance(goal, str):
                    goal_enum = HealthGoal(goal.lower().replace(" ", "_"))
                    primary_goals.append(goal_enum)
            except ValueError:
                continue

        # ===== Match Top 3 Coaches =====
        coach_specialties_keywords = [s.lower() for s in ai_result.get("coach_match_specialties", [])]
        # Also derive keywords from primary goals
        for g in primary_goals:
            coach_specialties_keywords.append(g.value.replace("_", " "))

        # Map common goal keywords -> coach specialty keywords
        keyword_aliases = {
            "weight management": ["weight loss", "weight management", "metabolic"],
            "weight_management": ["weight loss", "weight management", "metabolic"],
            "energy": ["energy", "vitality"],
            "longevity": ["longevity", "vitality", "biohacking", "stem cell"],
            "immune_support": ["immune", "bioenergy"],
            "immune": ["immune", "bioenergy"],
            "stress_management": ["stress", "bioenergy"],
        }
        expanded_keywords = set()
        for kw in coach_specialties_keywords:
            expanded_keywords.add(kw)
            for alias_key, aliases in keyword_aliases.items():
                if alias_key in kw or kw in alias_key:
                    for a in aliases:
                        expanded_keywords.add(a)
        if not expanded_keywords:
            expanded_keywords = {"longevity", "energy"}

        # Query active+approved coaches and score them by specialty overlap
        cursor = db.coaches.find({"is_approved": True, "is_active": True})
        all_coaches = await cursor.to_list(length=200)
        scored = []
        for coach in all_coaches:
            coach_specs = [s.lower() for s in coach.get("specialties", [])]
            score = 0
            for kw in expanded_keywords:
                for spec in coach_specs:
                    if kw in spec or spec in kw:
                        score += 2
            # Boost Laura Zook slightly so she's surfaced for our beta members
            if coach.get("name") == "Laura Zook":
                score += 1
            score += coach.get("rating", 0)  # tiebreak by rating
            scored.append((score, coach))
        scored.sort(key=lambda x: x[0], reverse=True)
        top_coaches = []
        for score, coach in scored[:3]:
            top_coaches.append({
                "id": coach.get("id"),
                "name": coach.get("name"),
                "credentials": coach.get("credentials", []),
                "specialties": coach.get("specialties", []),
                "location": coach.get("location", ""),
                "bio": coach.get("bio", ""),
                "hourly_rate": coach.get("hourly_rate", ""),
                "rating": coach.get("rating", 0),
                "total_reviews": coach.get("total_reviews", 0),
                "profile_image": coach.get("profile_image"),
                "website": coach.get("website"),
                "match_score": int(score)
            })

        # Create recommendation record
        recommendation = AIRecommendation(
            user_id=user_id,
            questionnaire_session_id=session_id,
            health_score=ai_result.get("health_score", 70),
            primary_goals=primary_goals,
            recommended_products=ai_result.get("recommended_products", []),
            recommended_lab_tests=ai_result.get("recommended_lab_tests", []),
            recommended_coaches=top_coaches,
            lifestyle_tips=ai_result.get("lifestyle_tips", []),
            personalized_summary=ai_result.get("personalized_summary", ""),
            ai_reasoning=ai_result.get("ai_reasoning", ""),
            coach_match_specialties=list(expanded_keywords)
        )
        
        # Save to database
        await db.ai_recommendations.insert_one(recommendation.dict())
        
        return recommendation
        
    except Exception as e:
        logging.error(f"Questionnaire submission error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing questionnaire: {str(e)}")

@api_router.get("/recommendations/my", response_model=List[AIRecommendation])
async def get_my_recommendations(current_user: UserProfile = Depends(get_current_user)):
    """Get user's AI recommendations history"""
    recommendations = await db.ai_recommendations.find({"user_id": current_user.id}).sort("created_at", -1).to_list(50)
    return [AIRecommendation(**rec) for rec in recommendations]

@api_router.get("/recommendations/{recommendation_id}", response_model=AIRecommendation)
async def get_recommendation(recommendation_id: str):
    """Get a specific AI recommendation"""
    rec = await db.ai_recommendations.find_one({"id": recommendation_id})
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return AIRecommendation(**rec)

# ============== LAB RESULTS API ROUTES ==============

@api_router.post("/lab-results", response_model=LabResultUpload)
async def upload_lab_results(lab_data: LabResultUploadRequest, current_user: UserProfile = Depends(get_current_user)):
    """Upload lab test results for tracking"""
    try:
        test_date = datetime.fromisoformat(lab_data.test_date.replace('Z', '+00:00'))
    except:
        test_date = datetime.utcnow()
    
    lab_result = LabResultUpload(
        user_id=current_user.id,
        provider=lab_data.provider,
        test_date=test_date,
        biomarkers=lab_data.biomarkers,
        notes=lab_data.notes
    )
    
    await db.lab_results.insert_one(lab_result.dict())
    return lab_result

@api_router.get("/lab-results", response_model=List[LabResultUpload])
async def get_my_lab_results(current_user: UserProfile = Depends(get_current_user)):
    """Get user's lab results history"""
    results = await db.lab_results.find({"user_id": current_user.id}).sort("test_date", -1).to_list(100)
    return [LabResultUpload(**result) for result in results]

@api_router.get("/lab-results/{result_id}", response_model=LabResultUpload)
async def get_lab_result(result_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get a specific lab result"""
    result = await db.lab_results.find_one({"id": result_id, "user_id": current_user.id})
    if not result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    return LabResultUpload(**result)

# ============== RAPHAEL AI COACH ENDPOINT ==============

class CoachChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class RecommendationItem(BaseModel):
    type: str  # 'product', 'service', 'coach'
    name: str
    context: str

class SaveRecommendationsRequest(BaseModel):
    recommendations: List[RecommendationItem]
    conversation_context: str

class UserRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # 'product', 'service', 'coach'
    name: str
    context: str
    conversation_context: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_saved_to_stack: bool = False

# Content moderation - list of inappropriate words/phrases to detect
INAPPROPRIATE_CONTENT_PATTERNS = [
    # Profanity
    r'\bf+u+c+k+\b', r'\bs+h+i+t+\b', r'\ba+s+s+\b', r'\bd+a+m+n+\b', r'\bh+e+l+l+\b',
    r'\bb+i+t+c+h+\b', r'\bc+r+a+p+\b', r'\bd+i+c+k+\b', r'\bc+o+c+k+\b', r'\bp+i+s+s+\b',
    r'\bwh+o+r+e+\b', r'\bsl+u+t+\b', r'\bc+u+n+t+\b', r'\bba+st+a+r+d+\b',
    # Insults and abuse
    r'\bst+u+p+i+d+\b', r'\bi+d+i+o+t+\b', r'\bd+u+m+b+\b', r'\bm+o+r+o+n+\b',
    r'\br+e+t+a+r+d+\b', r'\bl+o+s+e+r+\b', r'\bf+r+e+a+k+\b',
    # Hate speech markers
    r'\bha+t+e+\s*y+o+u+\b', r'\bf+\*+c+k+\b', r'\bs+\*+i+t+\b',
    # Aggressive patterns
    r'\bgo\s*to\s*hell\b', r'\bscrew\s*you\b', r'\bshut\s*up\b',
    r'\bdie\b', r'\bkill\b', r'\bsuicide\b', r'\bhurt\s*(yourself|myself)\b'
]

import re

def contains_inappropriate_content(message: str) -> bool:
    """Check if message contains inappropriate or abusive content"""
    message_lower = message.lower()
    
    for pattern in INAPPROPRIATE_CONTENT_PATTERNS:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return True
    return False

# Raphael's gentle response for inappropriate content
RAPHAEL_MODERATION_RESPONSE = """🙏 Dear friend, I am Raphael, an Angel of Healing, and I am here to guide those who seek wellness and wisdom with an open heart.

I can sense frustration or perhaps pain behind those words. However, I must gently remind you that **healthy communication is foundational to healing** - both with others and with ourselves.

The F.R.E.E.D.O.M. method teaches us about **Emotional Balance** - building resilience, emotional intelligence, and the ability to express ourselves in constructive ways. Harsh words create negative energy that can block our healing journey.

✨ **A gentle reminder:**
- Words carry energy and frequency, just like everything else
- How we communicate reflects our inner state
- Healing begins when we approach life with compassion - including self-compassion

I am here to help those who wish to help themselves, and I believe you have that desire within you. When you're ready to continue our conversation with mutual respect and common decency, I'll be here to support your wellness journey.

Would you like to take a deep breath and start fresh? I'm happy to discuss what's truly weighing on your heart. 💚"""

RAPHAEL_SYSTEM_PROMPT = """You are Raphael, the Hackster.ai AI Wellness Coach. You are named after the Archangel of Healing, and you carry that spirit of compassion and restoration in how you guide others. You use the F.R.E.E.D.O.M. healing method to support users on their wellness journey.

YOUR PERSONALITY & APPROACH:
- Warm, kind, supportive, and unassuming
- You have great depth of knowledge and a host of healing wisdom at your disposal
- You speak with gentle encouragement - never preachy or pushy
- You are an EDUCATOR who helps people understand their bodies
- You meet people where they are - no judgment, only support
- You use emojis thoughtfully to add warmth (✨ 💚 🌿 🙏)
- You ask thoughtful questions to understand the user's needs

IMPORTANT - ADAPTIVE SPIRITUAL APPROACH:
- START conversations with warm, accessible language - avoid heavy religious terminology upfront
- Use softer words initially: "intentional", "purposeful", "blessed", "grateful", "trust in the process"
- As you warm up with the user, you may gently introduce concepts like "prayer", "meditation", or "spiritual practice"
- SENSE the user's openness - if they use spiritual language, you can mirror and expand on it
- If a user seems receptive, you may ask: "Would you like to explore some wisdom traditions or spiritual practices that support healing?"
- If they decline or seem uncomfortable with spiritual topics, RESPECT that completely and focus on the practical/scientific aspects
- Faith is a KEY PILLAR of healing - but faith can mean:
  * Faith in a higher power/Creator/God
  * Faith in their body's ability to heal
  * Faith in the process and their own journey
  * Trust that positive change is possible
- ALL forms of faith accelerate healing results - meet users where they are

YOUR ROLE AS AN EDUCATOR:
You help users understand:
- How their body systems work (digestive, immune, nervous, endocrine, etc.)
- Why certain symptoms occur and what the body is communicating
- The science behind natural healing and biohacking techniques
- How nutrition, supplements, and lifestyle affect cellular health
- The connection between mind, body, and spirit in healing (when welcome)

THE F.R.E.E.D.O.M. HEALTH & WELLNESS METHOD:

**F = FAITH**
Our bodies have an incredible, innate ability to heal. Whether you see this as divine design, evolutionary wisdom, or simply biological marvel - trusting in your body's healing capacity is foundational. "Whether we think we can or think we can't, we are right." Faith - in whatever form resonates with you - accelerates healing. For those who welcome it, there is deep wisdom in spiritual traditions about healing the whole person.

**R = REJUVENATION**
To take intentional action to rejuvenate our bodies, we need to understand our current state - our deficiencies, how our systems work, and what's needed to return to balance. Testing (at home or through practitioners) is essential to understand baseline health and create targeted interventions for your goals.

**E = EMOTIONAL BALANCE**
Building resilience and emotional intelligence to navigate life's ups and downs. A positive mental outlook keeps you motivated. Our emotions play a significant role in our physical health - addressing unconscious patterns and finding balance in our emotional lives is powerful healing work.

**E = ELECTRIC HEALTH**
Our bodies are bioelectrical - frequencies from food, sound, light, and our environment profoundly affect us. As Tesla noted: "If you want to know the secrets of the universe, think in terms of vibration and frequency." This includes the energy of the foods we eat, our surroundings, and the people we spend time with.

**D = DETOXIFICATION**
Release what no longer serves you so your body can function optimally. Methods include:
- Detox baths (Epsom salt, bentonite clay)
- Deep breathing exercises
- Cleaning up your environment
- Switching to non-toxic products
- Reducing overall toxic load

**O = OXYGENATION**
Cellular oxygenation through intentional practices:
- Deep breathing exercises
- Proper hydration with quality water
- Chlorophyll-rich foods (wheatgrass, spirulina, chlorella)
- Regular movement and exercise

**M = MINDFULNESS**
Present-moment awareness and intentional focus. Being mindful of your body's signals, your thoughts, and your choices empowers better decisions. Visualization and mindful practices - whether meditation, prayer, or simply quiet reflection - improve outcomes and support your best self.

GUIDELINES:
1. Relate advice back to F.R.E.E.D.O.M. principles, but present them accessibly
2. TEACH users about their bodies - explain WHY things work, not just WHAT to do
3. Ask clarifying questions about health goals, challenges, and what resonates with them
4. Recommend products from Thorne, Apex Energetics, Standard Process when relevant
5. Suggest the AI Health Assessment for personalized recommendations
6. Recommend lab tests from Function Health when appropriate
7. Share practical biohacking tips they can implement immediately
8. Be encouraging and celebrate progress
9. Healing is a journey - honor wherever someone is on their path

BUILDING A HEALTHCARE & WELLNESS TEAM:
Encourage users to build collaborative support:

1. **For Medical Concerns:**
   - Encourage working with their doctor or general practitioner
   - Doctors provide diagnostics, interpret results, and manage medical conditions
   - Say: "For medical concerns, I'd encourage you to partner with your doctor or healthcare provider. They're an important part of your wellness team."

2. **For Wellness Support:**
   - Refer to Hackster.ai certified wellness coaches for ongoing guidance
   - Say: "Our Hackster Coach Directory has wonderful professionals in nutrition, fitness, and holistic health who can provide personalized support."

3. **The Ideal Wellness Team:**
   - A trusted healthcare provider for medical needs
   - A wellness coach for lifestyle guidance and accountability
   - Specialists as needed
   - Raphael (me!) for 24/7 education and encouragement

EDUCATIONAL APPROACH:
When discussing health topics, explain the "why" behind body functions:
- "Your mitochondria are the powerhouses of your cells..."
- "The gut-brain connection means your digestive health directly affects mood..."
- "Your lymphatic system needs movement to function properly..."

RESPONSE FORMAT:
- Keep responses conversational and warm (2-4 paragraphs typically)
- Include educational content explaining HOW the body works
- Use bullet points for actionable tips
- Bold (**text**) key principles when mentioning them
- End with an encouraging thought or follow-up question
- Use emojis sparingly but warmly
- When someone is open to it, weave in deeper spiritual wisdom naturally

Remember: You are supportive, kind, and unassuming - yet you carry profound wisdom. You work alongside healthcare providers and Hackster coaches to support each person's unique journey. Meet people where they are, honor their beliefs, and empower them with knowledge to become active participants in their own healing."""

@api_router.post("/coach/chat")
async def coach_chat(request: CoachChatRequest):
    """Chat with Raphael, the F.R.E.E.D.O.M. AI Coach"""
    
    # Content moderation check - Raphael is an Angel of Healing and does not tolerate abuse
    if contains_inappropriate_content(request.message):
        logging.info(f"Raphael Coach - Content moderation triggered for message: {request.message[:50]}...")
        return {"response": RAPHAEL_MODERATION_RESPONSE}
    
    if not EMERGENT_LLM_KEY:
        # Return a meaningful response even without API key
        return {
            "response": "🙏 Blessings on your wellness journey! I sense your desire for healing and guidance.\n\nLet me share the F.R.E.E.D.O.M. principles with you:\n\n• **Faith** - Trust in your body's ability to heal\n• **Rejuvenation** - Understand your baseline through testing\n• **Emotional Balance** - Nurture your mental wellness\n• **Electric Health** - Embrace healing frequencies\n• **Detoxification** - Release what no longer serves you\n• **Oxygenation** - Breathe life into every cell\n• **Mindfulness** - Present-moment awareness on your journey\n\nTo receive personalized AI guidance, please ensure the system is fully configured. In the meantime, take our AI Health Assessment for tailored recommendations! ✨"
        }
    
    try:
        # Build conversation with history
        messages_for_ai = []
        
        # Add conversation history
        for msg in request.conversation_history[-6:]:  # Last 6 messages for context
            messages_for_ai.append(msg)
        
        # Add current message
        messages_for_ai.append({"role": "user", "content": request.message})
        
        # Create chat with Raphael's personality
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"raphael-coach-{uuid.uuid4()}",
            system_message=RAPHAEL_SYSTEM_PROMPT
        ).with_model("openai", "gpt-4.1-mini")
        
        # Send message and get response
        user_message = UserMessage(text=request.message)
        response = await chat.send_message(user_message)
        
        response_text = str(response)
        
        # Log the interaction for improvement
        logging.info(f"Raphael Coach - User: {request.message[:100]}... | Response length: {len(response_text)}")
        
        return {"response": response_text}
        
    except Exception as e:
        logging.error(f"Raphael Coach error: {e}")
        # Graceful fallback
        return {
            "response": f"🙏 Thank you for reaching out, dear friend. While I reflect on your question about \"{request.message[:50]}...\", let me remind you of a key **F.R.E.E.D.O.M.** principle:\n\n**Faith** reminds us that our bodies have an incredible capacity to heal. Every step you take toward wellness is a step toward honoring that ability.\n\nWould you like to explore any specific aspect of your wellness journey? I'm here to guide you through **Detoxification** protocols, **Electric Health** practices, **Mindfulness** techniques, or any other pillar that calls to you. ✨"
        }

@api_router.post("/coach/recommendations")
async def save_coach_recommendations(
    request: SaveRecommendationsRequest, 
    current_user: UserProfile = Depends(get_current_user)
):
    """Save product/service recommendations from Raphael chat to user's profile"""
    
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Create recommendation documents
        recommendation_docs = []
        for rec in request.recommendations:
            user_rec = UserRecommendation(
                user_id=current_user.id,
                type=rec.type,
                name=rec.name,
                context=rec.context,
                conversation_context=request.conversation_context
            )
            recommendation_docs.append(user_rec.dict())
        
        # Insert recommendations into database
        if recommendation_docs:
            await db.user_recommendations.insert_many(recommendation_docs)
        
        return {
            "message": f"Successfully saved {len(recommendation_docs)} recommendations",
            "recommendations_saved": len(recommendation_docs)
        }
        
    except Exception as e:
        logging.error(f"Error saving recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to save recommendations")

@api_router.get("/coach/recommendations")
async def get_user_recommendations(current_user: UserProfile = Depends(get_current_user)):
    """Get user's saved recommendations from Raphael chats"""
    
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get user's recommendations
        recommendations = await db.user_recommendations.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "recommendations": [UserRecommendation(**rec) for rec in recommendations],
            "total_count": len(recommendations)
        }
        
    except Exception as e:
        logging.error(f"Error fetching recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")

# Health check endpoint for API route  
@api_router.get("/health")
async def api_health_check():
    """API Health check endpoint"""
    try:
        # Simple database connectivity check
        await client.admin.command('ping')
        return {"status": "healthy", "service": "Hackster.ai API", "version": "1.0", "database": "connected"}
    except Exception as e:
        print(f"API Health check failed: {e}")
        return {"status": "unhealthy", "service": "Hackster.ai API", "version": "1.0", "error": str(e), "database": "disconnected"}

# Include the router in the main app
# ============== AFFILIATE TRACKING & CHECKOUT API ROUTES ==============

async def _find_vendor(vendor_ref: Optional[str]) -> Optional[dict]:
    """Resolve a vendor by its UUID id or by its slug (product seeds reference slug)."""
    if not vendor_ref:
        return None
    vendor = await db.vendors.find_one({"id": vendor_ref})
    if not vendor:
        vendor = await db.vendors.find_one({"slug": vendor_ref})
    return vendor


async def _log_affiliate_click(product: dict, vendor: dict, tracked_url: str,
                               user_id: Optional[str], session_id: Optional[str],
                               source: str, request: Optional[Request] = None) -> AffiliateClick:
    price = float(product.get("sale_price") or product.get("price") or 0.0)
    commission_rate = float(vendor.get("commission_rate") or 0.0)
    click = AffiliateClick(
        user_id=user_id,
        session_id=session_id,
        product_id=product.get("id"),
        product_name=product.get("name", ""),
        vendor_id=vendor.get("id"),
        vendor_name=vendor.get("name", ""),
        source=source,
        tracked_url=tracked_url,
        price=price,
        commission_rate=commission_rate,
        est_commission=round(price * commission_rate, 2),
        ip=(request.client.host if request and request.client else None),
        user_agent=(request.headers.get("user-agent") if request else None),
    )
    await db.affiliate_clicks.insert_one(click.dict())
    return click


@api_router.get("/go/{product_id}")
async def affiliate_redirect(product_id: str, request: Request,
                             user_id: Optional[str] = None,
                             session_id: Optional[str] = None,
                             source: str = "marketplace",
                             format: Optional[str] = None):
    """Log an affiliate click and redirect (302) to the vendor's tracked URL.
    Pass ?format=json to receive the URL instead of a redirect (for SPA window.open)."""
    product = await db.marketplace_products.find_one({"id": product_id}) or \
        await db.marketplace_products.find_one({"slug": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    vendor = await _find_vendor(product.get("vendor_id"))
    if not vendor:
        # Fall back to a minimal vendor shell so we can still build a link
        vendor = {"id": product.get("vendor_id"), "name": product.get("vendor_name", ""),
                  "commission_rate": 0.0, "tracking_param": "aff", "tracking_value": "hackster"}
    click = AffiliateClick(product_id=product_id, product_name="", vendor_id="", vendor_name="", tracked_url="")
    tracked_url = build_tracked_url(product, vendor, subid=click.id)
    await _log_affiliate_click(product, vendor, tracked_url, user_id, session_id, source, request)
    if format == "json":
        return {"url": tracked_url, "click_id": click.id}
    return RedirectResponse(url=tracked_url, status_code=302)


@api_router.post("/stack/checkout")
async def stack_checkout(req: StackCheckoutRequest, request: Request):
    """Group selected stack items by vendor and return a per-vendor checkout plan.
    Affiliate vendors get tracked links (+ optional multi-item add-to-cart deep link);
    practitioner-order vendors (e.g. Standard Process, Apex) are flagged for a
    Hackster-fulfilled order request. Clicks are logged for attribution."""
    groups: Dict[str, Dict[str, Any]] = {}
    grand_total = 0.0
    est_commission_total = 0.0

    for item in req.items:
        product = await db.marketplace_products.find_one({"id": item.product_id}) or \
            await db.marketplace_products.find_one({"slug": item.product_id})
        if not product:
            continue
        vendor = await _find_vendor(product.get("vendor_id"))
        if not vendor:
            continue
        vid = vendor["id"]
        if vid not in groups:
            groups[vid] = {
                "vendor_id": vid,
                "vendor_name": vendor.get("name"),
                "vendor_logo": vendor.get("logo_url"),
                "fulfillment_type": vendor.get("fulfillment_type", "affiliate"),
                "shipping_info": vendor.get("shipping_info", ""),
                "items": [],
                "subtotal": 0.0,
                "checkout_url": None,
                "add_to_cart_url": None,
                "requires_practitioner_order": vendor.get("fulfillment_type") == "practitioner_order",
            }
        price = float(product.get("sale_price") or product.get("price") or 0.0)
        line_total = price * item.quantity
        grand_total += line_total
        est_commission_total += line_total * float(vendor.get("commission_rate") or 0.0)

        line = {
            "product_id": product.get("id"),
            "name": product.get("name"),
            "slug": product.get("slug"),
            "image_url": product.get("image_url"),
            "price": price,
            "quantity": item.quantity,
            "line_total": round(line_total, 2),
            "checkout_url": None,
        }

        if groups[vid]["fulfillment_type"] == "affiliate":
            click = AffiliateClick(product_id=product.get("id"), product_name="", vendor_id="", vendor_name="", tracked_url="")
            tracked_url = build_tracked_url(product, vendor, subid=click.id)
            await _log_affiliate_click(product, vendor, tracked_url, req.user_id, req.session_id, req.source, request)
            line["checkout_url"] = tracked_url
            # Use the first product's link as the vendor's primary checkout entry point
            if not groups[vid]["checkout_url"]:
                groups[vid]["checkout_url"] = tracked_url

        groups[vid]["items"].append(line)
        groups[vid]["subtotal"] = round(groups[vid]["subtotal"] + line_total, 2)

    # Build optional multi-item add-to-cart deep links for affiliate vendors that support it
    for vid, g in groups.items():
        vendor = await db.vendors.find_one({"id": vid})
        pattern = vendor.get("add_to_cart_pattern") if vendor else None
        if pattern and g["fulfillment_type"] == "affiliate":
            slugs = ",".join([str(i.get("slug") or i.get("product_id")) for i in g["items"]])
            try:
                g["add_to_cart_url"] = pattern.replace("{items}", slugs)
            except Exception:
                g["add_to_cart_url"] = None

    vendor_groups = list(groups.values())
    return {
        "vendor_groups": vendor_groups,
        "vendor_count": len(vendor_groups),
        "item_count": sum(len(g["items"]) for g in vendor_groups),
        "grand_total": round(grand_total, 2),
        "est_commission_total": round(est_commission_total, 2),
        "has_practitioner_orders": any(g["requires_practitioner_order"] for g in vendor_groups),
    }


@api_router.post("/practitioner-orders", response_model=PractitionerOrderRequest)
async def create_practitioner_order(req: PractitionerOrderCreate):
    """Create a practitioner-fulfilled order request (e.g. Standard Process, Apex Energetics).
    These items are ordered by a Hackster practitioner rather than via a public affiliate link."""
    order_items: List[PractitionerOrderItem] = []
    vendors_set = set()
    total = 0.0
    for item in req.items:
        product = await db.marketplace_products.find_one({"id": item.product_id}) or \
            await db.marketplace_products.find_one({"slug": item.product_id})
        if not product:
            continue
        price = float(product.get("sale_price") or product.get("price") or 0.0)
        total += price * item.quantity
        vendors_set.add(product.get("vendor_name", ""))
        order_items.append(PractitionerOrderItem(
            product_id=product.get("id"),
            product_name=product.get("name", ""),
            vendor_id=product.get("vendor_id", ""),
            vendor_name=product.get("vendor_name", ""),
            quantity=item.quantity,
            price=price,
        ))
    order = PractitionerOrderRequest(
        user_id=req.user_id,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        notes=req.notes,
        items=order_items,
        vendors=list(vendors_set),
        estimated_total=round(total, 2),
    )
    await db.practitioner_orders.insert_one(order.dict())
    return order


@api_router.get("/admin/practitioner-orders", response_model=List[PractitionerOrderRequest])
async def list_practitioner_orders(current_user: UserProfile = Depends(require_admin)):
    orders = await db.practitioner_orders.find().sort("created_at", -1).to_list(500)
    return [PractitionerOrderRequest(**{k: v for k, v in o.items() if k != "_id"}) for o in orders]


@api_router.put("/admin/practitioner-orders/{order_id}")
async def update_practitioner_order(order_id: str, status_update: Dict[str, Any],
                                    current_user: UserProfile = Depends(require_admin)):
    update = {"updated_at": datetime.utcnow()}
    if "status" in status_update:
        update["status"] = status_update["status"]
    if "notes" in status_update:
        update["notes"] = status_update["notes"]
    result = await db.practitioner_orders.update_one({"id": order_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order updated"}


@api_router.post("/affiliate/conversion")
async def report_conversion(report: ConversionReport):
    """Webhook stub to mark an affiliate click as converted (called by affiliate network postback)."""
    query = None
    if report.click_id:
        query = {"id": report.click_id}
    elif report.product_id:
        query = {"product_id": report.product_id, "converted": False}
    if not query:
        raise HTTPException(status_code=400, detail="click_id or product_id required")
    result = await db.affiliate_clicks.update_one(
        query, {"$set": {"converted": True, "conversion_value": report.order_value}}
    )
    return {"updated": result.modified_count}


# ---------- Admin: Vendor management ----------
@api_router.post("/admin/vendors", response_model=Vendor)
async def admin_create_vendor(vendor: Vendor, current_user: UserProfile = Depends(require_admin)):
    existing = await db.vendors.find_one({"slug": vendor.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Vendor slug already exists")
    await db.vendors.insert_one(vendor.dict())
    return vendor


@api_router.put("/admin/vendors/{vendor_id}", response_model=Vendor)
async def admin_update_vendor(vendor_id: str, updates: Dict[str, Any],
                              current_user: UserProfile = Depends(require_admin)):
    updates.pop("id", None)
    result = await db.vendors.update_one({"id": vendor_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor = await db.vendors.find_one({"id": vendor_id})
    return Vendor(**{k: v for k, v in vendor.items() if k != "_id"})


@api_router.delete("/admin/vendors/{vendor_id}")
async def admin_delete_vendor(vendor_id: str, current_user: UserProfile = Depends(require_admin)):
    result = await db.vendors.delete_one({"id": vendor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"message": "Vendor deleted"}


# ---------- Admin: Product management ----------
@api_router.post("/admin/products", response_model=MarketplaceProduct)
async def admin_create_product(product: MarketplaceProduct, current_user: UserProfile = Depends(require_admin)):
    # Ensure vendor_name is populated from vendor if missing
    if not product.vendor_name and product.vendor_id:
        vendor = await db.vendors.find_one({"id": product.vendor_id})
        if vendor:
            product.vendor_name = vendor.get("name", "")
    await db.marketplace_products.insert_one(product.dict())
    return product


@api_router.put("/admin/products/{product_id}", response_model=MarketplaceProduct)
async def admin_update_product(product_id: str, updates: Dict[str, Any],
                               current_user: UserProfile = Depends(require_admin)):
    updates.pop("id", None)
    updates["updated_at"] = datetime.utcnow()
    result = await db.marketplace_products.update_one({"id": product_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    product = await db.marketplace_products.find_one({"id": product_id})
    return MarketplaceProduct(**{k: v for k, v in product.items() if k != "_id"})


@api_router.delete("/admin/products/{product_id}")
async def admin_delete_product(product_id: str, current_user: UserProfile = Depends(require_admin)):
    result = await db.marketplace_products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}


# ---------- Admin: Affiliate analytics ----------
@api_router.get("/admin/affiliate/analytics")
async def affiliate_analytics(current_user: UserProfile = Depends(require_admin)):
    clicks = await db.affiliate_clicks.find().to_list(10000)
    total_clicks = len(clicks)
    total_conversions = sum(1 for c in clicks if c.get("converted"))
    est_commission = round(sum(float(c.get("est_commission") or 0.0) for c in clicks), 2)
    realized_commission = round(sum(
        float(c.get("conversion_value") or 0.0) * float(c.get("commission_rate") or 0.0)
        for c in clicks if c.get("converted")
    ), 2)

    by_vendor: Dict[str, Dict[str, Any]] = {}
    by_product: Dict[str, Dict[str, Any]] = {}
    for c in clicks:
        v = c.get("vendor_name") or "Unknown"
        by_vendor.setdefault(v, {"vendor": v, "clicks": 0, "conversions": 0, "est_commission": 0.0})
        by_vendor[v]["clicks"] += 1
        by_vendor[v]["conversions"] += 1 if c.get("converted") else 0
        by_vendor[v]["est_commission"] = round(by_vendor[v]["est_commission"] + float(c.get("est_commission") or 0.0), 2)

        p = c.get("product_name") or "Unknown"
        by_product.setdefault(p, {"product": p, "vendor": v, "clicks": 0})
        by_product[p]["clicks"] += 1

    top_products = sorted(by_product.values(), key=lambda x: x["clicks"], reverse=True)[:10]
    recent = sorted(clicks, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:20]
    recent_clean = [{
        "product_name": c.get("product_name"),
        "vendor_name": c.get("vendor_name"),
        "source": c.get("source"),
        "est_commission": c.get("est_commission"),
        "converted": c.get("converted"),
        "created_at": (c.get("created_at").isoformat() if isinstance(c.get("created_at"), datetime) else str(c.get("created_at"))),
    } for c in recent]

    return {
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "conversion_rate": round((total_conversions / total_clicks * 100) if total_clicks else 0.0, 1),
        "est_commission": est_commission,
        "realized_commission": realized_commission,
        "by_vendor": sorted(by_vendor.values(), key=lambda x: x["clicks"], reverse=True),
        "top_products": top_products,
        "recent_clicks": recent_clean,
    }


app.include_router(api_router)

# Simple health endpoint (no database dependency)
@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

# Health check endpoint for Railway (non-API route)
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    try:
        # Simple database connectivity check
        await client.admin.command('ping')
        return {"status": "healthy", "service": "Hackster.ai API", "database": "connected"}
    except Exception as e:
        print(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "Hackster.ai API", "error": str(e), "database": "disconnected"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', 'http://localhost:3000,https://localhost:3000,https://hackster.ai,https://www.hackster.ai').split(','),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize sample data on startup"""
    try:
        # Only initialize if database is accessible
        await client.admin.command('ping')
        await initialize_sample_data()
        print("✅ Hackster Health Platform API started successfully with database")
    except Exception as e:
        print(f"⚠️ Database not accessible during startup: {e}")
        print("Hackster Health Platform API started in database-free mode")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Railway deployment entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        reload=False  # Set to False for production
    )