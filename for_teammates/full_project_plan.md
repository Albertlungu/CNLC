# CNLC Full Project Plan

## Project Overview
CNLC (Canadian Non-chain Local Catalog) is a desktop application for discovering local, non-chain businesses in Canadian cities. Built with Python Flask backend and Electron frontend.

---

## Phase 1: Core Business Features ✅ COMPLETED

### Components
- **Business Data Population**: OSM Overpass API integration with chain filtering
- **Business Models**: Pydantic validation for Business and Address
- **Business Manager**: Search, filter, radius operations
- **Flask API**: RESTful endpoints with filter stacking
- **Utilities**: Fuzzy search, geolocation (Haversine), JSON storage

### Status
- ✅ 553k+ businesses populated across 8 cities
- ✅ Search by name (fuzzy matching with fuzzywuzzy)
- ✅ Filter by category
- ✅ Radius filtering with geolocation
- ✅ Filter stacking (combine multiple filters)
- ✅ RESTful API with CORS enabled
- ✅ Error handling and validation

### Files Implemented
- `backend/models/business.py` - Pydantic models
- `backend/core/business_manager.py` - Business logic
- `backend/api/server.py` - Flask application
- `backend/utils/search.py` - Search utilities
- `backend/utils/geo.py` - Geolocation utilities
- `backend/storage/json_handler.py` - JSON I/O
- `data/businesses.json` - Business data
- `scripts/overpass_api.py` - Data fetching
- `scripts/populate_businesses.py` - Data pipeline

---

## Phase 2: User Features 🔄 IN PROGRESS

### Objective
Add user accounts, authentication, and bookmarking functionality to personalize the experience.

### Components

#### 2.1 User Model & Validation
- **File**: `backend/models/user.py`
- **Purpose**: Define user data structure with validation
- **Features**:
  - User ID (UUID)
  - Username (unique, 3-30 characters)
  - Email (unique, validated format)
  - Password hash (bcrypt)
  - Created timestamp
  - Last login timestamp
  - Account status (active/inactive)

#### 2.2 User Manager
- **File**: `backend/core/user_manager.py`
- **Purpose**: Handle user CRUD operations and authentication
- **Features**:
  - Create user (registration)
  - Authenticate user (login)
  - Update user profile
  - Change password
  - Delete user account
  - Get user by ID/username/email

#### 2.3 Bookmark System
- **File**: `backend/core/bookmark_manager.py`
- **Purpose**: Manage user bookmarks/favorites
- **Features**:
  - Add bookmark
  - Remove bookmark
  - Get all bookmarks for user
  - Check if business is bookmarked
  - Bookmark counts per business

#### 2.4 Human Verification
- **File**: `backend/core/verification.py`
- **Purpose**: Bot prevention for registration/login
- **Features**:
  - Simple math CAPTCHA
  - Session-based challenge storage
  - Rate limiting integration
  - Challenge generation and validation

#### 2.5 User API Routes
- **File**: `backend/api/routes/users.py` (new)
- **Endpoints**:
  - `POST /api/users/register` - Create account
  - `POST /api/users/login` - Authenticate
  - `POST /api/users/logout` - End session
  - `GET /api/users/profile` - Get user info
  - `PUT /api/users/profile` - Update profile
  - `PUT /api/users/password` - Change password
  - `DELETE /api/users/account` - Delete account

#### 2.6 Bookmark API Routes
- **File**: `backend/api/routes/bookmarks.py` (new)
- **Endpoints**:
  - `POST /api/bookmarks` - Add bookmark
  - `DELETE /api/bookmarks/<business_id>` - Remove bookmark
  - `GET /api/bookmarks` - Get user's bookmarks
  - `GET /api/bookmarks/check/<business_id>` - Check if bookmarked

#### 2.7 Data Storage
- **Files**:
  - `data/users.json` - User accounts
  - `data/bookmarks.json` - User bookmarks
- **Structure**: JSON arrays with appropriate schemas

### Dependencies Already Available
- `bcrypt==4.1.2` - Password hashing
- `flask-limiter==3.5.0` - Rate limiting
- `python-dateutil==2.8.2` - Timestamp handling

