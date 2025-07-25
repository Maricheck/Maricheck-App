from app import db
from datetime import datetime


class Admin(db.Model):
    """Admin user model for dashboard access"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class CrewMember(db.Model):
    """Crew member model for registration and tracking"""
    __tablename__ = 'crew_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    rank = db.Column(db.String(64), nullable=False)
    passport = db.Column(db.String(32), unique=True, nullable=False)
    
    # New fields
    nationality = db.Column(db.String(64))
    date_of_birth = db.Column(db.Date)
    years_experience = db.Column(db.Integer)
    last_vessel_type = db.Column(db.String(128))
    availability_date = db.Column(db.Date)
    
    # File upload fields
    passport_file = db.Column(db.String(255))
    cdc_file = db.Column(db.String(255))
    resume_file = db.Column(db.String(255))
    photo_file = db.Column(db.String(255))
    
    status = db.Column(db.Integer, default=0)  # 0-3 for status stages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CrewMember {self.name} ({self.passport})>'
    
    def get_status_name(self):
        """Get the human-readable status name"""
        status_names = ["Registered", "Screening", "Documents Verified", "Approved"]
        return status_names[self.status] if 0 <= self.status < len(status_names) else "Unknown"


class StaffMember(db.Model):
    """Staff member model for offshore/office staff registration"""
    __tablename__ = 'staff_members'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    email_or_whatsapp = db.Column(db.String(128), nullable=False)
    position_applying = db.Column(db.String(128), nullable=False)
    department = db.Column(db.String(32), nullable=False)  # Ops, HR, Tech, Crewing
    years_experience = db.Column(db.Integer)
    current_employer = db.Column(db.String(128))
    location = db.Column(db.String(128))
    availability_date = db.Column(db.Date)
    
    # File upload fields
    resume_file = db.Column(db.String(255))
    photo_file = db.Column(db.String(255))
    
    status = db.Column(db.Integer, default=1)  # 1=Screening, 3=Approved, -1=Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaffMember {self.full_name} ({self.position_applying})>'
    
    def get_status_name(self):
        """Get the human-readable status name"""
        if self.status == 1:
            return "Screening"
        elif self.status == 3:
            return "Approved"
        elif self.status == -1:
            return "Rejected"
        else:
            return "Unknown"