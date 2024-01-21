import os
import subprocess
import threading

# os.environ["KIVY_NO_CONSOLELOG"] = "1"

def start(command):
    subprocess.run(['python', command], check=True)



if __name__ == "__main__":


    new_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CLIENT_storage")

    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    threading.Thread(target=start, args=('main.py',)).start()
    threading.Thread(target=start, args=('mocapScreen.py',)).start()