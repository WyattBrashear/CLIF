import hashlib

import os
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['upload', 'download', 'listdir', 'login', 'logout', 'delete', 'signup'])
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
        print("An error occured while logging you in.")
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