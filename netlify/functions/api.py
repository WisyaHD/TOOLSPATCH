import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import app

def handler(event, context):
    """Netlify Functions handler for Flask app"""
    
    # Build environ dict for WSGI app
    environ = {
        "REQUEST_METHOD": event["httpMethod"],
        "SCRIPT_NAME": "",
        "PATH_INFO": event["path"],
        "QUERY_STRING": event.get("queryStringParameters", {}),
        "CONTENT_TYPE": event["headers"].get("content-type", ""),
        "CONTENT_LENGTH": event["headers"].get("content-length", ""),
        "SERVER_NAME": event["headers"].get("host", "localhost"),
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": None,
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    
    # Add headers to environ
    for header, value in event.get("headers", {}).items():
        header = header.upper().replace("-", "_")
        if header not in ["CONTENT_TYPE", "CONTENT_LENGTH"]:
            header = f"HTTP_{header}"
        environ[header] = value
    
    # Handle body
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    else:
        body = body.encode("utf-8") if isinstance(body, str) else body
    
    environ["wsgi.input"] = io.BytesIO(body)
    
    # Capture response
    status = None
    response_headers = []
    
    def start_response(status_str, headers):
        nonlocal status, response_headers
        status = int(status_str.split(" ")[0])
        response_headers = headers
        return lambda x: None
    
    # Call WSGI app
    response_data = app(environ, start_response)
    
    # Build response
    body = b"".join(response_data)
    
    return {
        "statusCode": status or 500,
        "headers": {header[0]: header[1] for header in response_headers},
        "body": body.decode("utf-8") if isinstance(body, bytes) else body,
        "isBase64Encoded": False,
    }
