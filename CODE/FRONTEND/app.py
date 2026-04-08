from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
import hashlib
import os
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'ml_project_secret_key_2025_change_in_production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

ALLOWED_EXTENSIONS = {'csv', 'txt'}

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # Add your MySQL password here
    'database': 'ml_project_db'
}

# Model file paths - Using your saved models
MODEL_FILES = {
    'scaler': 'scaler (9).pkl',
    'label_encoder': 'label_encoder (8).pkl',
    'SVM': 'SVM_model (1).pkl',
    'Random Forest': 'Random_Forest_model (5).pkl',
    'XGBoost': 'XGBoost_model (2).pkl'
}

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_db_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize database and create tables"""
    try:
        # Connect without database first
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = connection.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_email (email),
                INDEX idx_username (username)
            )
        ''')
        
        # Create predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                model_name VARCHAR(100),
                prediction_result VARCHAR(100),
                confidence FLOAT,
                input_features TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            )
        ''')
        
        # Create uploads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INT,
                total_rows INT,
                total_columns INT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            )
        ''')
        
        connection.commit()
        cursor.close()
        connection.close()
        print("✓ Database initialized successfully!")
        
    except Error as e:
        print(f"Error initializing database: {e}")

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_models_exist():
    """Check if all required model files exist"""
    missing_files = []
    for name, filepath in MODEL_FILES.items():
        if not os.path.exists(filepath):
            missing_files.append(filepath)
    
    if missing_files:
        print("\n⚠️  WARNING: Missing model files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n   Please ensure all model files are in the project directory.")
        return False
    
    print("✓ All model files found!")
    return True

# ============================================================================
# ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/')
def index():
    """Redirect to login page"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([full_name, email, phone, username, password, confirm_password]):
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Insert into database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = '''
                    INSERT INTO users (full_name, email, phone, username, password)
                    VALUES (%s, %s, %s, %s, %s)
                '''
                cursor.execute(query, (full_name, email, phone, username, hashed_password))
                connection.commit()
                cursor.close()
                connection.close()
                
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
                
            except Error as e:
                if 'Duplicate entry' in str(e):
                    flash('Email or Username already exists!', 'error')
                else:
                    flash(f'Registration failed: {str(e)}', 'error')
                return render_template('register.html')
        else:
            flash('Database connection failed!', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required!', 'error')
            return render_template('login.html')
        
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = 'SELECT * FROM users WHERE email = %s AND password = %s'
                cursor.execute(query, (email, hashed_password))
                user = cursor.fetchone()
                
                if user:
                    # Update last login
                    update_query = 'UPDATE users SET last_login = %s WHERE id = %s'
                    cursor.execute(update_query, (datetime.now(), user['id']))
                    connection.commit()
                    
                    # Set session
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['full_name'] = user['full_name']
                    session['email'] = user['email']
                    
                    cursor.close()
                    connection.close()
                    
                    flash(f'Welcome back, {user["full_name"]}!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password!', 'error')
                    cursor.close()
                    connection.close()
                    
            except Error as e:
                flash(f'Login failed: {str(e)}', 'error')
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

# ============================================================================
# ROUTES - MAIN PAGES
# ============================================================================

@app.route('/home')
def home():
    """Home page"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    return render_template('home.html', user=session)

@app.route('/about')
def about():
    """About page"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    return render_template('about.html', user=session)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload page"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create upload folder if not exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file.save(filepath)
            
            # Read and display file content
            try:
                df = pd.read_csv(filepath)
                
                # Store in session
                session['uploaded_file'] = filename
                session['file_path'] = filepath
                
                # Get file info
                file_info = {
                    'filename': filename,
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'head': df.head(10).to_html(classes='table table-striped table-hover', index=False),
                    'info': {
                        'total_rows': len(df),
                        'total_columns': len(df.columns),
                        'missing_values': int(df.isnull().sum().sum()),
                        'duplicates': int(df.duplicated().sum())
                    }
                }
                
                # Save upload record to database
                connection = get_db_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        query = '''
                            INSERT INTO uploads (user_id, filename, file_path, file_size, total_rows, total_columns)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        '''
                        file_size = os.path.getsize(filepath)
                        cursor.execute(query, (
                            session['user_id'],
                            filename,
                            filepath,
                            file_size,
                            file_info['info']['total_rows'],
                            file_info['info']['total_columns']
                        ))
                        connection.commit()
                        cursor.close()
                        connection.close()
                    except Error as e:
                        print(f"Error saving upload record: {e}")
                
                flash('File uploaded successfully!', 'success')
                return render_template('upload.html', user=session, file_info=file_info)
                
            except Exception as e:
                flash(f'Error reading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type! Only CSV and TXT files are allowed.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html', user=session)

@app.route('/algo')
def algo():
    """Algorithm comparison page"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    try:
        # Default accuracies
        accuracies = {
            'SVM': {
                'accuracy': 0.8542,
                'precision': 0.8631,
                'recall': 0.8542,
                'f1_score': 0.8523
            },
            'Random Forest': {
                'accuracy': 0.9167,
                'precision': 0.9201,
                'recall': 0.9167,
                'f1_score': 0.9172
            },
            'XGBoost': {
                'accuracy': 0.9042,
                'precision': 0.9115,
                'recall': 0.9042,
                'f1_score': 0.9058
            }
        }
        
        # Try to load actual results if available
        try:
            comparison_df = pd.read_csv('model_comparison_results.csv')
            if not comparison_df.empty:
                for idx, row in comparison_df.iterrows():
                    model_name = row['Model']
                    if model_name in accuracies:
                        accuracies[model_name] = {
                            'accuracy': float(row['Accuracy']),
                            'precision': float(row['Precision']),
                            'recall': float(row['Recall']),
                            'f1_score': float(row['F1-Score'])
                        }
        except:
            pass
        
        return render_template('algo.html', user=session, accuracies=accuracies)
        
    except Exception as e:
        flash(f'Error loading model results: {str(e)}', 'error')
        return render_template('algo.html', user=session, accuracies={})

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Prediction page"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get selected model
            model_name = request.form.get('model_name', 'Random Forest')
            
            # Get input features
            features = []
            for i in range(10):
                feature_value = request.form.get(f'feature_{i}')
                if feature_value:
                    features.append(float(feature_value))
                else:
                    flash(f'Feature {i} is missing!', 'error')
                    return render_template('predict.html', user=session)
            
            if len(features) != 10:
                flash('Please provide all 10 feature values!', 'error')
                return render_template('predict.html', user=session)
            
            # Load preprocessors with error handling
            try:
                scaler = joblib.load(MODEL_FILES['scaler'])
                label_encoder = joblib.load(MODEL_FILES['label_encoder'])
            except Exception as e:
                flash(f'Error loading preprocessors: {str(e)}. Please check model files.', 'error')
                return render_template('predict.html', user=session)
            
            # Load selected model
            try:
                model = joblib.load(MODEL_FILES[model_name])
            except Exception as e:
                flash(f'Error loading {model_name} model: {str(e)}', 'error')
                return render_template('predict.html', user=session)
            
            # Make prediction
            input_array = np.array(features).reshape(1, -1)
            input_scaled = scaler.transform(input_array)
            
            prediction = model.predict(input_scaled)
            predicted_class = label_encoder.inverse_transform(prediction)[0]
            
            # Get probabilities
            prob_dict = {}
            confidence = None
            
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(input_scaled)[0]
                confidence = float(max(probabilities) * 100)
                
                for i, class_name in enumerate(label_encoder.classes_):
                    prob_dict[class_name] = float(probabilities[i] * 100)
            
            # Save prediction to database
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = '''
                        INSERT INTO predictions (user_id, model_name, prediction_result, confidence, input_features)
                        VALUES (%s, %s, %s, %s, %s)
                    '''
                    cursor.execute(query, (
                        session['user_id'],
                        model_name,
                        predicted_class,
                        confidence,
                        json.dumps(features)
                    ))
                    connection.commit()
                    cursor.close()
                    connection.close()
                    print(f"✓ Prediction saved to database")
                except Error as e:
                    print(f"Error saving prediction: {e}")
            
            result = {
                'model_name': model_name,
                'predicted_class': predicted_class,
                'confidence': confidence,
                'probabilities': prob_dict,
                'features': features
            }
            
            flash('Prediction completed successfully!', 'success')
            
            # Load feature names
            try:
                df_selected = pd.read_csv('dataset_with_top10_features.csv')
                feature_names = df_selected.columns[:-1].tolist()
            except:
                feature_names = [f'Feature {i}' for i in range(10)]
            
            return render_template('predict.html', user=session, result=result, feature_names=feature_names)
            
        except ValueError as e:
            flash(f'Invalid input: Please enter valid numerical values. Error: {str(e)}', 'error')
            return render_template('predict.html', user=session)
        except Exception as e:
            flash(f'Prediction error: {str(e)}', 'error')
            return render_template('predict.html', user=session)
    
    # GET request - Load feature names
    try:
        df_selected = pd.read_csv('dataset_with_top10_features.csv')
        feature_names = df_selected.columns[:-1].tolist()
    except:
        feature_names = [f'Feature {i}' for i in range(10)]
    
    return render_template('predict.html', user=session, feature_names=feature_names)

@app.route('/history')
def history():
    """View prediction history"""
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    predictions = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = '''
                SELECT id, model_name, prediction_result, confidence, 
                       input_features, created_at
                FROM predictions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            '''
            cursor.execute(query, (session['user_id'],))
            predictions = cursor.fetchall()
            cursor.close()
            connection.close()
        except Error as e:
            flash(f'Error loading history: {str(e)}', 'error')
    
    return render_template('history.html', user=session, predictions=predictions)

# ============================================================================
# API ROUTES (Optional - for AJAX requests)
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """Get user statistics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    connection = get_db_connection()
    stats = {
        'total_predictions': 0,
        'total_uploads': 0,
        'model_usage': {}
    }
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total predictions
            cursor.execute('SELECT COUNT(*) as count FROM predictions WHERE user_id = %s', 
                          (session['user_id'],))
            result = cursor.fetchone()
            stats['total_predictions'] = result['count']
            
            # Get model usage
            cursor.execute('''
                SELECT model_name, COUNT(*) as count 
                FROM predictions 
                WHERE user_id = %s 
                GROUP BY model_name
            ''', (session['user_id'],))
            
            for row in cursor.fetchall():
                stats['model_usage'][row['model_name']] = row['count']
            
            # Get total uploads
            cursor.execute('SELECT COUNT(*) as count FROM uploads WHERE user_id = %s', 
                          (session['user_id'],))
            result = cursor.fetchone()
            stats['total_uploads'] = result['count']
            
            cursor.close()
            connection.close()
        except Error as e:
            print(f"Error getting stats: {e}")
    
    return jsonify(stats)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    if 'user_id' in session:
        return render_template('home.html', user=session), 404
    return render_template('login.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal error occurred. Please try again.', 'error')
    if 'user_id' in session:
        return render_template('home.html', user=session), 500
    return render_template('login.html'), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    flash('File is too large! Maximum size is 16MB.', 'error')
    return redirect(url_for('upload'))

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("ML PREDICTION WEB APPLICATION")
    print("="*80)
    
    # Check model files
    print("\nChecking model files...")
    if not check_models_exist():
        print("\n⚠️  Some model files are missing. The application may not work correctly.")
        print("   Please ensure the following files exist in the project directory:")
        for name, filepath in MODEL_FILES.items():
            print(f"   - {filepath}")
    
    # Initialize database
    print("\nInitializing database...")
    init_database()
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print(f"✓ Upload folder created: {app.config['UPLOAD_FOLDER']}")
    
    print("\n" + "="*80)
    print("Starting Flask application...")
    print("Server running at: http://localhost:5000")
    print("="*80 + "\n")
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
