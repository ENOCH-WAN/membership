from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sqlite3
import os
from functools import wraps

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
        
        # Create admin user table
        cursor.execute('''
            CREATE TABLE admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
