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
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Hackster Health Platform API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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
    age: Optional[int] = None
    gender: Optional[str] = None
    goals: List[str] = []
    current_supplements: List[str] = []
    health_conditions: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(UserProfile):
    hashed_password: str

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
            "total_reviews": 127
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
            "total_reviews": 89
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
    query = {}
    if specialty:
        query["specialties"] = {"$in": [specialty]}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    
    coaches = await db.coaches.find(query).sort("rating", -1).to_list(100)
    return [Coach(**coach) for coach in coaches]

@api_router.post("/users", response_model=UserProfile)
async def create_user_profile(user_data: UserProfileCreate):
    """Create a new user profile"""
    user = UserProfile(**user_data.dict())
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user profile by ID"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**user)

@api_router.post("/assessments", response_model=HealthAssessment)
async def create_health_assessment(assessment_data: HealthAssessmentCreate):
    """Create a health assessment and get recommendations"""
    # This would contain logic to analyze responses and generate recommendations
    # For now, we'll create a basic assessment
    assessment = HealthAssessment(**assessment_data.dict())
    
    # Add sample recommendations based on responses
    assessment.recommended_tests = ["comprehensive_metabolic_panel"]
    assessment.recommended_supplements = ["vitamin_d3_k2", "magnesium_bisglycinate"]
    assessment.score = 75  # Sample score
    
    await db.assessments.insert_one(assessment.dict())
    return assessment

@api_router.get("/assessments/{user_id}", response_model=List[HealthAssessment])
async def get_user_assessments(user_id: str):
    """Get all assessments for a user"""
    assessments = await db.assessments.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return [HealthAssessment(**assessment) for assessment in assessments]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
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
    await initialize_sample_data()
    logger.info("Hackster Health Platform API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()