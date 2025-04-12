from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import weasyprint
from datetime import datetime

app = Flask(__name__)

# Set the secret key for sessions (make sure it's a secret key)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Define the folder for uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    # Initialize session variables if they don't exist
    if 'contact' not in session:
        session['contact'] = []
    if 'experience' not in session:
        session['experience'] = []
    if 'hobbies' not in session:
        session['hobbies'] = []

    return render_template('index.html')

@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        # Get form data and store it in the session
        session['template'] = request.form['template']
        session['name'] = request.form['name']
        session['job_title'] = request.form['job_title']
        
        # Get all form fields with proper defaults
        session['experience'] = [exp for exp in request.form.getlist('experience[]') if exp.strip()]
        session['education'] = request.form.get('education', 'Not specified')
        session['skills'] = request.form.get('skills', 'Not specified')
        session['profile'] = request.form.get('profile', '')
        
        session['contact'] = [cont for cont in request.form.getlist('contact[]') if cont.strip()]
        session['activities'] = [activity for activity in request.form.getlist('activities[]') if activity.strip()]
        session['hobbies'] = [hobby for hobby in request.form.getlist('hobbies[]') if hobby.strip()]

        # Debug print to check received data
        print("Received form data:", {
            'name': session['name'],
            'job_title': session['job_title'],
            'experience': session['experience'],
            'education': session['education'],
            'skills': session['skills'],
            'profile': session['profile'],
            'contact': session['contact'],
            'activities': session['activities'],
            'hobbies': session['hobbies']
        })

        # Handle the profile picture upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '':
                photo_filename = f"{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo.save(photo_path)
                session['photo'] = photo_filename
                print(f"Photo saved to: {photo_path}")

        # Create the resume dictionary with defaults
        resume = {
            'template': session.get('template'),
            'name': session.get('name', 'Your Name'),
            'job_title': session.get('job_title', 'Professional'),
            'experience': session.get('experience', ['Experience not specified']),
            'education': session.get('education', 'Education not specified'),
            'skills': session.get('skills', 'Skills not specified'),
            'profile': session.get('profile', ''),
            'contact': session.get('contact', ['Contact information not provided']),
            'activities': session.get('activities', []),
            'hobbies': session.get('hobbies', []),
            'photo': session.get('photo')
        }

        # Debug the resume data being passed to template
        print("Resume data being passed to template:", resume)

        # Load the appropriate HTML template
        html_template = f"{session['template']}_template.html"
        html_resume = render_template(html_template, resume=resume)

        # Debug: Save the generated HTML to inspect it
        debug_html_path = os.path.join('resumes', 'debug_resume.html')
        with open(debug_html_path, 'w') as f:
            f.write(html_resume)
        print(f"Debug HTML saved to: {debug_html_path}")

        # Generate PDF
        filename = f"resume_{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join('resumes', filename)
        
        print(f"Attempting to generate PDF at: {pdf_path}")
        weasyprint.HTML(string=html_resume).write_pdf(pdf_path)
        print("PDF generation successful!")

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"Error generating resume: {str(e)}", exc_info=True)
        return render_template("index.html", error=f"Failed to generate resume: {str(e)}")


@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