### Documentation
- **Guide**: `private/phase2_user_features.md` (to be created)
- **Style**: Matches `private/flask_api.md` format
- **Content**: In-depth explanations + code hints

---

## Phase 3: Review System 📋 PLANNED

### Objective
Allow users to write and read reviews for businesses.

### Components
- Review Model (`backend/models/review.py`)
- Review Manager (`backend/core/review_manager.py`)
- Review API routes
- Optional: Fetch reviews from Google/Yelp APIs
- Rating aggregation and sorting

### Features
- Create review with rating (1-5 stars)
- Edit own reviews
- Delete own reviews
- Get reviews for business
- Get reviews by user
- Calculate average rating
- Sort by date/rating/helpfulness

---

## Phase 4: Deals & Coupons 💰 PLANNED

### Objective
Businesses can post deals/coupons, users can discover and save them.

### Components
- Deal Model (`backend/models/deal.py`)
- Deal Manager (`backend/core/deal_manager.py`)
- Deal API routes
- Expiration date handling
- Optional: Scrape deals from websites

### Features
- Create deal (business owners)
- Browse active deals
- Filter deals by category/location
- Save deals to user account
- Automatic expiration cleanup
- Deal notifications

---

## Phase 5: Social Features 👥 PLANNED

### Objective
Friend network and social interactions.

### Components
- Friend relationship model
- Friend Manager
- Friend API routes
- Activity feed

### Features
- Send/accept/reject friend requests
- View friends list
- See friends' reviews and bookmarks
- Friend recommendations
- Privacy settings

---

## Phase 6: AI Recommendations 🤖 PLANNED

### Objective
Personalized business recommendations using ML.

### Components
- Recommender system (`backend/ml/recommender.py`)
- ML model training
- Recommendation API routes

### Features
- Collaborative filtering (users who liked X also liked Y)
- Content-based filtering (similar businesses)
- Hybrid recommendations
- Learning from user interactions
- Diversity in recommendations

---

## Phase 7: Frontend Development 🖥️ PLANNED

### Objective
Build Electron desktop application UI.

### Components
- Electron main process (`frontend/main.js`)
- Preload script (`frontend/preload.js`)
- HTML/CSS/JS UI
- API client (`frontend/src/js/api-client.js`)
- Map integration
- Search and filter controls

### Features
- Business list/grid view
- Interactive map with markers
- Search bar with autocomplete
- Category filters
- Radius slider
- Business detail view
- User profile page
- Bookmark management UI
- Review writing/viewing UI

---

## Phase 8: Polish & Production 🚀 PLANNED

### Objective
Prepare for production deployment.

### Components
- Testing suite
- Error handling improvements
- Performance optimization
- Security hardening
- Packaging and distribution

### Features
- Comprehensive test coverage
- Automated testing CI/CD
- Database migration (PostgreSQL with PostGIS)
- HTTPS and SSL
- User authentication tokens (JWT)
- Input sanitization
- Rate limiting
- Logging and monitoring
- Electron app packaging for Mac/Windows/Linux

---

## Current Status Summary

**Completed**: Phase 1 (Core Business Features)
**In Progress**: Phase 2 (User Features) - Documentation phase
**Next Steps**:
1. Create Phase 2 implementation guide
2. Implement user authentication
3. Implement bookmark system
4. Test Phase 2 features
5. Move to Phase 3 (Reviews)

**Overall Progress**: ~15% complete

---

## Technology Stack

### Backend
- Python 3.12
- Flask 3.0.0
- Pydantic 2.5.0
- bcrypt 4.1.2
- fuzzywuzzy (fuzzy search)

### Frontend
- Electron
- HTML/CSS/JavaScript
- Leaflet.js (maps)

### Data
- JSON file storage (MVP)
- Future: PostgreSQL with PostGIS

### External APIs
- OpenStreetMap Overpass API (business data)
- Browser Geolocation API (user location)

---

## Notes
- Focus on MVP functionality first, optimization later
- Maintain layered architecture throughout
- Follow existing code patterns and conventions
- Test each phase before moving to next
- Document as you go
