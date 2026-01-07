from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import sqlite3
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'biwc-kwabenya-secure-2025-change-in-production'

DATABASE = 'church_members.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database"""
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                date_of_birth TEXT,
                gender TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                marital_status TEXT,
                occupation TEXT,
                auxiliary_group TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                spiritual_status TEXT,
                baptism_date TEXT,
                previous_church TEXT,
                skills_interests TEXT,
                membership_status TEXT DEFAULT 'active',
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin user table (linked to members)
        cursor.execute('''
            CREATE TABLE admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER UNIQUE NOT NULL,
                admin_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")

# Initialize database on startup
with app.app_context():
    init_db()

def get_member_stats():
    """Get statistics about members"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM members WHERE membership_status = ?', ('active',))
    total_members = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM members WHERE gender = ? AND membership_status = ?', ('Male', 'active'))
    male_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM members WHERE gender = ? AND membership_status = ?', ('Female', 'active'))
    female_count = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total': total_members,
        'male': male_count,
        'female': female_count
    }

@app.route('/')
def index():
    """Home page"""
    stats = get_member_stats()
    return render_template('index.html', stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Member registration"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Validate email doesn't exist (if provided)
            email = request.form.get('email', '').strip()
            if email:
                cursor.execute('SELECT id FROM members WHERE email = ?', (email,))
                if cursor.fetchone():
                    flash('❌ Email already registered! Please use a different email.', 'error')
                    conn.close()
                    return render_template('register.html')
            
            # Process auxiliary group checkboxes
            auxiliary_group_selections = request.form.getlist('auxiliary_group')
            auxiliary_group = ','.join(auxiliary_group_selections) if auxiliary_group_selections else ''
            
            # Insert new member
            cursor.execute('''
                INSERT INTO members (
                    first_name, last_name, email, phone, date_of_birth,
                    gender, address, city, state, postal_code,
                    marital_status, occupation, auxiliary_group, emergency_contact_name,
                    emergency_contact_phone, spiritual_status, baptism_date,
                    previous_church, skills_interests
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('first_name', '').strip(),
                request.form.get('last_name', '').strip(),
                email,
                request.form.get('phone', '').strip(),
                request.form.get('date_of_birth', ''),
                request.form.get('gender', ''),
                request.form.get('address', '').strip(),
                request.form.get('city', '').strip(),
                request.form.get('state', '').strip(),
                request.form.get('postal_code', '').strip(),
                request.form.get('marital_status', ''),
                request.form.get('occupation', '').strip(),
                auxiliary_group,
                request.form.get('emergency_contact_name', '').strip(),
                request.form.get('emergency_contact_phone', '').strip(),
                request.form.get('spiritual_status', ''),
                request.form.get('baptism_date', ''),
                request.form.get('previous_church', '').strip(),
                request.form.get('skills_interests', '').strip()
            ))
            
            conn.commit()
            member_id = cursor.lastrowid
            conn.close()
            
            flash(f'✅ Welcome! Registration successful! Your Member ID is: {member_id}', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'❌ Registration error: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/members')
def members():
    """View all members"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    gender_filter = request.args.get('gender', '')
    status_filter = request.args.get('status', 'active')
    
    query = 'SELECT * FROM members WHERE membership_status = ?'
    params = [status_filter]
    
    if search:
        query += ' AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if gender_filter:
        query += ' AND gender = ?'
        params.append(gender_filter)
    
    query += ' ORDER BY join_date DESC'
    
    cursor.execute(query, params)
    all_members = cursor.fetchall()
    conn.close()
    
    return render_template('members.html', members=all_members, search=search, gender_filter=gender_filter, status_filter=status_filter)

@app.route('/member/<int:member_id>')
def member_detail(member_id):
    """View member details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members WHERE id = ?', (member_id,))
    member = cursor.fetchone()
    conn.close()
    
    if not member:
        flash('Member not found', 'error')
        return redirect(url_for('members'))
    
    return render_template('member_detail.html', member=member)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = get_member_stats()
    return jsonify(stats)

# ============ ADMIN ROUTES ============

def admin_login_required(f):
    """Decorator to check if user is logged in as admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or 'admin_member_id' not in session:
            flash('❌ Please log in as admin to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        member_id = request.form.get('member_id', '').strip()
        password = request.form.get('password', '').strip()
        
        if not member_id or not password:
            flash('❌ Please enter member ID and password', 'error')
            return render_template('admin_login.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if member exists and is an admin
        cursor.execute('SELECT * FROM admin_users WHERE member_id = ?', (member_id,))
        admin = cursor.fetchone()
        
        if admin and check_password_hash(admin['admin_password'], password):
            session['admin_logged_in'] = True
            session['admin_member_id'] = member_id
            
            # Get admin's name for display
            cursor.execute('SELECT first_name, last_name FROM members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            
            flash(f'✅ Welcome Admin {member["first_name"]} {member["last_name"]}!', 'success')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid member ID or password. Please try again.', 'error')
        
        conn.close()
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('✅ You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    """Admin dashboard - View members and recent joins"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all members ordered by join_date
    cursor.execute('SELECT * FROM members ORDER BY join_date DESC')
    all_members = cursor.fetchall()
    
    # Get recently joined members (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('SELECT * FROM members WHERE join_date > ? ORDER BY join_date DESC', (seven_days_ago,))
    recent_members = cursor.fetchall()
    
    # Get member statistics
    stats = get_member_stats()
    cursor.execute('SELECT COUNT(*) FROM members')
    total_all = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         all_members=all_members, 
                         recent_members=recent_members,
                         stats=stats,
                         total_all=total_all)

