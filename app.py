import shutil
import hashlib
from flask import Flask, request, send_file, send_from_directory, redirect
import sqlite3
import uuid
import os
import json
from pathlib import Path

Path('FileStor').mkdir(parents=True, exist_ok=True)
database_connection1 = sqlite3.connect('UserData.db')
database_cursor1 = database_connection1.cursor()
database_cursor1.execute(
    'CREATE TABLE IF NOT EXISTS userdata (user_id TEXT, user_name TEXT, pass_hash TEXT, pass_hashmode TEXT, allocation_limit INT, used_data INT)'
)
database_cursor1.execute("CREATE TABLE IF NOT EXISTS filedata (file_id TEXT, owner TEXT, file_name TEXT, file_size INT, file_path TEXT, file_hash TEXT)")
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
    if os.path.exists("./CLIF.json"):
        with open("./CLIF.json", "r") as f:
            server_config = json.load(f)
            allocation_limit = server_config.get("allocation_limit")
            f.close()
    else:
        allocation_limit = int(20000)
    database_cursor.execute("INSERT INTO userdata (user_id, user_name, pass_hash, pass_hashmode, allocation_limit, used_data) VALUES (?, ?, ?, ?, ?, ?)", (user_id, user_name, pass_hash, 'sha256', allocation_limit, 0))
    database_connection.commit()
    database_connection.close()
    return {
        'status': 'success',
        'message': 'User Created',
        'user_id': user_id
    }

@app.route('/fetch-userdata', methods=['POST'])
def fetch_userdata():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    request_data = request.get_json(silent=True) or {}
    #first things first. Before we hand over ANY user data, We need to do Authentication
    database_cursor.execute("SELECT user_id, user_name, pass_hash, allocation_limit, used_data FROM userdata WHERE user_id = ? AND pass_hash = ?", (request_data.get('user_id'), request_data.get('pass_hash')))
    data = database_cursor.fetchall()
    #Yes i know this is a bad variable name. i cant think of a name right now.
    database_cursor.close()
    x = data[0][4] / data[0][3]
    return {
        'status': 'success',
        'user_id': data[0][0],
        'user_name': data[0][1],
        'allocation_limit': data[0][3],
        'used_data': data[0][4],
        'data_percent': int(x*100)
    }

@app.route('/upload_file', methods=['POST'])
def upload_file():
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
            file_id = str(uuid.uuid4())
            with open(os.path.join("FileStor", file_id), 'wb') as f:
                f.write(request.files['file'].read())
                f.flush()
            #Calculate file hash
            hash_func = hashlib.new("sha256")
            with open(os.path.join("FileStor", file_id), 'rb') as file:
                while chunk := file.read(8192):
                    hash_func.update(chunk)
            file_hash = hash_func.hexdigest()
            try:
                os.mkdir(os.path.join("FileStor", file_hash[:2]))
            except:
                pass
            shutil.move(os.path.join("FileStor", file_id), os.path.join("FileStor", file_hash[:2], file_hash))
            database_cursor.execute("INSERT INTO filedata (file_id, owner, file_name, file_size, file_path, file_hash) VALUES (?, ?, ?, ?, ?, ?)", (file_id, request.form.get('user_id'), request.form.get('filename'), os.path.getsize(os.path.join("FileStor", file_hash[:2], file_hash)), f"{file_hash[:2]}/{file_hash}", file_hash))
            database_connection.commit()
            database_cursor.execute("SELECT file_size FROM filedata WHERE owner = ?", (request.form.get('user_id'),))
            data = database_cursor.fetchall()
            new_size = sum(row[0] for row in data)
            database_cursor.execute("SELECT allocation_limit FROM userdata WHERE user_id = ?", (request.form.get('user_id'),))
            allocation_limit = database_cursor.fetchall()[0][0]
            if new_size >= allocation_limit:
                os.remove(os.path.join("FileStor", file_hash[:2], file_hash))
                database_cursor.execute("DELETE FROM filedata WHERE owner = ? AND file_id = ?", (request.form.get('user_id'), file_id,))
                database_connection.commit()
                return {
                    'status': 'fail',
                    'message': "File Denied! File size too large!"
                }
            database_cursor.execute("UPDATE userdata SET used_data = ? WHERE user_id = ?",
                                    (new_size, request.form.get('user_id')))
            database_connection.commit()
            database_connection.close()
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
            database_cursor.execute("SELECT file_name, file_size, file_id FROM filedata WHERE owner = ?", (request_data.get('user_id'),))
            directories = database_cursor.fetchall()
            file_data = []
            for file_name, file_size, file_id in directories:
                file_data.append((file_name, file_size, file_id))
            database_cursor.close()
            print(file_data)
            return {
                'status': 'success',
                'directories': file_data
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
        # Get data from filedata database
        database_cursor.execute(
            "SELECT file_path, file_id, file_hash, file_name FROM filedata WHERE file_name = ? AND owner = ?",
            (request_data.get('filename'), request_data.get('user_id'),))
        filedata = database_cursor.fetchall()
        database_cursor.close()
        #print(filedata)
        if filedata:
            return send_from_directory(os.path.join("FileStor", str(filedata[0][0])[:2]), filedata[0][1], as_attachment=True)
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
    database_cursor.close()
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
    database_cursor.close()
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
        database_cursor.execute("SELECT file_path FROM filedata WHERE owner = ? and file_name = ?", (request_data.get('user_id'), request_data.get('filename')))
        data = database_cursor.fetchall()
        print(request_data)
        print(data)
        if len(data) > 0:
            os.remove(os.path.join("FileStor", data[0][0]))
        else:
            return {
                'status': 'fail',
                "message": "File does not exist!"
            }
        database_cursor.execute("DELETE FROM filedata WHERE owner = ? AND file_name = ?", (request_data.get("user_id"), request_data.get('filename')))
        database_connection.commit()
        database_cursor.execute("SELECT file_size FROM filedata WHERE owner = ?", (request_data.get('user_id'),))
        data = database_cursor.fetchall()
        new_size = sum(row[0] for row in data)
        database_cursor.execute("UPDATE userdata SET used_data = ? WHERE user_id = ?", (new_size, request_data.get('user_id')))
        database_connection.commit()
        database_connection.close()
        return {
            'status': 'success',
            'message': 'File Deleted'
        }
    else:
        return {
            'status': 'fail',
            'message': 'Authentication Failure!'
        }

@app.route('/', methods=["GET"])
def forward_to_github():
    return redirect("https://github.com/WyattBrashear/CLIF")


if __name__ == '__main__':
    if os.path.exists('./CLIF.json'):
        with open("./CLIF.json", "r") as f:
            server_config = json.load(f)
            port = server_config.get("server_port")
            host = server_config.get("host")
    else:
        host = "127.0.0.1"
        port = 8000
    print("CLIF (CLIFilestor) v 1.10 Created by Wyatt Brashear")
    app.run(host=host, port=port)
