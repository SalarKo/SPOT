from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import validators

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# File storage for URLs
URL_STORAGE_FILE = 'urls.txt'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle file uploads
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            flash('File successfully uploaded!', 'success')
            return redirect(url_for('home'))

    # Handle URL submission
    ad_link = request.form.get('adLink')
    if ad_link:
        if validators.url(ad_link):
            try:
                with open(URL_STORAGE_FILE, 'a') as file:
                    file.write(ad_link + '\n')
                flash('Link submitted successfully!', 'success')
                return redirect(url_for('home'))
            except Exception as e:
                flash(f'Error saving the URL: {e}', 'danger')
                return redirect(url_for('home'))
        else:
            flash('Invalid URL format. Please provide a correct URL.', 'danger')
            return redirect(url_for('home'))

    flash('No file or link provided.', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
