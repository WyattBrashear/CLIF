from flask import Flask, request, send_file, send_from_directory
import sqlite3
import uuid
import os
from werkzeug.utils import secure_filename
from pathlib import Path

database_connection1 = sqlite3.connect('UserData.db')
database_cursor1 = database_connection1.cursor()
database_cursor1.execute(
    'CREATE TABLE IF NOT EXISTS userdata (user_id TEXT, user_name TEXT, pass_hash TEXT, pass_hashmode TEXT, allocation_limit INT, used_data INT)'
)
database_connection1.commit()
app = Flask(__name__)


@app.route('/register', methods=['POST'])
def register_user():  # put application's code here
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    user_id = str(uuid.uuid4())
    user_name = str(request_data['username'])
    pass_hash = str(request_data['password'])
    pass_hashmode = str(request_data['password_hash'])
    allocation_limit = int(5120000000)
    database_cursor.execute("INSERT INTO userdata (user_id, user_name, pass_hash, pass_hashmode, allocation_limit, used_data) VALUES (?, ?, ?, ?, ?, ?)", (user_id, user_name, pass_hash, pass_hashmode, allocation_limit, 0))
    database_connection.commit()
    os.mkdir(f"FileStor/users/{user_id}")
    return {
        'status': 'success',
        'message': 'User Created',
        'user_id': user_id
    }

@app.route('/fetch_userdata', methods=['POST'])
def fetch_userdata():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json(silent=True) or {}
    #first things first. Before we hand over ANY user data, We need to do Authentication
    database_cursor.execute("SELECT user_id, user_name, pass_hash, allocation_limit, used_data FROM userdata WHERE user_id = ? AND pass_hash = ?", (request_data.get('user_id'), request_data.get('pass_hash')))
    data = database_cursor.fetchall()
    return {
        'status': 'success',
        'user_id': data[0][0],
        'user_name': data[0][1],
        'allocation_limit': data[0][3],
        'used_data': data[0][4],
    }

@app.route('/upload_file', methods=['POST'])
def upload_file():
    #TODO: Switch the file backend over to a SQL database
    #Connect the Database
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    #Check if the user is allowed to upload this data
    database_cursor.execute("SELECT used_data, allocation_limit FROM userdata WHERE user_id = ?", (request.form.get('user_id'),))
    sizedata = database_cursor.fetchall()
    try:
        if sizedata[0][0] >= sizedata[0][1]:
            return {
                'status': 'fail',
                'message': 'Used storage is higher than allocation!'
            }
    except:
        return {
            'status': 'fail',
            'message': 'An error occurred while uploading the file.'
        }
    #First things first. Authentication
    passhash = request.form.get('pass_hash')
    database_cursor.execute("SELECT pass_hash FROM userdata WHERE pass_hash = ? AND user_id = ?", (passhash,request.form.get('user_id'),))
    data = database_cursor.fetchall()
    print(data)
    print(passhash)
    try:
        if data[0][0] == passhash:
            #Then, UPLOAD
            with open(f"FileStor/users/{request.form.get('user_id')}/{request.form.get('filename')}", 'wb') as f:
                f.write(request.files['file'].read())
                f.flush()
                # Get current usage size
                database_cursor.execute("SELECT used_data FROM userdata WHERE user_id = ?",(request.form.get('user_id'),))
                data = database_cursor.fetchall()
                print(data)
                used_amount = int(data[0][0])
                file_size = Path(f"FileStor/users/{request.form.get('user_id')}/{request.form.get('filename')}").stat().st_size
                print(used_amount, file_size)
                # Update the data usage amount
                new_amount = used_amount + file_size
                if new_amount >= sizedata[0][1]:
                    os.remove(f"FileStor/users/{request.form.get('user_id')}/{secure_filename(request.form.get('filename'))}")
                    return {
                        'status': 'fail',
                        'message': 'Used storage is higher than allocation!'
                    }
                print(new_amount)
                database_cursor.execute("UPDATE userdata SET used_data = ? WHERE user_id = ?",(new_amount, request.form.get('user_id'),))
                database_connection.commit()
                print("Updated")
                return {
                    'status': 'success',
                    'message': 'File Uploaded',
                }
        else:
            return {
                'status': 'fail',
                'message': 'Authentication Failure!'
            }
    except Exception as e:
        print(e)
        return {
            'status': 'fail',
            'message': 'An error occurred while uploading the file.'
        }

