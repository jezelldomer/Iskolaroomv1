from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from supabase import create_client
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Supabase Initialization
SUPABASE_URL = "https://onwqxmbacuatnbsiahba.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ud3F4bWJhY3VhdG5ic2lhaGJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDI3MTQxOSwiZXhwIjoyMDQ5ODQ3NDE5fQ.HCCbLwRrJ54G6CGLLRb7xpqZy7o7XL4A9Y6L8G8HbVA"
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/dates')
@login_required
def dates():
    room = request.args.get('room')  # Get the room parameter from the query string
    return render_template('dates.html', room=room)  # Pass the room to the template

@app.route('/folders', methods=['GET'])
@login_required
def get_folders():
    response = supabase.table("images").select("date").execute()
    folders = {row["date"] for row in response.data if row.get("date")}

    # Sort the folders in ascending order (earliest to latest)
    sorted_folders = sorted(folders)

    # Format dates to "Month DD, YYYY"
    formatted_folders = [datetime.strptime(folder, "%Y-%m-%d").strftime("%B %d, %Y") for folder in sorted_folders]
    return jsonify(formatted_folders)

@app.route('/folder/<date>', methods=['GET'])
@login_required
def folder(date):
    if not date or date == "undefined":
        return "Invalid date parameter", 400

    # Convert "Month DD, YYYY" back to "YYYY-MM-DD"
    original_date = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")

    response = supabase.table("images").select("*").eq("date", original_date).execute()
    files = response.data or []

    # Format times for each file
    for file in files:
        if 'time' in file:  # Assuming a 'time' field exists in your Supabase table
            normalized_time = file['time'].replace('-', ':')
            try:
                file['formatted_time'] = datetime.strptime(normalized_time, "%H:%M:%S").strftime("%I:%M:%S %p")
            except ValueError:
                file['formatted_time'] = "Invalid Time Format"
    
    return render_template('captures.html', files=files, date=date)

# Dynamic room page route
@app.route('/room_<int:room_number>')
@login_required
def room(room_number):
    # Fetch data related to the specific room
    room_data = supabase.table("rooms").select("*").eq("room_number", room_number).execute()

    # Check if room data exists
    if room_data.data:
        room_details = room_data.data[0]  # Assuming room data contains details like name, description, etc.
        room_content = room_details.get('content', 'No content available')  # Default message if no content is provided
    else:
        room_content = "Room not found"

    # Return a dynamic page for the room with room_content rendered directly
    return render_template('room_page.html', room_number=room_number, room_content=room_content)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)
