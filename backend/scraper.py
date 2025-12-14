import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
        
    async def scrape_page(self, page_id: str) -> Dict[str, Any]:
        """
        Scrape LinkedIn company page data
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                company_url = f"{self.base_url}/company/{page_id}/"
                
                try:
                    await page.goto(company_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)
                except PlaywrightTimeoutError:
                    logger.warning(f"Timeout loading {company_url}, continuing anyway")
                
                # Extract page data
                page_data = await self._extract_page_info(page, page_id, company_url)
                
                # Extract posts
                posts = await self._extract_posts(page, page_id)
                
                # Extract employees (limited)
                employees = await self._extract_employees(page, page_id)
                
                await browser.close()
                
                return {
                    "page": page_data,
                    "posts": posts,
                    "employees": employees
                }
                
        except Exception as e:
            logger.error(f"Error scraping page {page_id}: {str(e)}")
            raise
    
    async def _extract_page_info(self, page: Page, page_id: str, url: str) -> Dict[str, Any]:
        """Extract company page information"""
        try:
            data = {
                "page_id": page_id,
                "page_url": url,
                "linkedin_id": page_id,
                "page_name": None,
                "profile_picture": None,
                "cover_image": None,
                "description": None,
                "website": None,
                "industry": None,
                "company_size": None,
                "headquarters": None,
                "founded": None,
                "specialties": [],
                "follower_count": 0,
                "employee_count": 0
            }
            
            # Company name
            try:
                name_elem = await page.query_selector("h1.org-top-card-summary__title")
                if name_elem:
                    data["page_name"] = (await name_elem.text_content()).strip()
            except Exception as e:
                logger.debug(f"Could not extract company name: {e}")
            
            # Profile picture
            try:
                img_elem = await page.query_selector("img.org-top-card-primary-content__logo")
                if img_elem:
                    data["profile_picture"] = await img_elem.get_attribute("src")
            except Exception as e:
                logger.debug(f"Could not extract profile picture: {e}")
            
            # Description
            try:
                desc_elem = await page.query_selector("p.org-top-card-summary__tagline")
                if desc_elem:
                    data["description"] = (await desc_elem.text_content()).strip()
            except Exception as e:
                logger.debug(f"Could not extract description: {e}")
            
            # Followers
            try:
                followers_elem = await page.query_selector(".org-top-card-summary-info-list__info-item")
                if followers_elem:
                    text = await followers_elem.text_content()
                    match = re.search(r'([\d,]+)\s*followers', text, re.IGNORECASE)
                    if match:
                        data["follower_count"] = int(match.group(1).replace(',', ''))
            except Exception as e:
                logger.debug(f"Could not extract followers: {e}")
            
            # About section details
            try:
                await page.click("a[href*='about']", timeout=5000)
                await asyncio.sleep(1)
                
                # Industry
                industry_elem = await page.query_selector("dd.org-about-company-module__industry")
                if industry_elem:
                    data["industry"] = (await industry_elem.text_content()).strip()
                
                # Company size
                size_elem = await page.query_selector("dd.org-about-company-module__company-size-definition-text")
                if size_elem:
                    data["company_size"] = (await size_elem.text_content()).strip()
                    match = re.search(r'([\d,]+)', data["company_size"])
                    if match:
                        data["employee_count"] = int(match.group(1).replace(',', ''))
                
                # Headquarters
                hq_elem = await page.query_selector("dd.org-about-company-module__headquarters")
                if hq_elem:
                    data["headquarters"] = (await hq_elem.text_content()).strip()
                
                # Founded
                founded_elem = await page.query_selector("dd.org-about-company-module__founded")
                if founded_elem:
                    data["founded"] = (await founded_elem.text_content()).strip()
                
                # Website
                website_elem = await page.query_selector("a.org-about-us-company-module__website")
                if website_elem:
                    data["website"] = await website_elem.get_attribute("href")
                
                # Specialties
                spec_elem = await page.query_selector("dd.org-about-company-module__specialities")
                if spec_elem:
                    specialties_text = (await spec_elem.text_content()).strip()
                    data["specialties"] = [s.strip() for s in specialties_text.split(',')]
                    
            except Exception as e:
                logger.debug(f"Could not extract about section: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting page info: {e}")
            return {}
    
    async def _extract_posts(self, page: Page, page_id: str) -> List[Dict[str, Any]]:
        """Extract recent posts from company page"""
        posts = []
        try:
            # Navigate to posts
            try:
                await page.click("a[href*='posts']", timeout=5000)
                await asyncio.sleep(2)
            except:
                logger.debug("Could not navigate to posts section")
            
            # Scroll to load posts
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(1)
            
            # Extract posts
            post_cards = await page.query_selector_all(".feed-shared-update-v2")
            
            for idx, post_card in enumerate(post_cards[:20]):
                try:
                    post_data = {
                        "post_id": f"{page_id}_post_{idx}_{int(datetime.utcnow().timestamp())}",
                        "page_id": page_id,
                        "content": None,
                        "posted_date": None,
                        "likes": 0,
                        "comments_count": 0,
                        "shares": 0,
                        "post_url": None,
                        "media_urls": []
                    }
                    
                    # Content
                    content_elem = await post_card.query_selector(".feed-shared-text")
                    if content_elem:
                        post_data["content"] = (await content_elem.text_content()).strip()[:500]
                    
                    # Post date
                    date_elem = await post_card.query_selector(".feed-shared-actor__sub-description")
                    if date_elem:
                        post_data["posted_date"] = (await date_elem.text_content()).strip()
                    
                    # Engagement metrics
                    likes_elem = await post_card.query_selector(".social-details-social-counts__reactions-count")
                    if likes_elem:
                        likes_text = await likes_elem.text_content()
                        match = re.search(r'([\d,]+)', likes_text)
                        if match:
                            post_data["likes"] = int(match.group(1).replace(',', ''))
                    
                    comments_elem = await post_card.query_selector(".social-details-social-counts__comments")
                    if comments_elem:
                        comments_text = await comments_elem.text_content()
                        match = re.search(r'([\d,]+)', comments_text)
                        if match:
                            post_data["comments_count"] = int(match.group(1).replace(',', ''))
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    logger.debug(f"Error extracting post {idx}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting posts: {e}")
        
        return posts
    
    async def _extract_employees(self, page: Page, page_id: str) -> List[Dict[str, Any]]:
        """Extract employee information"""
        employees = []
        try:
            # Navigate to people section
            try:
                await page.click("a[href*='people']", timeout=5000)
                await asyncio.sleep(2)
            except:
                logger.debug("Could not navigate to people section")
                return employees
            
            # Extract employee cards
            employee_cards = await page.query_selector_all(".org-people-profile-card")
            
            for idx, card in enumerate(employee_cards[:50]):
                try:
                    employee_data = {
                        "user_id": f"{page_id}_user_{idx}",
                        "name": None,
                        "profile_url": None,
                        "profile_picture": None,
                        "title": None,
                        "page_id": page_id
                    }
                    
                    # Name and profile URL
                    name_elem = await card.query_selector("a.app-aware-link")
                    if name_elem:
                        employee_data["name"] = (await name_elem.text_content()).strip()
                        employee_data["profile_url"] = await name_elem.get_attribute("href")
                    
                    # Profile picture
                    img_elem = await card.query_selector("img")
                    if img_elem:
                        employee_data["profile_picture"] = await img_elem.get_attribute("src")
                    
                    # Title
                    title_elem = await card.query_selector(".org-people-profile-card__profile-title")
                    if title_elem:
                        employee_data["title"] = (await title_elem.text_content()).strip()
                    
                    if employee_data["name"]:
                        employees.append(employee_data)
                        
                except Exception as e:
                    logger.debug(f"Error extracting employee {idx}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting employees: {e}")
        
        return employees
