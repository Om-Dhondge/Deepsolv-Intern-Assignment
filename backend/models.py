from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class LinkedInUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    user_id: str
    name: str
    profile_url: str
    profile_picture: Optional[str] = None
    title: Optional[str] = None
    page_id: str


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    comment_id: str
    post_id: str
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[str] = None


class LinkedInPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    post_id: str
    page_id: str
    content: Optional[str] = None
    posted_date: Optional[str] = None
    likes: Optional[int] = 0
    comments_count: Optional[int] = 0
    shares: Optional[int] = 0
    post_url: Optional[str] = None
    media_urls: Optional[List[str]] = []


class LinkedInPage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    page_id: str
    page_name: Optional[str] = None
    page_url: str
    linkedin_id: Optional[str] = None
    profile_picture: Optional[str] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    specialties: Optional[List[str]] = []
    follower_count: Optional[int] = 0
    employee_count: Optional[int] = 0
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PageListResponse(BaseModel):
    pages: List[LinkedInPage]
    total: int
    page: int
    page_size: int
    total_pages: int


class PostListResponse(BaseModel):
    posts: List[LinkedInPost]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserListResponse(BaseModel):
    users: List[LinkedInUser]
    total: int
    page: int
    page_size: int
    total_pages: int