@app.route('/admin/print-directory')
@admin_login_required
def print_directory():
    """Print-friendly members directory"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active members
    cursor.execute('SELECT * FROM members WHERE membership_status = ? ORDER BY last_name, first_name', ('active',))
    members = cursor.fetchall()
    conn.close()
    
    # Convert Row objects to dictionaries for template
    members_list = [dict(member) for member in members]
    
    from datetime import datetime
    return render_template('print_directory.html', members=members_list, now=datetime.now)

@app.route('/admin/export-csv')
@admin_login_required
def export_csv():
    """Export members to CSV format with presentable formatting"""
    import csv
    from io import StringIO
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members WHERE membership_status = ? ORDER BY last_name, first_name', ('active',))
    members = cursor.fetchall()
    conn.close()
    
    # Create CSV in memory
    output = StringIO()
    
    if members:
        # Define the order of columns with nice headers
        column_order = [
            'id', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'gender', 'marital_status', 'occupation', 'address', 'city', 'state', 
            'postal_code', 'auxiliary_group', 'emergency_contact_name', 'emergency_contact_phone',
            'spiritual_status', 'baptism_date', 'previous_church', 'skills_interests',
            'membership_status', 'join_date', 'last_updated'
        ]
        
        # Map database columns to nice headers
        column_mapping = {
            'id': 'ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone': 'Phone',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'address': 'Address',
            'city': 'City',
            'state': 'State',
            'postal_code': 'Postal Code',
            'marital_status': 'Marital Status',
            'occupation': 'Occupation',
            'auxiliary_group': 'Auxiliary Group',
            'emergency_contact_name': 'Emergency Contact',
            'emergency_contact_phone': 'Emergency Phone',
            'spiritual_status': 'Spiritual Status',
            'baptism_date': 'Baptism Date',
            'previous_church': 'Previous Church',
            'skills_interests': 'Skills & Interests',
            'membership_status': 'Membership Status',
            'join_date': 'Join Date',
            'last_updated': 'Last Updated'
        }
        
        # Create mapped fieldnames in the correct order
        mapped_fieldnames = [column_mapping.get(col, col) for col in column_order]
        
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(mapped_fieldnames)
        
        # Write data rows in the correct order
        for member in members:
            row = [member[col] for col in column_order]
            writer.writerow(row)
    
    # Return as downloadable file
    from flask import make_response
    response = make_response(output.getvalue())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response.headers["Content-Disposition"] = f"attachment; filename=BIWC_Members_Directory_{timestamp}.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route('/admin/manage-admins')
@admin_login_required
def manage_admins():
    """Manage admin users - add/remove admins"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all admin users with their details
    cursor.execute('''
        SELECT a.id, a.member_id, m.first_name, m.last_name, m.email, m.phone, a.created_at
        FROM admin_users a
        JOIN members m ON a.member_id = m.id
        ORDER BY m.first_name, m.last_name
    ''')
    admins = cursor.fetchall()
    
    # Get all non-admin members
    cursor.execute('''
        SELECT id, first_name, last_name, email, phone, gender
        FROM members
        WHERE id NOT IN (SELECT member_id FROM admin_users)
        AND membership_status = 'active'
        ORDER BY first_name, last_name
    ''')
    non_admins = cursor.fetchall()
    
    conn.close()
    
    return render_template('manage_admins.html', admins=admins, non_admins=non_admins)

@app.route('/admin/make-admin', methods=['POST'])
@admin_login_required
def make_admin():
    """Make a member an admin"""
    member_id = request.form.get('member_id', '').strip()
    admin_password = request.form.get('admin_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not member_id or not admin_password or not confirm_password:
        flash('❌ Please fill in all fields', 'error')
        return redirect(url_for('manage_admins'))
    
    if admin_password != confirm_password:
        flash('❌ Passwords do not match', 'error')
        return redirect(url_for('manage_admins'))
    
    if len(admin_password) < 6:
        flash('❌ Password must be at least 6 characters', 'error')
        return redirect(url_for('manage_admins'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if member exists
        cursor.execute('SELECT first_name, last_name FROM members WHERE id = ?', (member_id,))
        member = cursor.fetchone()
        
        if not member:
            flash('❌ Member not found', 'error')
            conn.close()
            return redirect(url_for('manage_admins'))
        
        # Check if already admin
        cursor.execute('SELECT id FROM admin_users WHERE member_id = ?', (member_id,))
        if cursor.fetchone():
            flash('❌ This member is already an admin', 'error')
            conn.close()
            return redirect(url_for('manage_admins'))
        
        # Hash password
        password_hash = generate_password_hash(admin_password)
        
        # Create admin user
        cursor.execute('''
            INSERT INTO admin_users (member_id, admin_password)
            VALUES (?, ?)
        ''', (member_id, password_hash))
        
        conn.commit()
        flash(f'✅ {member["first_name"]} {member["last_name"]} is now an admin!', 'success')
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('manage_admins'))

@app.route('/admin/remove-admin/<int:member_id>', methods=['POST'])
@admin_login_required
def remove_admin(member_id):
    """Remove admin privileges from a member"""
    # Prevent removing yourself
    if str(member_id) == session.get('admin_member_id'):
        flash('❌ You cannot remove your own admin privileges', 'error')
        return redirect(url_for('manage_admins'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get member name before deletion
        cursor.execute('SELECT first_name, last_name FROM members WHERE id = ?', (member_id,))
        member = cursor.fetchone()
        
        # Delete admin user
        cursor.execute('DELETE FROM admin_users WHERE member_id = ?', (member_id,))
        conn.commit()
        
        flash(f'✅ {member["first_name"]} {member["last_name"]} is no longer an admin', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('manage_admins'))

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
