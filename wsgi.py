import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    # For local development - don't use app.run for production deployment
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"], host=app.config["HOST"])