@app.route('/list', methods=['POST'])
def list_dir():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    #As per usual, before we hand over data. AUTHENTICATION
    database_cursor.execute("SELECT pass_hash FROM userdata WHERE pass_hash = ?", (request_data.get('pass_hash'),))
    data = database_cursor.fetchall()
    try:
        x = data[0][0]
    except:
        return {
            'status': 'fail',
            'message': 'Authentication Failure!'
        }
    try:
        if data[0][0] == request_data.get('pass_hash'):
            directories = os.listdir(f"FileStor/users/{request_data.get('user_id')}/{request_data.get('directory')}")
            return {
                'status': 'success',
                'directories': directories
            }
        else:
            return {
                'status': 'fail',
                'message': 'Authentication Failure!'
            }
    except:
        return {
            'status': 'fail',
            'message': 'An error occurred while listing the directory.'
        }
@app.route('/retrieve-file', methods=['POST'])
def retrieve_file():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    #Authing Tiem!!!
    database_cursor.execute("SELECT pass_hash FROM userdata WHERE pass_hash = ? AND user_id = ?", (request_data.get('pass_hash'),request_data.get('user_id'),))
    data = database_cursor.fetchall()
    if data[0][0] == request_data.get('pass_hash'):
        if os.path.exists(f"FileStor/users/{request_data.get('user_id')}/{request_data.get('filename')}"):
            return send_from_directory(
                directory=f"FileStor/users/{secure_filename(request_data.get('user_id'))}",
                path=secure_filename(request_data.get('filename')),
                as_attachment=True,
            )
        else:
            return {
                'status': 'fail',
                'message': 'File path does not exist!'
            }, 404
    else:
        return {
            'status': 'fail',
            'message': 'Authentication Failure!'
        }


@app.route('/authenticate', methods=['POST'])
def authenticate():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    database_cursor.execute("SELECT pass_hash FROM userdata WHERE pass_hash = ? AND user_id = ?", (request_data.get('pass_hash'), request_data.get('user_id'),))
    auth_pass = database_cursor.fetchall()
    try:
        if request_data.get('pass_hash') == auth_pass[0][0]:
            return {
                'status': 'success',
                'message': 'Authentication Valid!'
            }
    except:
        return {
            'status': 'fail',
            'message': 'Authentication FailureI!'
        }

@app.route('/translate_uname', methods=['POST'])
def translate_uname():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    #Okay. All this needs to do is translate the Username to a UserID. So no authentication needed!
    database_cursor.execute("SELECT user_id FROM userdata WHERE user_name = ?", (request_data.get('user_name'),))
    data = database_cursor.fetchall()
    return {
        'status': 'success',
        'message': f'{data[0][0]}'
    }

@app.route('/delete-file', methods=['POST'])
def delete_file():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json()
    database_cursor.execute("SELECT pass_hash FROM userdata WHERE user_id = ? AND pass_hash = ?", (request_data.get('user_id'), request_data.get('pass_hash')))
    auth_data = database_cursor.fetchall()
    if auth_data[0][0] == request_data.get('pass_hash'):
        filepath = secure_filename(request_data.get('filename'))
        os.remove(f"FileStor/users/{secure_filename(request_data.get('user_id'))}/{filepath}")
        return {
            'status': 'success',
            'message': 'File Deleted'
        }
    else:
        return {
            'status': 'fail',
            'message': 'Authentication Failure!'
        }


if __name__ == '__main__':
    app.run()
