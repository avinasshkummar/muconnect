from flask import Flask, render_template, request, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
import tempfile
import pandas as pd
import psycopg2.extras


app = Flask(__name__)

# Database connection info. You should get these from environment variables or a configuration file.
DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:@localhost:5433/muconnect'

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/')
def home():
    return render_template('home.html', current_view='home')

@app.route('/data-entry')
def data_entry_view():
    return render_template('data_entry.html', current_view='data_entry')

@app.route('/add_data', methods=['POST'])
def add_data():
    try:
        # Personal details
        name = request.form['name']
        phone_number = request.form['phone_number']

        # Application attributes
        father_name = request.form['father_name']
        roll_no = request.form['roll_no']
        date_of_birth = request.form['date_of_birth'] if request.form['date_of_birth'] else None
        email = request.form['email']
        pincode = request.form['pincode']
        application_no = request.form['application_no']

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if phone number exists
        cur.execute("SELECT id FROM applicant_details WHERE phone_number = %s", (phone_number,))
        result = cur.fetchone()

        if result is None:
            # Phone number doesn't exist, insert into applicant_details
            cur.execute("INSERT INTO applicant_details (name, phone_number) VALUES (%s, %s) RETURNING id",
                        (name, phone_number))
            applicant_id = cur.fetchone()[0]
        else:
            # Phone number exists, use existing applicant_id
            applicant_id = result[0]
            cur.execute("UPDATE applicant_details SET name = %s WHERE id = %s", (name, applicant_id))


        # Insert into applicant_attributes
        cur.execute("INSERT INTO applicant_attributes (applicant_id, father_name, roll_no, date_of_birth, email, pincode, application_no) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (applicant_id, father_name, roll_no, date_of_birth, email, pincode, application_no))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'OK', 'message': 'Data added successfully'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_data', methods=['POST'])
def get_data():
    try:
        # Extracting form data
        form_data = {
            'name': request.form.get('name'),
            'father_name': request.form.get('father_name'),
            'phone_number': request.form.get('phone_number'),
            'roll_no': request.form.get('roll_no'),
            'date_of_birth': request.form.get('date_of_birth'),
            'email': request.form.get('email'),
            'pincode': request.form.get('pincode'),
            'application_no': request.form.get('application_no')
        }

        query_parts = []
        params = []

        for key, value in form_data.items():
            if value:
                query_parts.append(f"ad.{key} = %s" if key in ['name', 'phone_number'] else f"aa.{key} = %s")
                params.append(value)

        if not query_parts:
            return jsonify({'error': 'No search criteria provided'}), 400

        query = f"SELECT distinct phone_number as number, name, ad.id as applicant_id FROM applicant_details ad JOIN applicant_attributes aa ON ad.id = aa.applicant_id WHERE {' OR '.join(query_parts)}"

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()

        results_list = [dict(row) for row in results]
        return jsonify({'status': 'OK', 'data': results_list})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/profile/<applicant_id>')
def profile(applicant_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM applicant_details ad JOIN applicant_attributes aa ON ad.id = aa.applicant_id WHERE ad.id = %s", (applicant_id,))
        result = cur.fetchall()
        cur.close()
        conn.close()

        summarized_result = {}
        if result is None:
            result = {'status': 'Error', 'message': 'No data for profile'}
        else:
            # Convert the result to a list of dictionaries
            result = [dict(row) for row in result]

            summarized_result["Name"] = result[0]['name']
            summarized_result["Phone Number"] = result[0]['phone_number']
            # Iterate through the result and modify attribute names
            i = 1
            for row in result:
                summarized_result["Father's Name "+ str(i)] = row['father_name']
                summarized_result["Roll Number "+ str(i)] = row['roll_no']
                summarized_result["Date Of Birth "+ str(i)] = row['date_of_birth']
                summarized_result["Email "+ str(i)] = row['email']
                summarized_result["Pincode "+ str(i)] = row['pincode']
                summarized_result["Application Number "+ str(i)] = row['application_no']
                i += 1
            # Flatten the dictionaries and add status key with value 'OK'
            summarized_result["status"]= 'OK'
            print(summarized_result)
    except Exception as e:
        summarized_result = {'status': 'Error', 'message': str(e)}
    return render_template('profile.html', profile=summarized_result)

def check_headers(data):
            expected_headers = ['Application_No', 'Date_of_Birth', 'Roll_No', 'Candidate_Name', 'Gender', 'Father_Name', 'Area', 'Locality', 'City', 'State', 'PinCode', 'Mobile_Number', 'Email']
            headers = data.columns.tolist()
            if headers != expected_headers:
                return False
            return True

@app.route('/bulk_import', methods=['POST'])
def bulk_import():
    try:
        file = request.files['file']
        filename = secure_filename(file.filename)
        
        # Save the file to a desired location
        # if folder doesn't exist, create it
        # take a temp path if upload_folder is not set
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            upload_folder = tempfile.gettempdir()
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))
        
        # Read the data from the Excel/CSV file using pandas
        if filename.endswith('.csv'):
            data = pd.read_csv(os.path.join(upload_folder, filename))
        elif filename.endswith('.xlsx'):
            data = pd.read_excel(os.path.join(upload_folder, filename))
        else:
            raise ValueError('Invalid file format')
        
        if check_headers(data) == False:
            raise ValueError('Invalid headers')
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Iterate through the data and insert into the database
        for index, row in data.iterrows():
            # Check if phone number exists
            cur.execute("SELECT id FROM applicant_details WHERE phone_number::bigint = %s", (row['Mobile_Number'],))
            result = cur.fetchone()
            applicant_id = None
            if result is None:
                cur.execute("INSERT INTO applicant_details (name, phone_number) VALUES (%s, %s)", (row['Candidate_Name'], row['Mobile_Number']))
                cur.execute("SELECT lastval()")
                applicant_id = cur.fetchone()[0]
            else:
                # Phone number exists, use existing applicant_id
                applicant_id = result[0]
                cur.execute("UPDATE applicant_details SET name = %s WHERE id = %s", (row['Candidate_Name'], applicant_id))
                # Insert into applicant_details table
                conn.commit()
            
            # Insert into applicant_attributes table
            cur.execute("INSERT INTO applicant_attributes (applicant_id, father_name, roll_no, date_of_birth, email, pincode, application_no) VALUES (%s, %s, %s, %s, %s, %s, %s)", (applicant_id, row["Father_Name"], row["Roll_No"], row["Date_of_Birth"], row["Email"], row["PinCode"], row["Application_No"]))
            conn.commit()
        
        # Close the database connection
        cur.close()
        conn.close()
        return {'status': 'OK', 'message': 'File uploaded and data imported successfully'}, 200
    except Exception as e:
        return {'status': 'Error', 'message': str(e)}, 400
        
if __name__ == '__main__':
    app.run(debug=True)
