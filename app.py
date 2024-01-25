from flask import Flask, render_template, request, jsonify
import psycopg2
import os

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
        date_of_birth = request.form['date_of_birth']
        email = request.form['email']
        pincode = request.form['pincode']
        application_no = request.form['application_no']

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert into applicant_details
        cur.execute("INSERT INTO applicant_details (name, phone_number) VALUES (%s, %s) RETURNING id",
                    (name, phone_number))
        applicant_id = cur.fetchone()[0]

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

        query = f"SELECT * FROM applicant_details ad JOIN applicant_attributes aa ON ad.id = aa.applicant_id WHERE {' OR '.join(query_parts)}"

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

if __name__ == '__main__':
    app.run(debug=True)
