from flask import Flask, request, jsonify
from pyngrok import ngrok
import pandas as pd
import joblib 
from utils import load_data, cleaning_data, generate_report, results,respones
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import sqlite3
import bcrypt
from email.utils import parseaddr
import os
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}) 
port_no = 5000
# Ensure your ngrok auth token is correct
ngrok.set_auth_token("2krmqKZu0EWIJESiqrVWagkvy9i_hnPfzwngRQuoCB6F2q1C")
public_url = ngrok.connect(port_no)
print(f"ngrok tunnel URL: {public_url}")  # Print the ngrok URL for debugging


UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db_connection():
    conn = sqlite3.connect('users.db')
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
    email = data.get('email')  # New field

    if not username or not password or not email:
        return jsonify({'error': 'Username, password, and email are required'}), 400

    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email address'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                       (username, hashed_password, email))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
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
    

@app.route('/generate-report', methods=['POST'])
def generate_report_endpoint():
    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Content-Type must be application/json'}), 415
        data = request.json
        file_path = data.get('file_path')
        sheet_name = data.get('sheet_name', 'Input Sheet (Monthly)')
        year = data.get('year')
        month = data.get('month')
        year1 = data.get('year1')
        month1 = data.get('month1')
        product_lines =  ['Product Line A', 'Product Line B', 'Product Line C', 'Product Line E', 'Product Line F', 'Product Line G']

        df = load_data(file_path, sheet_name)
        full_df = cleaning_data(df)
        report_df = generate_report(year, month, year1, month1, product_lines, full_df)
        final_data = results(report_df)
        prompt = f"""
        You are an expert tasked with analyzing the category data: {final_data["Category"]}. The data consists of two columns: {final_data['Margin Price Effect']} and {final_data['Margin Growth Rate']}. Your job is to review the values in these columns and provide reasoning for why each category appears in the dataset.
        Use the following format for each category:
        Product:{final_data["Product Line"]}
        Type:{final_data["Type"]}
        Category: [Category Name]
        Reasoning: [Provide a more explanation for why this category is represented based on the data.]
        Product: Product A
        Type:WO
        Category: [Category Name]
        Reasoning: [Provide a more explanation for why this category is represented based on the data.]
        other..
        Avoid giving any extra information.
        """
        result = respones(prompt)
        prompt1=f""" You are an expert to give the suggestion of the {result}, You give suggestion which strategy and method use to improve the performance, If the result is good then you show all okay.
        """
        result1 = respones(prompt1)
        # Return JSON response
        # return final_data.to_json(orient='records')
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
    app.run(port=port_no)
