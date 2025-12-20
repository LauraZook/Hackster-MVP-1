from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    lifestyle_tips: List[str]
    personalized_summary: str
    ai_reasoning: str  # Detailed AI analysis
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

# ============== AI RECOMMENDATION ENGINE ==============
async def generate_ai_recommendations(user_responses: List[QuestionnaireResponse], user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
    """Generate personalized product recommendations using GPT"""
    
    if not EMERGENT_LLM_KEY:
        # Return mock recommendations if no API key
        return {
            "health_score": 75,
            "primary_goals": ["energy", "sleep"],
            "recommended_products": [
                {"product_id": "vitamin_d3_k2", "name": "Vitamin D3 + K2", "reason": "Essential for immune and bone health", "priority": 1},
                {"product_id": "magnesium", "name": "Magnesium Bisglycinate", "reason": "Supports sleep and recovery", "priority": 2}
            ],
            "recommended_lab_tests": [
                {"test_id": "comprehensive_panel", "name": "Comprehensive Metabolic Panel", "reason": "Establish baseline health metrics"}
            ],
            "lifestyle_tips": [
                "Get 10-30 minutes of morning sunlight",
                "Practice box breathing for stress management",
                "End showers with 30-60 seconds of cold water"
            ],
            "personalized_summary": "Based on your responses, we recommend focusing on foundational health with Vitamin D3+K2 and Magnesium.",
            "ai_reasoning": "Mock response - API key not configured"
        }
    
    # Format responses for AI
    responses_text = "\n".join([f"Q: {r.question_id} - A: {r.answer}" for r in user_responses])
    
    user_context = ""
    if user_profile:
        user_context = f"\nUser Info: Age: {user_profile.age or 'Unknown'}, Gender: {user_profile.gender or 'Unknown'}, Goals: {', '.join(user_profile.goals)}"
    
    system_prompt = """You are an expert biohacking and health optimization AI assistant for Hackster.ai. 
    Your role is to analyze user health questionnaire responses and provide personalized supplement, 
    product, and lifestyle recommendations.
    
    You have deep knowledge of:
    - Supplements (Thorne, Apex Energetics, Standard Process brands)
    - Biohacking protocols (cold exposure, breathwork, light therapy)
    - Lab testing (Function Health, Superpower, Thorne tests)
    - Health optimization strategies
    
    IMPORTANT: Always respond with valid JSON in this exact format:
    {
        "health_score": <number 0-100>,
        "primary_goals": ["goal1", "goal2"],
        "recommended_products": [
            {"product_id": "id", "name": "Product Name", "brand": "Brand", "reason": "Why recommended", "priority": 1}
        ],
        "recommended_lab_tests": [
            {"test_id": "id", "name": "Test Name", "provider": "provider", "reason": "Why needed"}
        ],
        "lifestyle_tips": ["tip1", "tip2", "tip3"],
        "personalized_summary": "2-3 sentence summary of recommendations",
        "ai_reasoning": "Detailed analysis of user's responses and why these recommendations were made"
    }
    
    Base your recommendations on evidence-based health science and biohacking best practices."""
    
    user_prompt = f"""Please analyze the following health questionnaire responses and provide personalized recommendations:
    
    {responses_text}
    {user_context}
    
    Consider the user's health goals, current lifestyle, and any concerns mentioned. 
    Provide specific product recommendations from Thorne, Apex Energetics, or Standard Process brands.
    Include relevant lab tests they should consider.
    Suggest practical biohacking tips they can implement immediately."""
    
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
            "primary_goals": ["energy", "sleep"],
            "recommended_products": [
                {"product_id": "vitamin_d3_k2", "name": "Vitamin D3 + K2", "brand": "Thorne", "reason": "Essential for most people, supports immune function and bone health", "priority": 1},
                {"product_id": "magnesium", "name": "Magnesium Bisglycinate", "brand": "Thorne", "reason": "Supports sleep, recovery, and over 300 enzymatic processes", "priority": 2},
                {"product_id": "omega3", "name": "Super EPA", "brand": "Thorne", "reason": "Supports brain health and reduces inflammation", "priority": 3}
            ],
            "recommended_lab_tests": [
                {"test_id": "comprehensive_panel", "name": "Comprehensive Metabolic Panel", "provider": "function_health", "reason": "Establish baseline health metrics"}
            ],
            "lifestyle_tips": [
                "Get 10-30 minutes of morning sunlight within 1 hour of waking",
                "Practice 5 minutes of box breathing daily for stress management",
                "End showers with 30-60 seconds of cold water to boost energy"
            ],
            "personalized_summary": "We recommend starting with foundational supplements (Vitamin D3+K2 and Magnesium) and establishing your baseline through comprehensive lab testing.",
            "ai_reasoning": f"Error generating AI response: {str(e)}. Providing default evidence-based recommendations."
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
    
    # Sample Coaches
    coaches = [
        {
            "name": "Dr. Sarah Martinez",
            "credentials": ["PhD Nutrition Science", "Certified Functional Medicine Practitioner"],
            "specialties": ["Hormone Optimization", "Gut Health", "Weight Management"],
            "location": "Los Angeles, CA",
            "bio": "15+ years helping clients optimize health through personalized nutrition and lifestyle interventions.",
            "hourly_rate": "$150-200",
            "availability": "Mon-Fri 9AM-6PM PST",
            "contact_info": {"email": "sarah@hackstercoach.com", "phone": "(555) 123-4567"},
            "rating": 4.9,
            "total_reviews": 127,
            "years_experience": 15,
            "is_approved": True,
            "is_active": True,
            "website": "https://sarahmartinez-wellness.com"
        },
        {
            "name": "Mike Chen",
            "credentials": ["NASM-CPT", "Precision Nutrition Level 2", "Wim Hof Method Instructor"],
            "specialties": ["Athletic Performance", "Cold Therapy", "Breathwork"],
            "location": "Austin, TX",
            "bio": "Former professional athlete turned biohacking coach specializing in performance optimization.",
            "hourly_rate": "$100-150",
            "availability": "Tue-Sat 6AM-8PM CST",
            "contact_info": {"email": "mike@hackstercoach.com", "phone": "(555) 987-6543"},
            "rating": 4.8,
            "total_reviews": 89,
            "years_experience": 8,
            "is_approved": True,
            "is_active": True,
            "website": "https://mikechen-performance.com"
        },
        {
            "name": "Dr. Lisa Thompson",
            "credentials": ["MD", "Functional Medicine Certified", "Biohacking Institute Graduate"],
            "specialties": ["Longevity", "Biohacking", "Sleep Optimization", "Stress Management"],
            "location": "New York, NY",
            "bio": "Medical doctor specializing in longevity and biohacking protocols. Helping clients optimize their healthspan through cutting-edge interventions.",
            "hourly_rate": "$200-300",
            "availability": "Mon-Thu 10AM-4PM EST",
            "contact_info": {"email": "lisa@longevityhub.com", "phone": "(555) 234-5678"},
            "rating": 4.95,
            "total_reviews": 203,
            "years_experience": 12,
            "is_approved": True,
            "is_active": True,
            "website": "https://longevityhub.com"
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
    # Sample Vendors
    if await db.vendors.count_documents({}) == 0:
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
            }
        ]
        
        for vendor_data in sample_vendors:
            vendor = Vendor(**vendor_data)
            await db.vendors.insert_one(vendor.dict())
    
    # Sample Marketplace Products
    if await db.marketplace_products.count_documents({}) == 0:
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
            }
        ]
        
        for product_data in sample_products:
            product = MarketplaceProduct(**product_data)
            await db.marketplace_products.insert_one(product.dict())
    
    # Sample Questionnaire
    if await db.questionnaire_templates.count_documents({}) == 0:
        questionnaire = {
            "id": "biohacking-assessment-v1",
            "name": "Biohacking Health Assessment",
            "description": "Comprehensive questionnaire to determine your personalized Hackster Stack",
            "questions": [
                {
                    "id": "age_range",
                    "question": "What is your age range?",
                    "question_type": "single_choice",
                    "options": ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
                    "category": "demographics"
                },
                {
                    "id": "gender",
                    "question": "What is your biological sex?",
                    "question_type": "single_choice",
                    "options": ["Male", "Female", "Other/Prefer not to say"],
                    "category": "demographics"
                },
                {
                    "id": "primary_goal",
                    "question": "What is your PRIMARY health goal?",
                    "question_type": "single_choice",
                    "options": ["More Energy", "Better Sleep", "Mental Focus", "Athletic Performance", "Longevity", "Stress Management", "Weight Management", "Immune Support"],
                    "category": "health_goals"
                },
                {
                    "id": "secondary_goals",
                    "question": "Select any SECONDARY health goals:",
                    "question_type": "multiple_choice",
                    "options": ["More Energy", "Better Sleep", "Mental Focus", "Athletic Performance", "Longevity", "Stress Management", "Weight Management", "Immune Support", "Gut Health", "Hormone Balance", "Heart Health"],
                    "category": "health_goals"
                },
                {
                    "id": "energy_level",
                    "question": "How would you rate your current energy levels?",
                    "question_type": "scale",
                    "scale_min": 1,
                    "scale_max": 10,
                    "category": "current_health"
                },
                {
                    "id": "sleep_quality",
                    "question": "How would you rate your sleep quality?",
                    "question_type": "scale",
                    "scale_min": 1,
                    "scale_max": 10,
                    "category": "current_health"
                },
                {
                    "id": "stress_level",
                    "question": "How would you rate your stress levels?",
                    "question_type": "scale",
                    "scale_min": 1,
                    "scale_max": 10,
                    "category": "current_health"
                },
                {
                    "id": "exercise_frequency",
                    "question": "How often do you exercise?",
                    "question_type": "single_choice",
                    "options": ["Never", "1-2 times/week", "3-4 times/week", "5+ times/week", "Daily"],
                    "category": "lifestyle"
                },
                {
                    "id": "diet_type",
                    "question": "How would you describe your diet?",
                    "question_type": "single_choice",
                    "options": ["Standard American Diet", "Mostly Healthy", "Clean Eating", "Keto/Low Carb", "Mediterranean", "Vegan/Vegetarian", "Carnivore", "Other"],
                    "category": "diet"
                },
                {
                    "id": "current_supplements",
                    "question": "Which supplements do you currently take?",
                    "question_type": "multiple_choice",
                    "options": ["None", "Multivitamin", "Vitamin D", "Magnesium", "Omega-3/Fish Oil", "Probiotics", "Protein Powder", "Creatine", "Pre-workout", "Other"],
                    "category": "current_health"
                },
                {
                    "id": "health_concerns",
                    "question": "Do you have any specific health concerns?",
                    "question_type": "multiple_choice",
                    "options": ["None", "Fatigue", "Poor Sleep", "Brain Fog", "Digestive Issues", "Joint Pain", "Mood/Anxiety", "Blood Sugar", "Thyroid", "Hormonal Imbalance"],
                    "category": "current_health"
                },
                {
                    "id": "budget",
                    "question": "What's your monthly supplement budget?",
                    "question_type": "single_choice",
                    "options": ["Under $50", "$50-100", "$100-200", "$200-300", "$300+"],
                    "category": "preferences"
                }
            ]
        }
        await db.questionnaire_templates.insert_one(questionnaire)

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
    """Create a coach profile (authenticated coaches only)"""
    if current_user.role != UserRole.COACH:
        raise HTTPException(status_code=403, detail="Only coaches can create coach profiles")
    
    # Check if user already has a coach profile
    existing_coach = await db.coaches.find_one({"user_id": current_user.id})
    if existing_coach:
        raise HTTPException(status_code=400, detail="Coach profile already exists")
    
    coach_profile = Coach(
        user_id=current_user.id,
        **coach_data.dict()
    )
    
    await db.coaches.insert_one(coach_profile.dict())
    return coach_profile

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
    """Get the biohacking health assessment questionnaire"""
    questionnaire = await db.questionnaire_templates.find_one({"id": "biohacking-assessment-v1"})
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return questionnaire

