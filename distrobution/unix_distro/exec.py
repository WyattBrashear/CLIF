"""
    Hey verifiers. This is not part of the CLIF project but part of another of mine that's code i am using for execution.
"""
#!/usr/bin/env python3
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile

def actual_path():
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def main():
    """Main execution function."""
    path = os.getcwd()
    basepath = actual_path()
    source = os.path.join(basepath, "507ex-distro.507ex")
    hashmode = ""
    exec_hash = ""
    exec_id = ""
    with open(source, 'rb') as f:
        binary_lines = [f.readline() for _ in range(6)]
        string_lines = [line.decode('utf-8').strip() for line in binary_lines]
        for metadata in string_lines:
            if metadata.endswith("|507ex-id"):
                exec_id = metadata.split("|")[0]
            if metadata.endswith("|507ex-hashmode"):
                hashmode = metadata.split("|")[0]
            if metadata.endswith("|507ex-hash"):
                exec_hash = metadata.split("|")[0]

    #Check if the sourcefile is a .507ex file
    if not source.endswith(".507ex"):
        print("Source file must be a .507ex file.")
        sys.exit(1)

    #Remove .507ex-runtime if it exists
    if not os.path.exists(".507ex-runtime"):
        os.mkdir(".507ex-runtime")
    os.mkdir(f"{path}/.507ex-runtime/{exec_id}")
    #Attempt to copy the source file to the runtime directory
    try:
        shutil.copy(source, f"{path}/.507ex-runtime/{exec_id}/exec.zip")
    except FileNotFoundError:
        #If it does not exist, let the user know and sys.exit.
        print("Source executable not found. Are you sure it exists?")
        sys.exit(1)
    #Unzip the source file
    try:
        with zipfile.ZipFile(f'{path}/.507ex-runtime/{exec_id}/exec.zip', 'r') as zip_ref:
            zip_ref.extractall(f"{path}/.507ex-runtime/{exec_id}/exec")
    except zipfile.BadZipFile:
        print("An error occurred while attempting to run the executable.")
    try:
        # Hashing time!
        with open(f"{path}/.507ex-runtime/{exec_id}/exec.zip", "rb") as exc:
            lines = exc.readlines()[6:]
            exec_file_content = b"".join(lines)
            runtime_hash = hashlib.new(hashmode, exec_file_content).hexdigest()
        if runtime_hash != exec_hash:
            print("Hash mismatch detected. Executable may have been tampered with.")
            sys.exit(1)
        # Change the directory to .507ex-runtime/exec and generate hashes
        # for files inside that directory.
        os.chdir(f"{path}/.507ex-runtime/{exec_id}/exec")
        os.listdir(f"{path}/.507ex-runtime/{exec_id}/exec/")
        os.chdir(f"{path}/.507ex-runtime/{exec_id}/exec")
        # Open The runfile
        with open("./runfile", 'r', encoding='utf-8') as runfile:
            execfile = f"{runfile.read()}"
            subprocess.run(execfile, shell=True, check=False)
            #Once done, exit the .507ex environment.
            os.chdir(path)
    except KeyboardInterrupt:
        #Cleanly handle KeyboardInterrupts.
        print("\nExiting 507ex Environment")
        os.chdir(path)
        shutil.rmtree(f"{path}/.507ex-runtime")

    except Exception as e:
        print(f"An Error occurred while executing {source}. "
              "Please contact the developer for help.")
        print("\nExiting 507ex Environment")
        os.chdir(path)
        shutil.rmtree(f"{path}/.507ex-runtime")
if __name__ == "__main__":
    main()
