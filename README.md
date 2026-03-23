# CLI FileStor
A CLI app/server meant to be a self hostable version of google drive with customizable storage limits.

## Interaction with the server
The server can be interacted with either by the client application or curl

# Setup
## Both Systems
Just use:
~~~bash
pip install clifilestor
~~~
And it can be run:
(Client)
~~~bash
clif {option}}
~~~
(Server)
~~~bash
clif-server
~~~
## Server
1. Install python3 (3.10 Reccomended)
2. Make sure venv is installed alongside python3
3. Download and run the app (server-mac) from the github release page. It will handle dependencies on its own (A startup script will run that installs all of them in a venv at runtime).
4. (Optional) if you want to run it without the executable, install the packages: requests, flask
## Client
1. Download the latest version of the client (client-mac) from the releases page.
2. Run the client executable.
3. (Optional) if you want to run the client without the exe overhead, install the packages: requests.

## Live Server
WIll be offline going into april 2026.
http://187.124.225.245:999
(Server is secure, hosted with gunicorn!)
## Demo Video:
https://drive.google.com/file/d/1rXJU0RaOJyMVX-mN0eXn6FDzDeSv1rVL/view?usp=sharing


# API Documentation
All of the API endpoints are POST based.

1. POST: /register - Register a new user. {username: STR, password: STR} password should be a hash of the password for security reasons. It returns a user_id.
2. POST: /fetch-userdata - retrieve userdata from the server. Requires authenticaion. {user_id: STR, pass_hash: STR}. Returns userdata (usage statistics, username, user_id, etc)
3. POST: /upload_file - Form data. Upload a file to the server. Requires authenticaion. {user_id: STR, pass_hash: STR, file: FILE} returns status
4. POST: /list - List all files under the ownership of a file. Requires authenticaion. {user_id: STR, pass_hash: STR} returns a "directories" list.
5. POST: /retrieve-file - Download a file, Requires authenticaion. {user_id: STR, pass_hash: STR, filename: STR} returns the file in form data.
6. POST: /translate_uname - Translate username into a user_id. Does not require authentication. {user_name: STR} Returns user_id.
7. POST: /delete-file - Deletes a file. Requires authenticaion. {user_id: STR, pass_hash: STR, filename: STR} returns status.
8. POST: /authenticate - Authenticate a user. {user_id: STR, pass_hash: STR} returns status

## Authentication
By defualt, the client stores authentication data in a file located in .clif/authdata. It needs to be recreated if you are working in a new directory.

## Usage - Client (Script)
~~~bash
client.py signup #Create authdata, and account
client.py login #Login to an existing account (Creates authdata)
client.py list #List all files owned by the user
client.py upload <file> #Upload a file
client.py download <file> #Download a file
client.py info #Get user info
client.py delete <file> #Delete a file
client.py logout #Logout and delete authdata (Deletes authdata)
~~~
In the executable, the client will list the options in the terminal using python's input function.

### AI usage
As per usual, I dont like using too much AI in my projects as i feel it is dishonest. I wrote most of the code with some
help from Jetbrains AI Assistant when i was getting stuck. Additionally, the text completions (Which i havent figured 
out how to disable yet) was used to speed up the process. AI was used in the server script and the client. 
