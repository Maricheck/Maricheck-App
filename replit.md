# Maricheck - Maritime Crew Management System

## Overview

Maricheck is a professional Flask-based web application for managing maritime crew member registrations and certification tracking. The system provides comprehensive functionality for crew registration, administrative dashboard management, and real-time status tracking through passport number lookup. Built with modern Bootstrap design, navy blue and sea green branding, and PostgreSQL database backend for reliable data persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask
- **UI Framework**: Bootstrap 5 with light theme and custom Maricheck branding
- **Icons**: Font Awesome 6.4.0
- **Typography**: Google Fonts (Inter, Roboto)
- **Color Scheme**: Navy blue primary (#1e3a8a), Sea green accent (#20B2AA), Gold highlights (#fbbf24)
- **Branding**: Custom SVG maritime logo with anchor and wave elements
- **Responsive Design**: Mobile-first approach using Bootstrap grid system
- **Client-side Validation**: HTML5 form validation with enhanced Bootstrap styling
- **User Interface Separation**: Public pages for crew, protected admin dashboard

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Architecture Pattern**: MVC pattern with database models
- **Authentication**: Session-based admin authentication
- **Security**: Role-based access control (Public vs Admin)
- **Password Security**: Werkzeug password hashing

### Key Design Decisions
- **Database-Backed**: PostgreSQL for persistent data storage
- **Dual Interface Design**: Public crew interface + protected admin dashboard
- **Simple Authentication**: Basic admin login system
- **Environment Configuration**: Database URL and session secrets from environment
- **RESTful Routes**: Clear URL patterns for different user roles

## Key Components

### User Interface Separation

**🔓 Public Interface (Crew Members):**
- **Home Page (`/home`)**: Landing page with navigation to all public features
- **Registration (`/register`)**: Form-based crew member registration with validation
- **Status Tracking (`/track`)**: Public interface for status lookup via passport
- **Thank You Page**: Registration confirmation with tracking information

**🔒 Admin Interface (Protected):**
- **Admin Login (`/admin/login`)**: Authentication page for administrators
- **Dashboard (`/`)**: Administrative interface showing all crew members with statistics
- **Status Updates (`/update_status/<int:crew_id>`)**: Administrative status progression
- **Admin Logout (`/admin/logout`)**: Session termination

### Database Models

**Admin Model:**
```python
class Admin(db.Model):
    id = int              # Primary key
    username = str        # Unique admin username
    password_hash = str   # Hashed password
    created_at = datetime # Account creation timestamp
```

**CrewMember Model:**
```python
class CrewMember(db.Model):
    id = int              # Primary key
    name = str            # Full name
    rank = str            # Maritime rank/position
    passport = str        # Passport number (uppercase, unique)
    status = int          # Status stage index (0-3)
    created_at = datetime # Registration timestamp
    updated_at = datetime # Last status update
```

### Status System
- **4-Stage Progression**: Registered → Screening → Documents Verified → Approved
- **Color Coding**: Secondary → Warning → Info → Success
- **One-way Flow**: Status can only advance, never regress

## Data Flow

1. **Registration Flow**:
   - User fills registration form
   - Server validates required fields and duplicate passports
   - New crew member added to in-memory storage
   - Success confirmation displayed

2. **Administrative Flow**:
   - Admin views dashboard with statistics and crew list
   - Admin can advance crew member status
   - Status updates trigger immediate page refresh

3. **Tracking Flow**:
   - User enters passport number
   - System searches in-memory data
   - Displays current status with progress visualization

## External Dependencies

### CDN Resources
- **Bootstrap CSS**: `bootstrap-agent-dark-theme.min.css` from cdn.replit.com
- **Font Awesome**: Version 6.0.0 from cdnjs.cloudflare.com
- **Bootstrap JS**: Implied for interactive components

### Python Dependencies
- **Flask**: Core web framework
- **os**: Environment variable access for configuration

## Deployment Strategy

### Current Setup
- **Development Mode**: Flask debug mode enabled
- **Port Configuration**: Default Flask development server
- **Static Assets**: Served via Flask's static file handling
- **Environment Variables**: SESSION_SECRET for production security

### Scalability Considerations
- **Data Persistence**: Current in-memory storage will reset on restart
- **Concurrent Access**: No thread safety for crew_data modifications
- **Production Readiness**: Requires proper WSGI server and database integration

### Recommended Enhancements
- **Database Integration**: Replace in-memory storage with persistent database
- **Authentication**: Add admin login system for dashboard access
- **API Endpoints**: RESTful API for mobile or external integrations
- **Data Validation**: Enhanced server-side validation and sanitization
- **Logging**: Application logging for debugging and monitoring