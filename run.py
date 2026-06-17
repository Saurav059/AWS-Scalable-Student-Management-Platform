import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

# Build application factory
app = create_app()

if __name__ == '__main__':
    # Retrieve port and debug configurations
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting local server on http://127.0.0.1:{port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
