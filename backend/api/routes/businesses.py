"""
./backend/api/routes/businesses.py

Business-related API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.core.business_manager as buis
import backend.storage.json_handler as jh

businesses_bp = Blueprint("businesses", __name__, url_prefix="/api/businesses")


@businesses_bp.route("", methods=["GET"])
def get_businesses() -> Response:
    """
    RESTful endpoint: GET /api/businesses
    """
    search_query = request.args.get("search", type=str)
    category = request.args.get("category", type=str)
    filepath = request.args.get("filepath", "data/businesses.json", type=str)
    radius = request.args.get("radius", 10, type=int)
    lat1 = request.args.get("lat1", type=float)
    lon1 = request.args.get("lon1", type=float)
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 30, type=int)

    try:
        results = jh.load_businesses(input_filepath=filepath)

        if lat1 and lon1:
            if radius != 0:
                results = buis.filter_by_radius(results, radius, lat1, lon1)
            else:
                resp = jsonify({"error": "Radius must be nonzero"})
                return make_response(resp, 400)

        if category:
            results = buis.filter_by_category(results, category)

        if search_query:
            results = buis.search_by_name(results, search_query)

        total_count = len(results)
        results = results[offset : offset + limit]

        resp = jsonify(
            {
                "status": "success",
                "businesses": results,
                "count": len(results),
                "total": total_count,
            }
        )
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"error": str(e)})
        return make_response(resp, 500)


@businesses_bp.route("/<int:business_id>", methods=["GET"])
def get_business_by_id(business_id: int) -> Response:
    """
    RESTful endpoint: GET /api/businesses/<id>

    Returns a single business by its ID.
    """
    results = jh.load_businesses()
    try:
        results = buis.search_by_id(results, business_id=business_id)

        resp = jsonify(
            {
                "business": results[0] if results else None,
            }
        )
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"error": str(e)})
        return make_response(resp, 500)
