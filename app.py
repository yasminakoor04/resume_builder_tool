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
        
        # Get lists of dynamic fields and filter out empty strings
        session['experience'] = [exp for exp in request.form.getlist('experience[]') if exp.strip()]
        session['education'] = request.form['education']
        session['skills'] = request.form['skills']
        session['profile'] = request.form['profile']
        
        session['contact'] = [cont for cont in request.form.getlist('contact[]') if cont.strip()]
        session['activities'] = [activity for activity in request.form.getlist('activities[]') if activity.strip()]
        session['hobbies'] = [hobby for hobby in request.form.getlist('hobbies[]') if hobby.strip()]

        # Handle the profile picture upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '':
                # Save the uploaded photo to the 'uploads' folder
                photo_filename = f"{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo.save(photo_path)
                session['photo'] = photo_filename

        # Create the resume dictionary with all sections
        resume = {
            'template': session.get('template'),
            'name': session.get('name'),
            'job_title': session.get('job_title'),
            'experience': session.get('experience'),
            'education': session.get('education'),
            'skills': session.get('skills'),
            'profile': session.get('profile'),
            'contact': session.get('contact'),
            'activities': session.get('activities'),
            'hobbies': session.get('hobbies'),
            'photo': session.get('photo')  # Pass the photo filename to the template
        }

        # Load the appropriate HTML template based on the selected template
        html_template = f"{session['template']}_template.html"

        # Render the HTML with the resume data
        html_resume = render_template(html_template, resume=resume)

        # Generate the filename for the PDF
        filename = f"resume_{session['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join('resumes', filename)

        # Convert HTML to PDF using WeasyPrint
        weasyprint.HTML(string=html_resume).write_pdf(pdf_path)

        # Return the generated PDF as a download
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print("Error:", e)
        return render_template("index.html", error="An error occurred while generating the resume.")

@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
