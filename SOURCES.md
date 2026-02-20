# Sources

All external libraries, APIs, tools, and resources used in this project.

---

## Python Libraries

| Package | Purpose | License | Link |
|---|---|---|---|
| Flask | Web framework / REST API server | BSD-3-Clause | https://flask.palletsprojects.com/ |
| Flask-CORS | Cross-Origin Resource Sharing support for Flask | MIT | https://github.com/corydolphin/flask-cors |
| Flask-Limiter | Rate limiting for Flask routes | MIT | https://github.com/alisaifee/flask-limiter |
| Pydantic | Data validation and serialization using Python type hints | MIT | https://docs.pydantic.dev/ |
| pydantic-extra-types | Additional types for Pydantic (phone numbers, etc.) | MIT | https://github.com/pydantic/pydantic-extra-types |
| phonenumbers | Phone number parsing and validation (used with Pydantic) | Apache-2.0 | https://github.com/daviddrysdale/python-phonenumbers |
| bcrypt | Password hashing | Apache-2.0 | https://github.com/pyca/bcrypt |
| FuzzyWuzzy | Fuzzy string matching using Levenshtein distance | GPL-2.0 | https://github.com/seatgeek/fuzzywuzzy |
| python-Levenshtein | Fast Levenshtein distance computation (C extension for FuzzyWuzzy) | GPL-2.0 | https://github.com/maxbachmann/python-Levenshtein |
| python-dateutil | Date/time parsing and manipulation utilities | Apache-2.0 / BSD | https://github.com/dateutil/dateutil |
| requests | HTTP client library | Apache-2.0 | https://docs.python-requests.org/ |
| numpy | Numerical computing | BSD-3-Clause | https://numpy.org/ |
| python-dotenv | Load environment variables from `.env` files | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| google-genai | Google Generative AI SDK (Gemini API) | Apache-2.0 | https://github.com/googleapis/python-genai |
| google-auth | Google authentication library | Apache-2.0 | https://github.com/googleapis/google-auth-library-python |
| google-auth-oauthlib | OAuth 2.0 integration for Google APIs | Apache-2.0 | https://github.com/googleapis/google-auth-library-python-oauthlib |
| google-api-python-client | Google API client library (Calendar API) | Apache-2.0 | https://github.com/googleapis/google-api-python-client |
| opencv-python | Computer vision (frame extraction for 3D scan pipeline) | Apache-2.0 | https://github.com/opencv/opencv-python |
| Pillow | Image processing | HPND | https://python-pillow.org/ |
| trimesh | 3D mesh loading and GLB export | MIT | https://github.com/mikedh/trimesh |
| ddgs | DuckDuckGo search (web search, image search, deal scraping) | MIT | https://github.com/deedy5/duckduckgo_search |
| pytest | Testing framework | MIT | https://docs.pytest.org/ |
| pytest-cov | Code coverage plugin for pytest | MIT | https://github.com/pytest-dev/pytest-cov |

---

## JavaScript / Node.js Libraries

| Package | Purpose | License | Link |
|---|---|---|---|
| Electron | Desktop application shell (Chromium + Node.js) | MIT | https://www.electronjs.org/ |

---

## Frontend Libraries (CDN / Bundled)

| Library | Purpose | License | Link |
|---|---|---|---|
| Leaflet.js | Interactive maps for business location display | BSD-2-Clause | https://leafletjs.com/ |

---

## External APIs and Services

| Service | Purpose | Link |
|---|---|---|
| Overpass API (OpenStreetMap) | Bulk-fetching real business data (shops, restaurants, cafes) for Canadian cities | https://overpass-api.de/ |
| OpenStreetMap | Underlying geographic data and map tiles | https://www.openstreetmap.org/ |
| Google Gemini 1.5 Flash | AI-powered business recommendations and conversational agent with function calling | https://ai.google.dev/ |
| Google Calendar API | OAuth 2.0 calendar integration (read/write events, sync reservations) | https://developers.google.com/calendar |
| Google reCAPTCHA v3 | Bot prevention on authentication forms | https://developers.google.com/recaptcha |
| DuckDuckGo Search | Web search (AI agent), image search (business photos), deal scraping | https://duckduckgo.com/ |

---

## External Tools (Optional)

| Tool | Purpose | License | Link |
|---|---|---|---|
| COLMAP | Structure-from-Motion and Multi-View Stereo for 3D reconstruction | BSD-3-Clause | https://colmap.github.io/ |
| OpenMVS | Dense reconstruction and mesh generation from SfM output | AGPL-3.0 | https://github.com/cdcseacave/openMVS |

---

## Data Sources

| Source | Usage | License |
|---|---|---|
| OpenStreetMap contributors | Business names, addresses, categories, coordinates, and metadata for Canadian cities | ODbL (Open Data Commons Open Database License) |

---

## References and Documentation

| Resource | Used For |
|---|---|
| [Flask Documentation](https://flask.palletsprojects.com/) | Backend REST API design and implementation |
| [Pydantic Documentation](https://docs.pydantic.dev/) | Data model validation |
| [Electron Documentation](https://www.electronjs.org/docs) | Desktop application shell and IPC |
| [Overpass API Documentation](https://wiki.openstreetmap.org/wiki/Overpass_API) | Querying OpenStreetMap for business data |
| [Google Gemini API Documentation](https://ai.google.dev/docs) | AI recommendations and function-calling agent |
| [Google Calendar API Documentation](https://developers.google.com/calendar/api) | Calendar OAuth flow and event management |
| [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha/docs/v3) | Bot prevention integration |
| [Leaflet.js Documentation](https://leafletjs.com/reference.html) | Interactive map rendering |
| [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula) | Distance calculation between geographic coordinates |
| [COLMAP Documentation](https://colmap.github.io/tutorial.html) | 3D reconstruction pipeline setup |
| [OpenMVS Wiki](https://github.com/cdcseacave/openMVS/wiki) | Dense reconstruction and mesh export |
| [ICS File Format (RFC 5545)](https://datatracker.ietf.org/doc/html/rfc5545) | Calendar file generation for reservation downloads |
