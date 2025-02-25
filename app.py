from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

app = Flask(__name__)
CORS(app)

# Check if serviceAccountKey.json exists
if not os.path.exists('serviceAccountKey.json'):
    raise FileNotFoundError("serviceAccountKey.json not found. Please download it from Firebase Console.")

# Initialize Firebase Admin
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Hello World!'})

@app.route('/users', methods=['GET'])
def get_users():
    try:
        users_ref = db.collection('users')
        docs = users_ref.get()  # Changed from stream() to get()
        users = []
        
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            
            # Fetch subcollections for each user
            subcollections = doc.reference.collections()
            user_data['collections'] = {}
            
            for subcoll in subcollections:
                subcoll_docs = subcoll.get()
                user_data['collections'][subcoll.id] = [subdoc.to_dict() for subdoc in subcoll_docs]
            
            users.append(user_data)
            print(f"Found user with data: {user_data}")  # Debug logging
            
        return jsonify(users)
    except Exception as e:
        print(f"Error fetching users: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/update-balance', methods=['POST'])
def update_balance():
    try:
        data = request.json
        user_id = data.get('userId')
        current_balance = data.get('currentBalance')
        
        if not user_id or current_balance is None:
            return jsonify({'error': 'Missing required fields'}), 400
            
        new_balance = current_balance + 1000
        
        db.collection('users').document(user_id).update({
            'balance': new_balance
        })
        
        return jsonify({'success': True, 'newBalance': new_balance})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add-test-user', methods=['GET'])
def add_test_user():
    try:
        test_user = {
            'name': 'Test User',
            'email': 'test@example.com',
            'balance': 0
        }
        db.collection('users').add(test_user)
        return jsonify({'message': 'Test user added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add-user', methods=['POST'])
def add_user():
    try:
        data = request.json
        required_fields = ['accountNumber', 'holderName', 'email', 'ifscCode', 'balance']
        
        # Validate required fields
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Add user to database
        new_user = {
            'accountNumber': data['accountNumber'],
            'name': data['holderName'],
            'email': data['email'],
            'ifscCode': data['ifscCode'],
            'balance': data['balance'],
            'createdDate': data['createdDate'],
            'transactions': []
        }
        
        # Check if account number already exists
        existing_user = db.collection('users').where('accountNumber', '==', data['accountNumber']).get()
        if len(existing_user) > 0:
            return jsonify({'error': 'Account number already exists'}), 400
            
        doc_ref = db.collection('users').add(new_user)
        return jsonify({'success': True, 'userId': doc_ref[1].id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)