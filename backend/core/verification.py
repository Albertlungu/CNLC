"""
./backend/core/verification.py

Uses Google's reCAPTCHA (subtle mouse movements) to complete to verify that they are human.
"""

import requests
import json

from typing import Any

def verify_recaptcha(
        response_token,
        secret_key,
        user_ip
        ) -> Any:

    verification_url = "https://www.google.com/recaptcha/api/siteverify"
    params = {
        'secret': secret_key,
        'response': response_token,
        'remoteip': user_ip
    }

    try:
        resp = requests.post(verification_url, data=params)
        result = resp.json()

        if result.get('success'):
            if 'score' in result:
                score = result.get('score')
                if score >= 0.5:
                    return True, "reCAPTCHA verified successfully"
                else:
                    return False, f"reCAPTCHA score too low: {score}"
            return True, "reCAPTCHA verified successfully"
        else:
            error_codes = result.get("error-codes", ["Unspecified error"])
            return False, f"reCAPTCHA failed. Error codes: {error_codes}"

    except requests.exceptions.RequestException as e:
        return False, f"Network error during reCAPTCHA verification: {e}"