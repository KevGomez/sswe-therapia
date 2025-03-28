import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=int(os.environ.get("FLASK_PORT", "5001")),
        debug=os.environ.get("FLASK_DEBUG", "True").lower() in ["true", "1", "t"]
    )
