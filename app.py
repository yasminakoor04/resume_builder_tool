from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import weasyprint
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('resumes', exist_ok=True)

@app.route('/')
def home():
    # Initialize session variables
    session.setdefault('contact', [])
    session.setdefault('experience', [])
    session.setdefault('hobbies', [])
    return render_template('index.html')

@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        # Store form data in session
        session.update({
            'template': request.form['template'],
            'name': request.form['name'],
            'job_title': request.form['job_title'],
            'experience': [exp for exp in request.form.getlist('experience[]') if exp.strip()],
            'education': request.form.get('education', 'Not specified'),
            'skills': request.form.get('skills', 'Not specified'),
            'profile': request.form.get('profile', ''),
            'contact': [cont for cont in request.form.getlist('contact[]') if cont.strip()],
            'activities': [act for act in request.form.getlist('activities[]') if act.strip()],
            'hobbies': [hobby for hobby in request.form.getlist('hobbies[]') if hobby.strip()]
        })

        # Handle file upload
        photo_path = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and photo.filename != '':
                # Generate secure filename
                ext = os.path.splitext(photo.filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png']:
                    raise ValueError("Invalid image format. Only JPG/PNG allowed.")
                
                filename = secure_filename(
                    f"{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                )
                photo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo.save(photo_path)
                session['photo'] = filename
                print(f"Saved photo to: {photo_path}")

        # Prepare resume data with relative path for WeasyPrint
        resume = {
        **session,
        'photo_path': f"static/uploads/{session['photo']}" if 'photo' in session else None,  # Use relative path for Flask
        'photo_local_path': photo_path if photo_path else None,
        'pdf': True  # Flag to indicate PDF generation context
    }

        # Generate HTML
        html_resume = render_template(f"{session['template']}_template.html", resume=resume)

        # Generate PDF
        pdf_filename = f"resume_{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join('resumes', pdf_filename)
        
        # Convert HTML to PDF with base_url to resolve local paths
        weasyprint.HTML(
        string=html_resume,
        base_url='http://localhost:5000'  # Ensure absolute URLs are resolved correctly
        ).write_pdf(pdf_path)
        
        print(f"PDF successfully generated at: {pdf_path}")
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"Error: {str(e)}", exc_info=True)
        return render_template("index.html", error=f"Error generating resume: {str(e)}")

@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)