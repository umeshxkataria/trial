# backend/server.py

import os
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from PyPDF2 import PdfReader
import docx
import openai
import bcrypt
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-192837465")
UPLOAD_DIR = "uploads"

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# -------------------------
# Initialize FastAPI
# -------------------------
app = FastAPI(title="Resume AI Backend")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# In-Memory Storage (Development)
# -------------------------
class InMemoryCollection:
    """Simple in-memory storage for development"""
    def __init__(self):
        self.data = {}
    
    async def find_one(self, query):
        for doc in self.data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    async def insert_one(self, doc):
        doc_id = ObjectId()
        doc["_id"] = doc_id
        self.data[str(doc_id)] = doc
        
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        
        return InsertResult(doc_id)
    
    async def find(self, query):
        results = []
        for doc in self.data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        
        class FindResult:
            def __init__(self, docs):
                self.docs = docs
            
            async def to_list(self, length):
                return self.docs
        
        return FindResult(results)

# Use in-memory collections for development
users_collection = InMemoryCollection()
resumes_collection = InMemoryCollection()

print("✓ Using in-memory storage for development")

# -------------------------
# Pydantic Models
# -------------------------
class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "job_seeker"

class UserLogin(BaseModel):
    email: str
    password: str

# -------------------------
# Helpers: Parse PDF/DOCX
# -------------------------
def parse_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# -------------------------
# JWT Helpers
# -------------------------
def create_token(user_id: str, email: str, name: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # Handle Bearer token
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -------------------------
# Routes
# -------------------------

@app.get("/")
async def root():
    return {"message": "Resume AI Backend is running!"}

# ==================== AUTH ROUTES ====================

@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    """Register a new user"""
    try:
        existing = await users_collection.find_one({"email": user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        user_doc = {
            "email": user.email,
            "name": user.name or user.email.split("@")[0],
            "password": hashed_pw.decode(),
            "role": user.role,
            "created_at": datetime.utcnow()
        }
        result = await users_collection.insert_one(user_doc)
        
        token = create_token(str(result.inserted_id), user.email, user_doc["name"], user.role)
        return {
            "token": token,
            "user": {
                "id": str(result.inserted_id),
                "email": user.email,
                "name": user_doc["name"],
                "role": user.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(e)}")

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user"""
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(user.password.encode(), db_user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(str(db_user["_id"]), db_user["email"], db_user["name"], db_user["role"])
    return {
        "token": token,
        "user": {
            "id": str(db_user["_id"]),
            "email": db_user["email"],
            "name": db_user["name"],
            "role": db_user["role"]
        }
    }

@app.get("/api/auth/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await users_collection.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== RESUME ROUTES ====================

@app.post("/api/resumes/upload")
async def upload_resume(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Upload and parse resume"""
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Parse resume content
        if file.filename.lower().endswith(".pdf"):
            content = parse_pdf(file_path)
        elif file.filename.lower().endswith(".docx"):
            content = parse_docx(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Get user from token
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]

        # Save to MongoDB
        resume_doc = {
            "user_id": ObjectId(user_id),
            "filename": file.filename,
            "content": content,
            "created_at": datetime.utcnow()
        }
        result = await resumes_collection.insert_one(resume_doc)

        return {"filename": file.filename, "resume_id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def get_resumes(authorization: Optional[str] = Header(None)):
    """Get user's resumes"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]
        
        find_result = await resumes_collection.find({"user_id": ObjectId(user_id)})
        resumes = await find_result.to_list(None)
        return [{"id": str(r["_id"]), "filename": r["filename"], "created_at": r.get("created_at")} for r in resumes]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching resumes: {str(e)}")

@app.post("/api/resumes/analyze/{resume_id}")
async def analyze_resume(resume_id: str, authorization: Optional[str] = Header(None)):
    """Analyze resume with OpenAI"""
    try:
        resume = await resumes_collection.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        content = resume["content"]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume analyzer."},
                {"role": "user", "content": f"Analyze this resume and provide a summary:\n{content}"}
            ],
            temperature=0.5
        )
        analysis = response.choices[0].message.content
        return {"analysis": analysis}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== JOB ROUTES ====================

@app.get("/api/jobs")
async def get_jobs(authorization: Optional[str] = Header(None)):
    """Get all jobs"""
    try:
        jobs_collection = InMemoryCollection()
        jobs = await jobs_collection.find({}).to_list(None)
        return [{"id": str(j["_id"]), "title": j.get("title"), "company": j.get("company"), "description": j.get("description")} for j in jobs]
    except Exception as e:
        return []

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, authorization: Optional[str] = Header(None)):
    """Get a specific job"""
    try:
        jobs_collection = InMemoryCollection()
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs")
async def create_job(job_data: dict, authorization: Optional[str] = Header(None)):
    """Create a new job"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]
        
        jobs_collection = InMemoryCollection()
        job_doc = {
            **job_data,
            "employer_id": ObjectId(user_id),
            "created_at": datetime.utcnow()
        }
        result = await jobs_collection.insert_one(job_doc)
        
        return {"id": str(result.inserted_id), **job_doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== APPLICATION ROUTES ====================

@app.get("/api/applications")
async def get_applications(authorization: Optional[str] = Header(None)):
    """Get user's job applications"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]
        
        applications_collection = InMemoryCollection()
        apps = await applications_collection.find({"user_id": ObjectId(user_id)}).to_list(None)
        return [{"id": str(a["_id"]), "job_id": str(a.get("job_id")), "status": a.get("status")} for a in apps]
    except HTTPException:
        raise
    except Exception as e:
        return []

@app.post("/api/applications")
async def create_application(app_data: dict, authorization: Optional[str] = Header(None)):
    """Create a job application"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]
        
        applications_collection = InMemoryCollection()
        app_doc = {
            **app_data,
            "user_id": ObjectId(user_id),
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        result = await applications_collection.insert_one(app_doc)
        
        return {"id": str(result.inserted_id), "status": "pending"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))