@api_router.post("/questionnaire/submit", response_model=AIRecommendation)
async def submit_questionnaire(submission: AIQuestionnaireSubmission, current_user: Optional[UserProfile] = None):
    """Submit questionnaire and get AI-powered recommendations"""
    try:
        # Get current user if authenticated
        user_profile = None
        user_id = "anonymous"
        
        if current_user:
            user_profile = current_user
            user_id = current_user.id
        
        # Generate AI recommendations
        ai_result = await generate_ai_recommendations(submission.responses, user_profile)
        
        # Create session ID for this questionnaire submission
        session_id = str(uuid.uuid4())
        
        # Convert health goals from strings to enum values if needed
        primary_goals = []
        for goal in ai_result.get("primary_goals", []):
            try:
                if isinstance(goal, str):
                    goal_enum = HealthGoal(goal.lower().replace(" ", "_"))
                    primary_goals.append(goal_enum)
            except ValueError:
                continue
        
        # Create recommendation record
        recommendation = AIRecommendation(
            user_id=user_id,
            questionnaire_session_id=session_id,
            health_score=ai_result.get("health_score", 70),
            primary_goals=primary_goals,
            recommended_products=ai_result.get("recommended_products", []),
            recommended_lab_tests=ai_result.get("recommended_lab_tests", []),
            lifestyle_tips=ai_result.get("lifestyle_tips", []),
            personalized_summary=ai_result.get("personalized_summary", ""),
            ai_reasoning=ai_result.get("ai_reasoning", "")
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
    allow_origins=os.environ.get('CORS_ORIGINS', 'http://localhost:3000,https://localhost:3000').split(','),
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