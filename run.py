# run.py - at the root of the project
from app import create_app, create_admin_command
from app.extensions import db

app = create_app()
create_admin_command(app)

if __name__ == "__main__":
    app.run(debug=True, port=5500)