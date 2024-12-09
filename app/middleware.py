from flask import request, jsonify
import jwt
import os
from functools import wraps

SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")

def role_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Periksa apakah header Authorization ada
            token = request.headers.get("Authorization")
            if not token:
                return jsonify({"message": "Token is missing."}), 401

            # Ambil token setelah "Bearer"
            try:
                token = token.split()[1]
            except IndexError:
                return jsonify({"message": "Token format is invalid."}), 401

            # Decode dan validasi token
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if "role" not in payload:
                    return jsonify({"message": "Role not found in token."}), 403
                if payload["role"] not in roles:
                    return jsonify({"message": "Access denied. Insufficient role permissions."}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token has expired."}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({"message": "Invalid token.", "error": str(e)}), 401
            except Exception as e:
                return jsonify({"message": "An error occurred while validating token.", "error": str(e)}), 401

            # Jika semua validasi berhasil, jalankan fungsi
            return func(*args, **kwargs)
        return wrapper
    return decorator
