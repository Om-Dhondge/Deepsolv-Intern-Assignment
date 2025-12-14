# LinkedIn Insights Microservice

A full-stack application to scrape, store, and analyze LinkedIn company pages with detailed insights.

## Features

### Mandatory Requirements ✅
- **LinkedIn Page Scraper**: Scrapes company pages for comprehensive data
  - Basic details (name, URL, ID, profile picture, description, website, industry)
  - Follower count and employee count
  - Company size, headquarters, founded date, specialties
  - Recent posts (15-25 posts with engagement metrics)
  - Comments on posts
  - People working at the company

- **Database Storage**: MongoDB with proper schemas and relationships
  - LinkedInPage collection
  - LinkedInPost collection
  - LinkedInUser collection
  - Comment collection (embedded in posts)

- **RESTful API Endpoints**:
  - `GET /api/pages/{page_id}` - Get page details (scrapes if not in DB)
  - `GET /api/pages` - List pages with filters and pagination
  - `GET /api/pages/{page_id}/posts` - Get recent posts
  - `GET /api/pages/{page_id}/employees` - Get employee list
  - `GET /api/pages/{page_id}/followers` - Get follower information

- **Advanced Filtering**:
  - Search by page name (similar search)
  - Filter by industry
  - Filter by follower count range (min/max)
  - Pagination on all list endpoints

- **Postman Collection**: Complete API collection included at `/app/LinkedIn_Insights_API.postman_collection.json`

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React
- **Database**: MongoDB
- **Scraping**: Playwright (headless browser automation)
- **Styling**: Custom CSS with modern design

## Architecture

```
/app/
├── backend/
│   ├── server.py           # FastAPI application with all endpoints
│   ├── models.py           # Pydantic models for data validation
│   ├── scraper.py          # LinkedIn scraper using Playwright
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Global styles
│   │   └── pages/
│   │       ├── Dashboard.js    # Home page with search
│   │       ├── PageList.js     # Browse all pages with filters
│   │       └── PageDetails.js  # Detailed page view
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend environment variables
└── LinkedIn_Insights_API.postman_collection.json  # API collection

```

## Database Schema

### LinkedInPage
```python
{
    "page_id": str,              # Unique page identifier
    "page_name": str,
    "page_url": str,
    "linkedin_id": str,
    "profile_picture": str,
    "description": str,
    "website": str,
    "industry": str,
    "company_size": str,
    "headquarters": str,
    "founded": str,
    "specialties": List[str],
    "follower_count": int,
    "employee_count": int,
    "scraped_at": datetime,
    "updated_at": datetime
}
```

### LinkedInPost
```python
{
    "post_id": str,
    "page_id": str,              # Foreign key to page
    "content": str,
    "posted_date": str,
    "likes": int,
    "comments_count": int,
    "shares": int,
    "post_url": str,
    "media_urls": List[str]
}
```

### LinkedInUser
```python
{
    "user_id": str,
    "name": str,
    "profile_url": str,
    "profile_picture": str,
    "title": str,
    "page_id": str              # Foreign key to page
}
```

## API Endpoints

### 1. Get Page by ID
```
GET /api/pages/{page_id}
```
Fetches page details. If not in database, scrapes in real-time.

**Example**: `GET /api/pages/deepsolv`

### 2. List All Pages
```
GET /api/pages?page=1&page_size=10&name=tech&industry=software&follower_count_min=1000&follower_count_max=50000
```
List pages with optional filters and pagination.

**Query Parameters**:
- `page` (default: 1) - Page number
- `page_size` (default: 10, max: 100) - Items per page
- `name` (optional) - Search by company name
- `industry` (optional) - Filter by industry
- `follower_count_min` (optional) - Minimum followers
- `follower_count_max` (optional) - Maximum followers

### 3. Get Page Posts
```
GET /api/pages/{page_id}/posts?page=1&page_size=15
```
Get recent posts with pagination.

### 4. Get Page Employees
```
GET /api/pages/{page_id}/employees?page=1&page_size=20
```
Get employee list with pagination.

### 5. Get Page Followers
```
GET /api/pages/{page_id}/followers
```
Get follower count information.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Yarn package manager

### Backend Setup
```bash
cd /app/backend
pip install -r requirements.txt
playwright install chromium
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd /app/frontend
yarn install
yarn start
```

### Environment Variables

**Backend (.env)**:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
```

**Frontend (.env)**:
```
REACT_APP_BACKEND_URL=http://your-backend-url
```

## Using the Postman Collection

1. Import the collection: `/app/LinkedIn_Insights_API.postman_collection.json`
2. Set the `base_url` variable to your backend URL (default: `http://localhost:8001/api`)
3. Run requests in the following order for testing:
   - Health Check
   - Get Page by ID (this will scrape and store data)
   - List All Pages
   - Get Page Posts
   - Get Page Employees

## Example Usage

### Scrape a LinkedIn Page
```bash
curl -X GET "http://localhost:8001/api/pages/deepsolv"
```

### Search Pages by Name
```bash
curl -X GET "http://localhost:8001/api/pages?name=tech&page=1&page_size=10"
```

### Filter by Follower Range
```bash
curl -X GET "http://localhost:8001/api/pages?follower_count_min=20000&follower_count_max=40000"
```

### Get Recent Posts
```bash
curl -X GET "http://localhost:8001/api/pages/deepsolv/posts?page=1&page_size=15"
```

## Frontend Features

### Dashboard
- Search for LinkedIn pages by page ID
- Quick access to browse all analyzed pages
- Feature highlights

### Page List
- View all analyzed pages
- Filter by name, industry, follower count
- Pagination controls
- Click to view details

### Page Details
- Complete company information
- Statistics (followers, employees, industry, size)
- Tabbed interface:
  - Overview: Company details and specialties
  - Posts: Recent posts with engagement metrics
  - Employees: List of people working at the company

## Design Highlights

- Modern LinkedIn-inspired color scheme (blue gradient)
- Glass-morphism effects
- Responsive grid layouts
- Smooth animations and transitions
- Professional typography (Manrope for headings, Inter for body)
- Hover effects and interactive elements

## Limitations & Notes

1. **LinkedIn Anti-Scraping**: LinkedIn has sophisticated anti-scraping measures. The scraper may encounter rate limits or CAPTCHAs. For production use, consider:
   - Using LinkedIn Official API
   - Implementing proxy rotation
   - Adding delays between requests
   - Using authenticated sessions

2. **Scraping Performance**: Initial scraping can take 15-30 seconds per page depending on content volume.

3. **Data Freshness**: Scraped data is stored in DB. Re-scraping the same page will use cached data. Implement cache invalidation if real-time data is needed.

4. **Follower Lists**: Full follower lists are not accessible via scraping without authentication. The API returns follower counts only.

## Future Enhancements (Bonus Features)

These features are planned but not yet implemented:
- ✅ Asynchronous programming (already implemented with FastAPI async/await)
- ⏳ AI Summary using LLMs (ChatGPT/Claude/Gemini)
- ⏳ Storage server integration (S3/GCS) for images
- ⏳ Redis caching with TTL
- ⏳ Docker containerization

## Troubleshooting

### Scraping Errors
- Verify the page ID is correct
- Check internet connectivity
- LinkedIn may be blocking automated access - consider using LinkedIn API

### Database Connection Issues
- Ensure MongoDB is running
- Verify MONGO_URL in backend/.env

### Frontend Not Loading
- Check REACT_APP_BACKEND_URL is set correctly
- Verify backend is running on the correct port
- Check CORS configuration

## License

This project is for educational and demonstration purposes.

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.
