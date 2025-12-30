from flask import Flask

# Initialize the Flask application
app = Flask(__name__)


# Define the main route (Home Page)
@app.route("/")
def home():
    return "VitalMine System Running - Phase 2 Complete"


# Run the app in debug mode (auto-reloads when you change code)
if __name__ == "__main__":
    app.run(debug=True)
