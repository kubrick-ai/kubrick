import os
from app import create_app

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == "__main__":
    if config_name == "production":
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)