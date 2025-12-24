import os
import json
import io
from flask import Flask, render_template, jsonify, request, send_file
from config import MEDIA_ASSIGNMENT_JSON, INPUT_FOLDER
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

app = Flask(__name__)

# Ensure we can serve files from the input folder
# We'll use a custom route for this to handle absolute paths safely-ish for this local tool

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    if not os.path.exists(MEDIA_ASSIGNMENT_JSON):
        return jsonify({})
    
    with open(MEDIA_ASSIGNMENT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Sort by date
    sorted_data = dict(sorted(data.items()))
    return jsonify(sorted_data)

@app.route('/api/save', methods=['POST'])
def save_data():
    new_data = request.json
    try:
        # Validate structure roughly? Or just save.
        # The user wants to modify assignments.
        # We should probably backup the old one first?
        if os.path.exists(MEDIA_ASSIGNMENT_JSON):
            import shutil
            shutil.copy2(MEDIA_ASSIGNMENT_JSON, MEDIA_ASSIGNMENT_JSON + ".bak")
            
        with open(MEDIA_ASSIGNMENT_JSON, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            
        return jsonify({"status": "success", "message": "Data saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/media')
def serve_media():
    # Security note: This is a local tool, so we allow serving files from the system
    # The JSON has absolute paths, so we serve directly from those paths.
    
    file_path = request.args.get('path')
    if not file_path:
        return "No path provided", 400
        
    # Normalize path
    file_path = os.path.normpath(file_path)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Check if it's a HEIC file and convert to JPEG for browser compatibility
    if file_path.lower().endswith('.heic'):
        if not HEIF_SUPPORT:
            return "HEIC support not available. Install pillow-heif.", 500
            
        try:
            # Open HEIC and convert to JPEG
            img = Image.open(file_path)
            
            # Convert to RGB if necessary (HEIC might have alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create a thumbnail (max 800px on longest side for performance)
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save to bytes buffer as JPEG
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/jpeg')
        except Exception as e:
            return f"Error converting HEIC: {str(e)}", 500
        
    # For all other file types, serve directly
    return send_file(file_path)

if __name__ == '__main__':
    print("Starting Media Validator UI...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
