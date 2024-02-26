import docker
import random
import string
import os
import socket
from flask_cors import CORS
import webbrowser
from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = docker.from_env()

def generate_random_username():
    return ''.join(random.choices(string.ascii_lowercase, k=8))

def generate_random_port():
    return random.randint(8000, 9000)

def generate_random_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def set_directory_permissions(username):
    try:
        os.system(f"sudo chown -R jovyan:jovyan /home/{username}/work")
        os.system(f"sudo chmod -R 777 /home/{username}/work")
    except Exception as e:
        print(f"Error setting directory permissions: {e}")

def create_user_and_jupyter(username, token):
    folder_path = f'/home/{username}/work'
    os.makedirs(folder_path, exist_ok=True)
    port = generate_random_port()
    try:
        os.chmod(folder_path, 0o777)  # Set permissions to allow read, write, and execute for all
        
        # Build Docker image with username as the image name (converted to lowercase)
        dockerfile_path = os.path.abspath('Dockerfile')  # Assuming Dockerfile is in the same directory
        image_name = f"juyel-{username.lower()}"
        client.images.build(path=os.path.dirname(dockerfile_path), dockerfile=dockerfile_path, tag=image_name)
        
        # Create Docker container with the built image
        container = client.containers.run(
            image=image_name,
            detach=True,
            ports={'8888/tcp': port},
            environment={'NB_UID': '0', 'JUPYTER_TOKEN': token},
            volumes={folder_path: {'bind': '/home/jovyan/work', 'mode': 'rw'}}
        )
    except Exception as e:
        return f"Error: Failed to create container for user '{username}': {str(e)}"

    server_ip = 'platform.learningpath.ai'  # Replace with your server's IP address
    notebook_url = f"http://{server_ip}:{port}/?username={username}"
    print(notebook_url)
    return f"Jupyter Notebook for user '{username}' is running at: {notebook_url}"


@app.route('/create_users', methods=['POST'])
def create_users():
    data = request.get_json()
    token = data.get('token')
    username = data.get('username')
    if not token:
        return jsonify({"error": "Token is required"}), 400
    if not username:
        return jsonify({"error": "Username is required"}), 400

    result = create_user_and_jupyter(username, token)
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(debug=True, port=5443, host='platform.learningpath.ai')

