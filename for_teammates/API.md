
# This document is to explain how the API and the server works to join Python backend and JS frontend
**DEADLINE: FEB 1, 2026**

## Table of Contents

- [Prerequisites](#prerequisites)
- [What's important](#whats-important)
- [Populating the businesses](#populating-the-businesses-not-really-important-you-can-skip)
- [Pydantic verification](#pydantic-verification-slightly-more-important)
- [Business Manager](#business-manager-containing-functions-to-search-through-filter-and-more)
- [Server (MOST IMPORTANT)](#server-most-important)
  - [Query Parameters](#query-parameters)
  - [Example URLs](#example-urls)
  - [Response Format](#response-format)
  - [Testing](#testing)
- [API Endpoints Reference](#api-endpoints-reference)
  - [Businesses](#businesses)
  - [Users](#users)
  - [Authentication](#authentication)
  - [Bookmarks](#bookmarks)
  - [Sessions](#sessions)
- [Frontend Integration Guide](#frontend-integration-guide)
  - [Making API Calls](#making-api-calls)
  - [Authentication Flow](#authentication-flow)
  - [Handling Responses](#handling-responses)
  - [Error Handling](#error-handling)

---

## Prerequisites

Tools used and what you NEED to know at least a little about:
- Flask

What you MIGHT have to know about
- Pydantic
(tl;dr: Basically just to verify the structure of each dictionary for the businesses)

---

## What's important


---

## Populating the businesses (not really important, you can skip)
To have all the businesses here, I didn't add them manually (that would take too long). Instead, I used the Overpass API. This works by going to a certain webpage and injecting some javascript code through the console to get information about a specific business/location.

I used response to do this. You can see the full file [here](./scripts/overpass_api.py)

[./backend/storage/json_handler](./backend/storage/json_handler) was used to save and load JSON files.

Then, I used a different file that brought the two above together and iterated manually through cities. The current cities included are
Ottawa, Gatineau, Montreal, Toronto, Regina, Winnipeg, Calgary, Edmonton

---

## Pydantic verification (slightly more important)
[backend/models/business.py](backend/models/business.py)

Here, I make the blueprint for the businesses, saved as JSON structures. If you want to see how the collection of businesses looks like:

[data/businesses.json](data/businesses.json)

---

## Business Manager (containing functions to search through, filter, and more)
The main scripts here are [backend/utils/search.py](backend/utils/search.py) and [backend/core/business_manager.py](backend/core/business_manager.py).

The search file contains most of the functions to search and filter, which are then used by the business_manager.

The business manager then has the search_by_radius function, which uses [backend/utils/geo.py](backend/utils/geo.py) (the file containing all the math for coordinate geolocation).

---

## Server (MOST IMPORTANT)

[backend/api/server.py](backend/api/server.py)
**Contains:** Error handling, routing.

Basically, you know what's at the end of a website, with the "?", "&", and other symbols like that? That's what server.py handles. It creates a server locally on your computer, and when you access a certain webpage, it uses the words you put into the website URL as arguments to put into the python code, then returns something. Here's an example:

### Example URLs

**A possible link looks like this:**
```
http://127.0.0.1:5000/api/businesses?lat1=45.382865&lon1=-75.732837&radius=20
```

The server, once started, opens the link above. Imagine /api/businesses as just another webpage that returns a value.

**The "?" symbol** means a query exists (parameter inputs start there). Whatever comes after **lat1=** is the floating point used for the user's latitude, and after **lon1=** is the float used for their longitude. **Radius=** represents the radius (in km) that creates a circle around the user in which the computer should search for businesses.

Note that between each parameter, **there is "&"**. This simply means that after "&", a new parameter starts.

**You can also stack parameters:**
```
http://127.0.0.1:5000/api/businesses?category=restaurant&lat1=45.382865&lon1=-75.732837&radius=20
```

The same thing can be seen here, you just add a **category** filter. Below are a list of parameters used and what they expect:

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | - | Search query (e.g., `?search=...`) |
| `category` | string | - | Filter by category (e.g., `?category=restaurant`) |
| `lat1` | float | - | User's latitude coordinate |
| `lon1` | float | - | User's longitude coordinate |
| `radius` | integer | 10 | Search radius in kilometers |
| `filepath` | string | data/businesses.json | JSON file path (DO NOT USE) |

**Implementation:**
```python
search_query = request.args.get('search', type=str)
category = request.args.get('category', type=str)
filepath = request.args.get('filepath', 'data/businesses.json', type=str)
radius = request.args.get('radius', 10, type=int)
lat1 = request.args.get('lat1', type=float)
lon1 = request.args.get('lon1', type=float)
```

All you should worry about here is the what is between quotations and the `type=` part.

The first argument is what is put into the search bar (ex. `http://127.0.0.1:5000/api/businesses?name=...`)

If there are three arguments given, the middle one is the default (e.g. 10 for radius). The third argument is always the datatype it expects.

**Do not use the `filepath` category. Ever.** That's just there if I ever change the filepath to the JSON file containing all the businesses.

### Testing

>[!NOTE]
>I recommend to try using the test_filters shell file to see exactly what it does, the websites it goes to, and which tests pass and fail.

```bash
chmod +x ./tests/test_backend/test_filters.sh
./tests/test_backend/test_filters.sh
```

You'll see the output and what it is (a short title of the test, the URL, and a pass or fail (as well as a count of how many businesses were returned)).

The results are also saved to `./tests/JSON`, where you can see what results look like, or read the below:

### Response Format

```json
{
    "businesses": [
        {
            _a_business_here
        },
        {
            _another_one_here
        },
        {
            etc...
        }
    ]
}
```
`dtype=dict[list[dict]]`

---

## API Endpoints Reference

The server is organized into **blueprints** (separate files for different features). Here's the full list of endpoints:

### Businesses

#### GET /api/businesses
Get a list of businesses with optional filters.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Fuzzy search by business name |
| `category` | string | No | Filter by category (e.g., `restaurant`) |
| `lat1` | float | No | User's latitude (required if using radius) |
| `lon1` | float | No | User's longitude (required if using radius) |
| `radius` | integer | No | Search radius in km (default: 10) |

**Example:**
```
GET /api/businesses?category=restaurant&lat1=45.38&lon1=-75.73&radius=20
```

**Response:**
```json
{
    "status": "success",
    "businesses": [...],
    "count": 42
}
```

#### GET /api/businesses/{id}
Get a single business by its ID.

**Example:**
```
GET /api/businesses/123456
```

**Response:**
```json
{
    "business": {
        "id": 123456,
        "name": "...",
        ...
    }
}
```

---

### Users

#### POST /api/user/create
Create a new user account. **Note:** For registration, use `/api/auth/register` instead (it creates the user AND logs them in).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Email address |
| `phone` | string | Yes | Phone number |
| `password` | string | Yes | Password (will be hashed) |
| `first-name` | string | Yes | First name |
| `last-name` | string | Yes | Last name |
| `city` | string | Yes | City |
| `country` | string | No | Country (default: "Canada") |

**Example:**
```
POST /api/user/create?username=john_doe&email=john@example.com&phone=6135551234&password=secret123&first-name=John&last-name=Doe&city=Ottawa
```

---

### Authentication

These are the main endpoints you'll use for user auth in the frontend.

#### POST /api/auth/register
Register a new user and automatically log them in (creates a session).

**Request Body (JSON):**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "phone": "6135551234",
    "password": "secret123",
    "first-name": "John",
    "last-name": "Doe",
    "city": "Ottawa",
    "country": "Canada"
}
```

**Response:**
```json
{
    "status": "success",
    "user": {
        "username": "john_doe",
        "email": "john@example.com",
        ...
    },
    "session_info": {
        "session_id": "abc123...",
        "username": "john_doe",
        "created_at": "2026-01-09T12:00:00",
        "expiration": "2026-01-16T12:00:00",
        "is_active": true
    }
}
```

#### POST /api/auth/login
Log in an existing user.

**Request Body (JSON):**
```json
{
    "username": "john_doe",
    "password": "secret123"
}
```

**Response:**
```json
{
    "status": "success",
    "session_info": {
        "session_id": "abc123...",
        "username": "john_doe",
        "created_at": "2026-01-09T12:00:00",
        "expiration": "2026-01-16T12:00:00",
        "is_active": true
    }
}
```

**Error Response (401):**
```json
{
    "status": "error",
    "message": "ERROR: Invalid password."
}
```

#### POST /api/auth/logout
Log out a user (destroys all their active sessions).

**Request Body (JSON):**
```json
{
    "username": "john_doe"
}
```

**Response:**
```json
{
    "status": "success"
}
```

#### GET /api/auth/profile
Get a user's profile information.

**Example:**
```
GET /api/auth/profile?username=john_doe
```

**Response:**
```json
{
    "status": "success",
    "user": {
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        ...
    }
}
```

#### POST /api/auth/profile
Update a user's profile field.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | The user to update |
| `field` | string | Yes | Field to update (e.g., `email`, `city`) |
| `new-value` | string | Yes | New value for the field |

**Example:**
```
POST /api/auth/profile?username=john_doe&field=city&new-value=Toronto
```

#### POST /api/auth/delete
Delete a user account.

**Example:**
```
POST /api/auth/delete?username=john_doe
```

---

### Bookmarks

Users can bookmark businesses they want to save.

#### POST /api/bookmarks/add
Add bookmarks to a user's account.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | The user |
| `bookmarks` | string | Yes | Comma-separated business IDs |

**Example:**
```
POST /api/bookmarks/add?username=john_doe&bookmarks=123456,789012
```

#### POST /api/bookmarks/remove
Remove bookmarks from a user's account.

**Example:**
```
POST /api/bookmarks/remove?username=john_doe&bookmarks=123456
```

#### GET /api/bookmarks/get
Get a user's bookmark IDs.

**Example:**
```
GET /api/bookmarks/get?username=john_doe
```

**Response:**
```json
{
    "status": "success",
    "bookmarks": [123456, 789012, 345678]
}
```

#### GET /api/bookmarks/businesses
Get the full business objects for a user's bookmarks.

**Example:**
```
GET /api/bookmarks/businesses?username=john_doe
```

**Response:**
```json
{
    "status": "success",
    "businesses": [
        {"id": 123456, "name": "Restaurant A", ...},
        {"id": 789012, "name": "Cafe B", ...}
    ],
    "count": 2
}
```

---

### Sessions

Sessions are created automatically on login/register. You typically don't need to call these directly.

#### POST /api/session/create
Manually create a session for a user.

**Example:**
```
POST /api/session/create?username=john_doe
```

---

## Frontend Integration Guide

### Making API Calls

The server runs on `http://127.0.0.1:5000`. Here's how to make API calls from JavaScript:

#### GET Requests (Query Parameters)
For GET requests, parameters go in the URL:

```javascript
// Fetch businesses near a location
async function getBusinesses(lat, lon, radius = 10) {
    const response = await fetch(
        `http://127.0.0.1:5000/api/businesses?lat1=${lat}&lon1=${lon}&radius=${radius}`
    );
    const data = await response.json();
    return data.businesses;
}

// Get user profile
async function getProfile(username) {
    const response = await fetch(
        `http://127.0.0.1:5000/api/auth/profile?username=${username}`
    );
    return await response.json();
}
```

#### POST Requests (JSON Body)
For POST requests that need a JSON body (login, register, logout):

```javascript
// Login
async function login(username, password) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    return await response.json();
}

// Register
async function register(userData) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: userData.username,
            email: userData.email,
            phone: userData.phone,
            password: userData.password,
            'first-name': userData.firstName,
            'last-name': userData.lastName,
            city: userData.city,
            country: userData.country || 'Canada'
        })
    });
    return await response.json();
}

// Logout
async function logout(username) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username
        })
    });
    return await response.json();
}
```

#### POST Requests (Query Parameters)
Some POST endpoints use query parameters instead of JSON body:

```javascript
// Add bookmarks
async function addBookmarks(username, businessIds) {
    const bookmarks = businessIds.join(',');
    const response = await fetch(
        `http://127.0.0.1:5000/api/bookmarks/add?username=${username}&bookmarks=${bookmarks}`,
        { method: 'POST' }
    );
    return await response.json();
}
```

---

### Authentication Flow

Here's the typical auth flow for a frontend:

```
1. User opens app
   |
   v
2. Check if session exists in localStorage
   |
   +--> YES: User is logged in, show main app
   |
   +--> NO: Show login/register page
            |
            v
3. User submits login/register form
   |
   v
4. Call POST /api/auth/login or /api/auth/register
   |
   v
5. On success: Store session_info in localStorage
   |
   v
6. Redirect to main app
```

**Example implementation:**

```javascript
// On login success
function handleLoginSuccess(response) {
    if (response.status === 'success') {
        // Store session info
        localStorage.setItem('session', JSON.stringify(response.session_info));
        localStorage.setItem('username', response.session_info.username);
        
        // Redirect to main app
        window.location.href = '/dashboard';
    }
}

// Check if user is logged in
function isLoggedIn() {
    const session = localStorage.getItem('session');
    if (!session) return false;
    
    const sessionInfo = JSON.parse(session);
    const expiration = new Date(sessionInfo.expiration);
    
    // Check if session is still valid
    return sessionInfo.is_active && expiration > new Date();
}

// On logout
async function handleLogout() {
    const username = localStorage.getItem('username');
    await logout(username);
    
    localStorage.removeItem('session');
    localStorage.removeItem('username');
    
    window.location.href = '/login';
}
```

---

### Handling Responses

All API responses follow this format:

**Success:**
```json
{
    "status": "success",
    ...additional data...
}
```

**Error:**
```json
{
    "status": "error",
    "message": "Description of what went wrong"
}
```

**Example handler:**

```javascript
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.message);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error.message);
        throw error;
    }
}
```

---

### Error Handling

The API returns different HTTP status codes:

| Code | Meaning | When it happens |
|------|---------|-----------------|
| 200 | Success | Request completed successfully |
| 201 | Created | New resource created (e.g., register) |
| 400 | Bad Request | Missing required parameters |
| 401 | Unauthorized | Invalid credentials (login failed) |
| 403 | Forbidden | Access denied (e.g., reCAPTCHA failed) |
| 404 | Not Found | Resource doesn't exist (e.g., user not found) |
| 500 | Server Error | Something went wrong on the server |

**Example error handling:**

```javascript
async function login(username, password) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.status === 401) {
        // Wrong password
        showError('Invalid username or password');
        return null;
    }
    
    if (response.status === 400) {
        // Missing fields
        showError('Please fill in all fields');
        return null;
    }
    
    if (data.status === 'success') {
        return data.session_info;
    }
    
    showError(data.message || 'An error occurred');
    return null;
}
```

---

## Server File Structure

The server code is organized into blueprints for better readability:

```
backend/api/
    server.py              # Main entry point (error handlers, blueprints)
    routes/
        __init__.py        # Exports all blueprints
        auth.py            # /api/auth/* endpoints
        bookmarks.py       # /api/bookmarks/* endpoints
        businesses.py      # /api/businesses/* endpoints
        sessions.py        # /api/session/* endpoints
        users.py           # /api/user/* endpoints
        verification.py    # /api/submit-form endpoint
```

To start the server:
```bash
cd backend/api
python server.py
```

The server will run on `http://127.0.0.1:5000`.
