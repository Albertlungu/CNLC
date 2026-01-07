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