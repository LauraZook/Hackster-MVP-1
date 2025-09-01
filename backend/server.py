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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'hackster-ai-secret-key-for-jwt-tokens-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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