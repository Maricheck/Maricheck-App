from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from datetime import datetime
import os

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# Initialize the app with the extension
db.init_app(app)

# Status stages for crew processing
status_stages = ["Registered", "Screening", "Documents Verified", "Approved"]

# Status colors for UI
status_colors = ["secondary", "warning", "info", "success"]

# File upload helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder, prefix):
    """Save uploaded file with safe filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename with prefix
        name, ext = os.path.splitext(filename)
        safe_filename = f"{prefix}_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, safe_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file.save(file_path)
        return safe_filename
    return None

# Create tables and initialize database
with app.app_context():
    # Import models here so tables are created
    import models
    db.create_all()
    
    # Create default admin user if none exists
    from models import Admin
    if not Admin.query.first():
        default_admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin created: username='admin', password='admin123'")


# Helper function to check if user is logged in as admin
def is_admin_logged_in():
    return session.get('admin_logged_in', False)


# Helper function to require admin login
def require_admin():
    if not is_admin_logged_in():
        flash('Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('admin_login'))

@app.route('/')
def public_home():
    """Public home page for crew members - DEFAULT LANDING PAGE"""
    return render_template('public_home.html')

@app.route('/admin')
@app.route('/admin/dashboard') 
def dashboard():
    """Administrative dashboard showing all crew members and staff"""
    # Check if admin is logged in
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get all crew members and staff from database
    from models import CrewMember, StaffMember
    crew_members = CrewMember.query.order_by(CrewMember.created_at.desc()).all()
    staff_members = StaffMember.query.order_by(StaffMember.created_at.desc()).all()
    
    # Calculate statistics
    total_registrations = len(crew_members) + len(staff_members)
    crew_in_screening = len([c for c in crew_members if c.status == 1])
    staff_in_screening = len([s for s in staff_members if s.status == 1])
    approved_profiles = len([c for c in crew_members if c.status == 3]) + len([s for s in staff_members if s.status == 3])
    
    # Group by status for easy display
    crew_by_status = {
        'screening': [c for c in crew_members if c.status == 1],
        'approved': [c for c in crew_members if c.status == 3]
    }
    staff_by_status = {
        'screening': [s for s in staff_members if s.status == 1],
        'approved': [s for s in staff_members if s.status == 3]
    }
    
    return render_template('dashboard.html', 
                         crew=crew_members,
                         staff=staff_members,
                         crew_by_status=crew_by_status,
                         staff_by_status=staff_by_status,
                         stats={
                             'total_registrations': total_registrations,
                             'crew_in_screening': crew_in_screening,
                             'staff_in_screening': staff_in_screening,
                             'approved_profiles': approved_profiles
                         },
                         stages=status_stages,
                         colors=status_colors)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Crew member registration form - PUBLIC ACCESS"""
    if request.method == 'POST':
        # Server-side validation
        name = request.form.get('name', '').strip()
        rank = request.form.get('rank', '').strip()
        passport = request.form.get('passport', '').strip()
        nationality = request.form.get('nationality', '').strip()
        dob = request.form.get('date_of_birth', '')
        years_exp = request.form.get('years_experience', '')
        vessel_type = request.form.get('last_vessel_type', '').strip()
        availability = request.form.get('availability_date', '')
        
        # Validate required fields
        if not name or not rank or not passport:
            flash('Name, rank, and passport are required fields.', 'danger')
            return render_template('register.html')
        
        # Check for duplicate passport in database
        from models import CrewMember
        existing_crew = CrewMember.query.filter_by(passport=passport.upper()).first()
        if existing_crew:
            flash('A crew member with this passport number already exists.', 'danger')
            return render_template('register.html')
        
        # Convert dates and numbers
        date_of_birth = None
        availability_date = None
        years_experience = None
        
        try:
            if dob:
                date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            if availability:
                availability_date = datetime.strptime(availability, '%Y-%m-%d').date()
            if years_exp:
                years_experience = int(years_exp)
        except ValueError:
            flash('Please check date formats and numeric values.', 'danger')
            return render_template('register.html')
        
        # Handle file uploads
        passport_file = save_uploaded_file(request.files.get('passport_file'), 'crew', f"{name.replace(' ', '_')}_passport")
        cdc_file = save_uploaded_file(request.files.get('cdc_file'), 'crew', f"{name.replace(' ', '_')}_cdc")
        resume_file = save_uploaded_file(request.files.get('resume_file'), 'crew', f"{name.replace(' ', '_')}_resume")
        photo_file = save_uploaded_file(request.files.get('photo_file'), 'crew', f"{name.replace(' ', '_')}_photo")
        
        # Create new crew member
        new_crew = CrewMember(
            name=name,
            rank=rank,
            passport=passport.upper(),
            nationality=nationality,
            date_of_birth=date_of_birth,
            years_experience=years_experience,
            last_vessel_type=vessel_type,
            availability_date=availability_date,
            passport_file=passport_file,
            cdc_file=cdc_file,
            resume_file=resume_file,
            photo_file=photo_file,
            status=0  # Start at "Registered"
        )
        db.session.add(new_crew)
        db.session.commit()
        
        flash('Registration completed successfully!', 'success')
        return render_template('thankyou.html', crew=new_crew, stages=status_stages)
    
    return render_template('register.html')

