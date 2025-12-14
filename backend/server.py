from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import Optional, List
import math
from datetime import datetime

from models import (
    LinkedInPage, LinkedInPost, LinkedInUser,
    PageListResponse, PostListResponse, UserListResponse
)
from scraper import LinkedInScraper


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections
pages_collection = db.linkedin_pages
posts_collection = db.linkedin_posts
users_collection = db.linkedin_users

# Create the main app without a prefix
app = FastAPI(title="LinkedIn Insights API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize scraper
scraper = LinkedInScraper()


@api_router.get("/")
async def root():
    return {"message": "LinkedIn Insights Microservice API", "version": "1.0.0"}


@api_router.get("/pages/{page_id}", response_model=LinkedInPage)
async def get_page(page_id: str):
    """
    Get LinkedIn page details by page_id.
    If not in DB, scrape in real-time.
    """
    # Check if page exists in DB
    existing_page = await pages_collection.find_one({"page_id": page_id}, {"_id": 0})
    
    if existing_page:
        # Convert datetime strings back to datetime objects if needed
        if isinstance(existing_page.get('scraped_at'), str):
            existing_page['scraped_at'] = datetime.fromisoformat(existing_page['scraped_at'])
        if isinstance(existing_page.get('updated_at'), str):
            existing_page['updated_at'] = datetime.fromisoformat(existing_page['updated_at'])
        return LinkedInPage(**existing_page)
    
    # Scrape if not found
    try:
        scraped_data = await scraper.scrape_page(page_id)
        
        # Store page data
        page_data = scraped_data["page"]
        page_obj = LinkedInPage(**page_data)
        page_dict = page_obj.model_dump()
        page_dict['scraped_at'] = page_dict['scraped_at'].isoformat()
        page_dict['updated_at'] = page_dict['updated_at'].isoformat()
        await pages_collection.insert_one(page_dict)
        
        # Store posts
        if scraped_data["posts"]:
            posts_to_insert = []
            for post in scraped_data["posts"]:
                post_obj = LinkedInPost(**post)
                posts_to_insert.append(post_obj.model_dump())
            if posts_to_insert:
                await posts_collection.insert_many(posts_to_insert)
        
        # Store employees
        if scraped_data["employees"]:
            users_to_insert = []
            for emp in scraped_data["employees"]:
                user_obj = LinkedInUser(**emp)
                users_to_insert.append(user_obj.model_dump())
            if users_to_insert:
                await users_collection.insert_many(users_to_insert)
        
        return page_obj
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping page: {str(e)}")


@api_router.get("/pages", response_model=PageListResponse)
async def list_pages(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Search by page name"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    follower_count_min: Optional[int] = Query(None, ge=0, description="Minimum follower count"),
    follower_count_max: Optional[int] = Query(None, ge=0, description="Maximum follower count")
):
    """
    List all LinkedIn pages with filters and pagination.
    """
    # Build query
    query = {}
    
    if name:
        query["page_name"] = {"$regex": name, "$options": "i"}
    
    if industry:
        query["industry"] = {"$regex": industry, "$options": "i"}
    
    if follower_count_min is not None or follower_count_max is not None:
        query["follower_count"] = {}
        if follower_count_min is not None:
            query["follower_count"]["$gte"] = follower_count_min
        if follower_count_max is not None:
            query["follower_count"]["$lte"] = follower_count_max
    
    # Get total count
    total = await pages_collection.count_documents(query)
    
    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Get pages
    pages_cursor = pages_collection.find(query, {"_id": 0}).skip(skip).limit(page_size)
    pages_list = await pages_cursor.to_list(length=page_size)
    
    # Convert datetime strings
    for p in pages_list:
        if isinstance(p.get('scraped_at'), str):
            p['scraped_at'] = datetime.fromisoformat(p['scraped_at'])
        if isinstance(p.get('updated_at'), str):
            p['updated_at'] = datetime.fromisoformat(p['updated_at'])
    
    pages_objects = [LinkedInPage(**p) for p in pages_list]
    
    return PageListResponse(
        pages=pages_objects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@api_router.get("/pages/{page_id}/posts", response_model=PostListResponse)
async def get_page_posts(
    page_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=50, description="Items per page")
):
    """
    Get recent posts for a LinkedIn page with pagination.
    """
    # Check if page exists
    page_exists = await pages_collection.find_one({"page_id": page_id})
    if not page_exists:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get posts
    query = {"page_id": page_id}
    total = await posts_collection.count_documents(query)
    
    skip = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    posts_cursor = posts_collection.find(query, {"_id": 0}).skip(skip).limit(page_size)
    posts_list = await posts_cursor.to_list(length=page_size)
    
    posts_objects = [LinkedInPost(**p) for p in posts_list]
    
    return PostListResponse(
        posts=posts_objects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@api_router.get("/pages/{page_id}/employees", response_model=UserListResponse)
async def get_page_employees(
    page_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get employees/people working at a LinkedIn page with pagination.
    """
    # Check if page exists
    page_exists = await pages_collection.find_one({"page_id": page_id})
    if not page_exists:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get users
    query = {"page_id": page_id}
    total = await users_collection.count_documents(query)
    
    skip = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    users_cursor = users_collection.find(query, {"_id": 0}).skip(skip).limit(page_size)
    users_list = await users_cursor.to_list(length=page_size)
    
    users_objects = [LinkedInUser(**u) for u in users_list]
    
    return UserListResponse(
        users=users_objects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@api_router.get("/pages/{page_id}/followers")
async def get_page_followers(page_id: str):
    """
    Get followers list for a page.
    Note: LinkedIn doesn't easily expose follower lists via scraping.
    This endpoint returns follower count from page data.
    """
    page_data = await pages_collection.find_one({"page_id": page_id}, {"_id": 0})
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {
        "page_id": page_id,
        "follower_count": page_data.get("follower_count", 0),
        "note": "Full follower list requires LinkedIn API or authentication"
    }


@api_router.post("/pages/demo/{page_id}")
async def create_demo_page(page_id: str):
    """
    Create a demo page with mock data for testing purposes.
    Use this for demonstration when LinkedIn scraping is blocked.
    """
    import random
    from datetime import datetime, timezone
    
    # Check if page already exists
    existing = await pages_collection.find_one({"page_id": page_id})
    if existing:
        return {"message": "Page already exists", "page_id": page_id}
    
    # Create mock page data
    demo_data = {
        "page_id": page_id,
        "page_name": f"{page_id.capitalize()} Corporation",
        "page_url": f"https://www.linkedin.com/company/{page_id}/",
        "linkedin_id": page_id,
        "profile_picture": f"https://media.licdn.com/dms/image/v2/{page_id}/company-logo_200_200/0/1234567890000",
        "description": f"Leading technology company specializing in innovative solutions. {page_id.capitalize()} is transforming the industry with cutting-edge products and services.",
        "website": f"https://www.{page_id}.com",
        "industry": "Technology, Information and Internet",
        "company_size": "10,001+ employees",
        "headquarters": "San Francisco, CA",
        "founded": "2010",
        "specialties": ["Cloud Computing", "Artificial Intelligence", "Software Development", "Data Analytics"],
        "follower_count": random.randint(50000, 500000),
        "employee_count": random.randint(1000, 10000),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await pages_collection.insert_one(demo_data)
    
    # Create mock posts
    posts = []
    for i in range(15):
        post = {
            "post_id": f"{page_id}_post_{i}",
            "page_id": page_id,
            "content": f"Exciting update #{i+1} from {page_id.capitalize()}! We're proud to announce our latest innovations in technology and continue to drive excellence in our industry.",
            "posted_date": f"{random.randint(1, 30)} days ago",
            "likes": random.randint(100, 5000),
            "comments_count": random.randint(10, 500),
            "shares": random.randint(5, 200),
            "post_url": f"https://www.linkedin.com/feed/update/urn:li:activity:123456{i}/",
            "media_urls": []
        }
        posts.append(post)
    
    if posts:
        await posts_collection.insert_many(posts)
    
    # Create mock employees
    employees = []
    titles = ["Software Engineer", "Product Manager", "Data Scientist", "Marketing Manager", "Sales Director"]
    names = ["John Smith", "Sarah Johnson", "Michael Chen", "Emily Davis", "David Wilson", "Lisa Anderson", "James Brown", "Maria Garcia"]
    
    for i, name in enumerate(names[:8]):
        employee = {
            "user_id": f"{page_id}_user_{i}",
            "name": name,
            "profile_url": f"https://www.linkedin.com/in/{name.lower().replace(' ', '-')}/",
            "profile_picture": f"https://media.licdn.com/dms/image/v2/profile-{i}/photo.jpg",
            "title": random.choice(titles),
            "page_id": page_id
        }
        employees.append(employee)
    
    if employees:
        await users_collection.insert_many(employees)
    
    return {
        "message": "Demo page created successfully",
        "page_id": page_id,
        "note": "This is mock data for demonstration purposes"
    }


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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
