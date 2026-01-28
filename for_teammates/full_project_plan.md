# CNLC Full Project Plan

## Project Overview
CNLC (Canadian Non-chain Local Catalog) is a desktop application for discovering local, non-chain businesses in Canadian cities. Built with Python Flask backend and Electron frontend.

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
