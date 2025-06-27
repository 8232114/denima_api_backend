"""
WSGI middleware for CORS handling
This ensures CORS headers are set at the WSGI level, bypassing any Flask issues
"""

class CORSMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def new_start_response(status, response_headers):
            # Add CORS headers to every response
            cors_headers = [
                ("Access-Control-Allow-Origin", "https://denimahub.netlify.app"),
                ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With"),
                ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
                ("Access-Control-Allow-Credentials", "true"),
            ]
            
            # Remove any existing CORS headers to avoid duplicates
            filtered_headers = [
                (name, value) for name, value in response_headers
                if not name.lower().startswith("access-control-")
            ]
            
            # Add our CORS headers
            filtered_headers.extend(cors_headers)
            
            return start_response(status, filtered_headers)

        # Handle OPTIONS requests at WSGI level
        if environ.get("REQUEST_METHOD") == "OPTIONS":
            response_headers = [
                ("Content-Type", "text/plain"),
                ("Access-Control-Allow-Origin", "https://denimahub.netlify.app"),
                ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With"),
                ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
                ("Access-Control-Allow-Credentials", "true"),
            ]
            start_response("200 OK", response_headers)
            return [b""]

        return self.app(environ, new_start_response)


# Import the Flask app
from src.main import create_app

# Create the Flask app
app = create_app()

# Wrap with CORS middleware
application = CORSMiddleware(app)

if __name__ == "__main__":
    # For development
    app.run(host="0.0.0.0", port=5000, debug=True)



