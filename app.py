from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import weasyprint
from werkzeug.utils import secure_filename
from datetime import datetime

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
    session.setdefault('photo_shape', 'circle')  # default shape
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
            'hobbies': [hobby for hobby in request.form.getlist('hobbies[]') if hobby.strip()],
            'photo_shape': request.form.get('photo_shape', 'circle')  # Save selected photo shape
        })

        # Handle file upload
        photo = request.files.get('photo')
        photo_shape = request.form.get('photo_shape')

        # If a new photo was uploaded
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png']:
                raise ValueError("Invalid image format. Only JPG/PNG allowed.")
            
            filename = secure_filename(
                f"{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            )
            photo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo.save(photo_path)
            session['photo'] = filename
            session['photo_shape'] = photo_shape or 'circle'
        else:
            # No photo uploaded this time, so remove any previous photo
            session.pop('photo', None)
            session.pop('photo_shape', None)

        # Prepare resume data
        resume = {
            **session,
            'photo_path': f"static/uploads/{session['photo']}" if 'photo' in session else None,
            'photo_shape': session.get('photo_shape', 'circle'),
            'pdf': True
        }

        # Render HTML
        html_resume = render_template(f"{session['template']}_template.html", resume=resume)

        # Generate PDF
        pdf_filename = f"resume_{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join('resumes', pdf_filename)

        weasyprint.HTML(string=html_resume, base_url='http://localhost:5000').write_pdf(pdf_path)

        print(f"PDF successfully generated at: {pdf_path}")
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"Error: {str(e)}", exc_info=True)
        return render_template("index.html", error=f"Error generating resume: {str(e)}")

@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('home'))

@app.route('/preview')
def preview():
    if 'template' not in session:
        return redirect(url_for('home'))

    resume = {
        **session,
        'photo_path': f"static/uploads/{session['photo']}" if 'photo' in session else None,
        'photo_shape': session.get('photo_shape', 'circle'),
        'pdf': False
    }

    return render_template(f"{session['template']}_template.html", resume=resume)

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
