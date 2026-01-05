# CNLC

## Installing Dependencies
To install the dependencies needed for this program, copy paste the following commands into your computer's terminal:

MacOS:
```bash
./setup.sh
```

Windows (for Eason):
```bash
.\setup.ps1
```

## Overview and project plan (my notes from Jan 4 call):
**Prompt**: A byte-sized business boost
- Use programming skills to support small local businesses in their community
	- Can be in the form of:
		- CLI
		- Desktop app
		- Interactive interface
	- Should include:
		- Program should include sorting by category (food, retail services)
		- Review/rating (also sort by these)
		- Saving/bookmarking fav businesses
		- Display special deals/coupons
		- Verification step to prevent bot activity
	- *Could also include other info (date created, owner name, history, etc.)*
	- *Recent order history sharing* - this would help discover new businesses from friends that have similar tastes
	- *Fetch data from business website and display on app*
	- *3D model of inside of store* - show vibe and help decide if it's desirable or not
	- *Recommendation model* - user data is put into an ML model and cross-referenced with other users to recommend a place they would like:
		- People who liked X also discovered Y
	- *Points system* - money -> points -> "ratings" (sort of)

## Project Structure

```
CNLC/
├── backend/                          # Python backend for business logic and API
│   ├── api/                          # Flask REST API for Electron to communicate with
│   │   ├── server.py                 # Main Flask application entry point
│   │   └── routes/                   # API endpoint definitions
│   │       ├── businesses.py         # CRUD operations for businesses (GET, POST, PUT, DELETE)
│   │       ├── reviews.py            # Review/rating submission and retrieval endpoints
│   │       ├── categories.py         # Category filtering and listing endpoints
│   │       ├── deals.py              # Deals/coupons management endpoints
│   │       └── auth.py               # User authentication and verification endpoints
│   ├── core/                         # Core business logic (independent of API)
│   │   ├── business_manager.py       # Business operations (add, update, search, filter)
│   │   ├── review_manager.py         # Review/rating calculations and management
│   │   ├── bookmark_manager.py       # User favorites/bookmarks logic
│   │   ├── deal_manager.py           # Deal/coupon validation and expiry logic
│   │   └── verification.py           # Bot prevention and user verification logic
│   ├── models/                       # Data models defining structure of entities
│   │   ├── business.py               # Business schema (name, address, category, hours, etc.)
│   │   ├── review.py                 # Review schema (rating, comment, timestamp, user)
│   │   ├── user.py                   # User schema (username, password hash, bookmarks)
│   │   ├── deal.py                   # Deal/coupon schema (discount, expiry, conditions)
│   │   └── category.py               # Category schema (food, retail, services, etc.)
│   ├── storage/                      # Data persistence layer
│   │   ├── json_handler.py           # Read/write operations for JSON files
│   │   └── data_validator.py         # Validate data before saving to ensure integrity
│   ├── utils/                        # Utility functions and helpers
│   │   ├── sorting.py                # Sort businesses by rating, category, distance, etc.
│   │   ├── search.py                 # Search and filter functionality
│   │   └── validators.py             # Input validation (email, phone, postal code, etc.)
│   └── ml/                           # Machine learning features (future)
│       └── recommender.py            # Recommendation system for business suggestions
│
├── frontend/                         # Electron desktop application (GUI)
│   ├── main.js                       # Electron main process (window management, IPC)
│   ├── preload.js                    # Electron preload script (secure API exposure)
│   ├── package.json                  # Node.js dependencies for Electron
│   └── src/                          # Frontend source code
│       ├── index.html                # Main HTML entry point
│       ├── css/                      # Stylesheets
│       │   ├── styles.css            # Global styles and theme
│       │   ├── business-card.css     # Styling for business listing cards
│       │   └── components.css        # Reusable UI component styles
│       ├── js/                       # JavaScript application logic
│       │   ├── app.js                # Main application initialization and routing
│       │   ├── api-client.js         # Communication layer with Python backend API
│       │   ├── components/           # UI components
│       │   │   ├── business-list.js  # Display grid/list of businesses
│       │   │   ├── business-detail.js# Detailed view of a single business
│       │   │   ├── review-form.js    # Form for submitting reviews
│       │   │   ├── filter-panel.js   # Filters for category, rating, location
│       │   │   ├── bookmarks.js      # User's saved/favorited businesses
│       │   │   └── deals.js          # Display active deals and coupons
│       │   └── utils/
│       │       ├── helpers.js        # Helper functions (formatting, date handling)
│       │       └── constants.js      # App constants and configuration
│       └── assets/                   # Static assets
│           ├── icons/                # Application icons
│           └── images/               # Images and graphics
│
├── data/                             # JSON file storage for all data
│   ├── businesses.json               # All business information
│   ├── reviews.json                  # All user reviews and ratings
│   ├── users.json                    # User accounts and authentication data
│   ├── bookmarks.json                # User-saved favorite businesses
│   ├── deals.json                    # Active deals and coupons
│
├── scripts/                          # Data population and maintenance scripts
│   ├── populate_businesses.py        # Main script to fetch and populate business data
│   ├── osm_overpass_api.py           # OpenStreetMap Overpass API client and methods
│
├── tests/                            # Automated tests
│   ├── test_backend/                 # Backend unit and integration tests
│   │   ├── test_business_manager.py  # Test business logic
│   │   ├── test_review_manager.py    # Test review functionality
│   │   └── test_storage.py           # Test JSON storage operations
│   └── test_frontend/                # Frontend tests
│       └── test_api_client.js        # Test API communication
│
├── docs/                             # Documentation
│   ├── API.md                        # API endpoint documentation
│   ├── SETUP.md                      # Detailed setup instructions
│   └── FEATURES.md                   # Feature specifications and roadmap
│
├── config/                           # Configuration files
│   ├── config.py                     # Backend configuration (API keys, ports, etc.)
│   └── settings.json                 # Application settings
│
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
├── README.md                         # This file
└── LICENSE                           # Project license
```

### Architecture Overview
- **Backend (Python/Flask)**: Handles all data operations, business logic, and serves a REST API
- **Frontend (Electron)**: Desktop GUI that communicates with the backend via HTTP requests
- **Data Layer (JSON)**: Persistent storage using JSON files for simplicity and portability
- **Communication**: Frontend sends HTTP requests to `http://localhost:5000` where Flask serves the API
