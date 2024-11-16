from flask import Flask, request, jsonify
import pandas as pd
import joblib 
from utils import load_data, process_service_data, generate_report, results,respones
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import sqlite3
import bcrypt
from email.utils import parseaddr
import os
import time
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}) 


UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024


def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False,timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_email(email):
    # Check if the email is valid
    return '@' in parseaddr(email)[1]

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')  # Confirm password field
    email = data.get('email')

    # Check if all required fields are provided
    if not username or not password or not email or not confirm_password:
        return jsonify({'error': 'Username, password, email, and confirm password are required'}), 400

    # Check if passwords match
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    # Check for a valid email
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email address'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email already exists in the database
        user_by_email = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user_by_email:
            return jsonify({'error': 'Email already exists'}), 400

        # Check if the username already exists in the database
        user_by_username = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user_by_username:
            return jsonify({'error': 'Username already exists'}), 400

        # Hash the password only after ensuring passwords match
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user
        cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                       (username, hashed_password, email))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User created successfully'}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Database integrity error occurred'}), 400
    except sqlite3.OperationalError as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
@app.route('/approve-user', methods=['POST'])
def approve_user():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the user's approved status
    cursor.execute('UPDATE users SET approved = ? WHERE id = ?', ('approved', user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User approved successfully'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve user by email
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    # Check if user exists and password matches
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        # Check if the user is approved
        if user['approved'] != 'approved':
            return jsonify({'error': 'Account not approved by admin'}), 403
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'file_path': file_path}), 200
    
@app.route('/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all users with their approval status
    users = cursor.execute('SELECT id, username, email, approved FROM users').fetchall()
    conn.close()

    # Convert the result to a list of dictionaries
    users_list = [dict(user) for user in users]
    
    return jsonify(users_list), 200

@app.route('/generate-report', methods=['POST'])
def generate_report_endpoint():
    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Content-Type must be application/json'}), 415
        data = request.json
        file_path = data.get('file_path')
        year = data.get('year')
        month = data.get('month')
        year1 = data.get('year1')
        month1 = data.get('month1')

        df = load_data(file_path)
        df = df.sort_values(by=["Year", "Month", "Product line"])
        df = df.set_index(["Year", "Month", "Product line"])

        final_dataframe1 = process_service_data(df, year, month)
        final_dataframe2 = process_service_data(df, year1, month1)
        product_lines = pd.concat([final_dataframe1, final_dataframe2])['Product'].unique()

    # Step 3: Generate the report
        report = generate_report(year, month, year1, month1, product_lines, final_dataframe1, final_dataframe2)
        final_data = results(report)
        analysis = f"""
You are an expert data analyst tasked with analyzing category data for various products in the dataset. The dataset includes the following attributes:

- **Product Names**: {final_data['Product Line'].unique().tolist()} (list of different product lines)
- **Types**: {final_data['Type'].unique().tolist()} (types of products, including 'SKU' and 'WO')
- **Revenue Growth Rate**: {final_data['Revenue Growth Rate ']} (monthly revenue growth rate values)
- **Margin Growth Rate**: {final_data['Margin Growth Rate']} (monthly margin growth rate values)
- **Category**: {final_data['Category']} (derived from the analysis of growth rates)

Please provide an analysis for each product category by comparing the **Revenue Growth Rate** and **Margin Growth Rate** across two months for each product line and type. The analysis should consider the following conditions for categorization:

1. **Growing**: If both the Revenue Growth Rate and Margin Growth Rate have increased compared to the previous month.
2. **Stable**: If one of the growth rates has increased while the other remains unchanged or both remain constant.
3. **Declining**: If both the Revenue Growth Rate and Margin Growth Rate have decreased compared to the previous month.

Use the following format for each entry:

- **Product Name**: [Product Name] (specific name from the dataset)
- **Type**: [SKU or WO] (specific type from the dataset)
- **Category**: [Calculated Category] (based on the comparison of Revenue Growth Rate and Margin Growth Rate for both months)

- **Reason**: [Provide a detailed analysis explaining the category assignment. Clearly describe the trends observed in Revenue Growth Rate and Margin Growth Rate between the two months, and justify whether the category is growing, stable, or declining.]

For each product category, generate one distinct entry for both 'SKU' and 'WO' types, ensuring accurate comparison without adding any extra information outside of this format.
"""

        result = respones(analysis)
        prompt1 = f"""
        You are a strategic consultant providing suggestions based on the analysis results: {result}. 

        Please evaluate the findings and suggest specific strategies or methods that can be employed to improve the performance of the products in this dataset. 

        If the analysis indicates satisfactory results, simply respond with "All okay." 
        """
        result1 = respones(prompt1)
        # Return JSON response
        response_data = {
            'final_data': final_data.to_dict(orient='records'),  # Convert DataFrame to dict for JSON compatibility
            'analysis_result': result,
            'suggestion': result1
        }
        
        # Return the combined response as JSON
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

   

if __name__ == '__main__':
    app.run()
