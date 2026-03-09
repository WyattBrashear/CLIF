from flask import Flask, request
import sqlite3
import uuid

database_connection1 = sqlite3.connect('UserData.db')
database_cursor1 = database_connection1.cursor()
database_cursor1.execute(
    'CREATE TABLE IF NOT EXISTS userdata (user_id TEXT, user_name TEXT, pass_hash TEXT, pass_hashmode TEXT, allocation_limit INT)'
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
    database_cursor.execute("INSERT INTO userdata (user_id, user_name, pass_hash, pass_hashmode, allocation_limit) VALUES (?, ?, ?, ?, ?)", (user_id, user_name, pass_hash, pass_hashmode))
    database_connection.commit()
    return {
        'status': 'success',
        'message': 'User Created',
        'user_id': user_id
    }

@app.route('/fetch_userdata', methods=['POST'])
def fetch_userdata():
    database_connection = sqlite3.connect('UserData.db')
    database_cursor = database_connection.cursor()
    #first things first. Before we hand over ANY user data, We need to do Authentication
    database_cursor.execute("SELECT user_id, pass_hash FROM userdata")
    data = database_cursor.fetchall()

if __name__ == '__main__':
    app.run()