@app.route('/register-staff', methods=['GET', 'POST'])
def register_staff():
    """Staff member registration form - PUBLIC ACCESS"""
    if request.method == 'POST':
        # Server-side validation
        full_name = request.form.get('full_name', '').strip()
        email_or_whatsapp = request.form.get('email_or_whatsapp', '').strip()
        position_applying = request.form.get('position_applying', '').strip()
        department = request.form.get('department', '').strip()
        years_exp = request.form.get('years_experience', '')
        current_employer = request.form.get('current_employer', '').strip()
        location = request.form.get('location', '').strip()
        availability = request.form.get('availability_date', '')
        
        # Validate required fields
        if not full_name or not email_or_whatsapp or not position_applying or not department:
            flash('Name, contact, position, and department are required fields.', 'danger')
            return render_template('register_staff.html')
        
        # Convert dates and numbers
        availability_date = None
        years_experience = None
        
        try:
            if availability:
                availability_date = datetime.strptime(availability, '%Y-%m-%d').date()
            if years_exp:
                years_experience = int(years_exp)
        except ValueError:
            flash('Please check date formats and numeric values.', 'danger')
            return render_template('register_staff.html')
        
        # Handle file uploads
        resume_file = save_uploaded_file(request.files.get('resume_file'), 'staff', f"{full_name.replace(' ', '_')}_resume")
        photo_file = save_uploaded_file(request.files.get('photo_file'), 'staff', f"{full_name.replace(' ', '_')}_photo")
        
        # Create new staff member
        from models import StaffMember
        new_staff = StaffMember(
            full_name=full_name,
            email_or_whatsapp=email_or_whatsapp,
            position_applying=position_applying,
            department=department,
            years_experience=years_experience,
            current_employer=current_employer,
            location=location,
            availability_date=availability_date,
            resume_file=resume_file,
            photo_file=photo_file,
            status=1  # Start at "Screening"
        )
        db.session.add(new_staff)
        db.session.commit()
        
        flash('Staff registration completed successfully!', 'success')
        return render_template('thankyou_staff.html', staff=new_staff)
    
    return render_template('register_staff.html')

@app.route('/uploads/<folder>/<filename>')
def download_file(folder, filename):
    """Secure file download route"""
    # Check if admin is logged in for file downloads
    redirect_response = require_admin()
    if redirect_response:
        flash('Admin access required to download files.', 'warning')
        return redirect(url_for('admin_login'))
    
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename)

@app.route('/update_status/<int:crew_id>')
def update_status(crew_id):
    """Update crew member status to next stage - ADMIN ONLY"""
    # Check if admin is logged in
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    try:
        from models import CrewMember
        crew_member = CrewMember.query.get_or_404(crew_id)
        
        if crew_member.status < len(status_stages) - 1:
            crew_member.status += 1
            db.session.commit()
            flash(f"Status updated to {status_stages[crew_member.status]} for {crew_member.name}", 'success')
        else:
            flash('Crew member is already at final status.', 'info')
            
    except Exception as e:
        flash('Error updating status.', 'danger')
        db.session.rollback()
    
    return redirect(url_for('dashboard'))

@app.route('/track', methods=['GET', 'POST'])
def track():
    """Public tracking interface using passport numbers - PUBLIC ACCESS"""
    if request.method == 'POST':
        passport = request.form.get('passport', '').strip().upper()
        
        if not passport:
            flash('Please enter a passport number.', 'warning')
            return render_template('tracker.html', crew=None, stages=status_stages)
        
        # Search for crew member in database
        from models import CrewMember
        crew_member = CrewMember.query.filter_by(passport=passport).first()
        
        if crew_member:
            return render_template('tracker.html', 
                                 crew=crew_member, 
                                 stages=status_stages,
                                 colors=status_colors)
        
        # Not found
        flash('No crew member found with this passport number.', 'danger')
        return render_template('tracker.html', crew=None, stages=status_stages, not_found=True)
    
    return render_template('tracker.html', crew=None, stages=status_stages)


# NEW ADMIN AUTHENTICATION ROUTES

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('admin_login.html')
        
        # Check admin credentials
        from models import Admin
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('admin_login.html')
    
    # If already logged in, redirect to dashboard
    if is_admin_logged_in():
        return redirect(url_for('dashboard'))
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public_home'))

@app.route('/profile/crew/<int:crew_id>')
def crew_profile(crew_id):
    """View detailed crew member profile - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import CrewMember
    crew = CrewMember.query.get_or_404(crew_id)
    return render_template('crew_profile.html', crew=crew, stages=status_stages, colors=status_colors)

@app.route('/profile/staff/<int:staff_id>')
def staff_profile(staff_id):
    """View detailed staff member profile - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import StaffMember
    staff = StaffMember.query.get_or_404(staff_id)
    return render_template('staff_profile.html', staff=staff)

@app.route('/approve/crew/<int:crew_id>')
def approve_crew(crew_id):
    """Approve crew member - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import CrewMember
    crew = CrewMember.query.get_or_404(crew_id)
    crew.status = 3  # Approved
    db.session.commit()
    flash(f'Crew member {crew.name} has been approved!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reject/crew/<int:crew_id>')
def reject_crew(crew_id):
    """Reject crew member - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import CrewMember
    crew = CrewMember.query.get_or_404(crew_id)
    crew.status = -1  # Rejected
    db.session.commit()
    flash(f'Crew member {crew.name} has been rejected.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/approve/staff/<int:staff_id>')
def approve_staff(staff_id):
    """Approve staff member - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import StaffMember
    staff = StaffMember.query.get_or_404(staff_id)
    staff.status = 3  # Approved
    db.session.commit()
    flash(f'Staff member {staff.full_name} has been approved!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reject/staff/<int:staff_id>')
def reject_staff(staff_id):
    """Reject staff member - ADMIN ONLY"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    from models import StaffMember
    staff = StaffMember.query.get_or_404(staff_id)
    staff.status = -1  # Rejected
    db.session.commit()
    flash(f'Staff member {staff.full_name} has been rejected.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/home')
def home_redirect():
    """Redirect /home to public home for backward compatibility"""
    return redirect(url_for('public_home'))





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
