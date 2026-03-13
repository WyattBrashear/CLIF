import hashlib

import os
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['upload', 'download', 'list', 'login', 'logout', 'delete', 'signup', 'info'])
parser.add_argument('file', nargs='?')
args = parser.parse_args()

try:
    with open(".clif/authdata", "r") as f:
        user_id = f.readline().strip()
        passhash = f.readline().strip()
        server_address = f.readline().strip()
        username = f.readline().strip()
except:
    pass


if args.action == 'signup':
    if os.path.exists(".clif/authdata"):
        print("You are already logged in!")
        exit()
    server_address = input("Enter the server address:\n")
    uname1 = input("Enter your username:\n")
    pass1 = hashlib.sha256(input("Enter your password:\n").encode()).hexdigest()
    r = requests.post(f"{server_address}/register", json={'username': uname1, 'password': pass1, 'password_hash': 'sha256'})
    if r.status_code == 200:
        print("User Created")
        try:
            os.mkdir(".clif")
        except:
            pass

        with open(".clif/authdata", "w") as f:
            f.write(r.json()['user_id'])
            f.write("\n")
            f.write(pass1)
            f.write("\n")
            f.write(server_address)
            f.write("\n")
            f.write(uname1)
    else:
        print("User Creation Failed")

if args.action == 'login':
    try:
        server_address = input("Enter the server address:\n")
        r = requests.post(f"{server_address}/translate_uname", json={'user_name': input("Enter your username:\n")})
        user_id = r.json()['message']
        passhash = hashlib.sha256(input("Enter your password:\n").encode()).hexdigest()
        r = requests.post(f"{server_address}/authenticate", json={'user_id': user_id, 'pass_hash': passhash})
    except:
        print("An error occurred while logging you in.")
        exit()
    if r.json()['status'] == "success":
        print("Login Successful")
        try:
            os.mkdir(".clif")
            with open(".clif/authdata", "w") as f:
                f.write(user_id)
                f.write("\n")
                f.write(passhash)
                f.write("\n")
                f.write(server_address)
                f.write("\n")
                f.write(r.json()['user_name'])
        except:
            pass
    else:
        print("Authentication Failed!")
        exit()

if args.action == 'logout':
    if input("Are you sure you want to logout? (y/n)\n").lower() == "y":
        os.remove(".clif/authdata")
    else:
        pass
if args.action == 'upload':
    if os.path.exists(".clif/authdata"):
        with open(args.file, "rb") as f:
            r = requests.post(f"{server_address}/upload_file", files=[('file', f)], data={'user_id': user_id, 'pass_hash': passhash, 'filename': args.file})
            print(r.json()['message'])

if args.action == 'download':
    if os.path.exists(".clif/authdata"):
        r = requests.post(f"{server_address}/retrieve-file", json={'user_id': user_id, 'pass_hash': passhash, 'filename': args.file})
        if r.status_code != 200:
            print("An error occurred while downloading the file.")
            exit()
        with open(args.file, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {args.file} successfully")
    else:
        print("You are not logged in!")
        exit()
if args.action == 'list':
    if os.path.exists(".clif/authdata"):
        r = requests.post(f"{server_address}/list", json={'user_id': user_id, 'pass_hash': passhash})
        directories = r.json()['directories']
        print(f"Files currently owned by {username}:")
        for directory in directories:
            print(directory[0])
    else:
        print("You are not logged in!")
        exit()
if args.action == 'delete':
    if os.path.exists(".clif/authdata"):
        r = requests.post(f"{server_address}/delete-file", json={'user_id': user_id, 'pass_hash': passhash, 'filename': args.file})
        print(r.json()['message'])
    else:
        print("You are not logged in!")
        exit()
if args.action == 'info':
    r = requests.post(f"{server_address}/fetch-userdata", json={'user_id': user_id, 'pass_hash': passhash})
    if r.status_code != 200:
        print("An error occurred while fetching user data.")
        exit()
    print(f"""User Statistics for {username}:
---------------------------------
            Username: {username}
            User ID: {user_id}
            Used Storage: {r.json()['used_data']} bytes
            Allocation Limit: {r.json()['allocation_limit']} bytes
            Percentage of storage used: {r.json()['data_percent']}%
""")
