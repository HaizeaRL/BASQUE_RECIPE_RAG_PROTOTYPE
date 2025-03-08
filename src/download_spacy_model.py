import os
import sys
import yaml
from pathlib import Path
import requests
import subprocess

# Add the parent directory (where modules is located) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Read config file
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf = yaml.safe_load(Path(os.path.join(root_path, "config.yaml")).read_text())

# Create data folder
data_folder = os.path.join(root_path, conf["DATA_PATH"])
os.makedirs(data_folder, exist_ok=True)

# Define model path
model_file_name = conf["SPACY_MODEL"]
model_path = os.path.join(data_folder, model_file_name)

if not os.path.exists(model_path):
    print(f"{model_file_name} not found. Downloading...")
    response = requests.get(conf["SPACY_MODEL_URL"], stream=True)
    with open(model_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"{model_file_name} model saved in: {model_path}")
else:
    print(f"{model_file_name} already exists. Skipping download.")

# Install model
subprocess.check_call([sys.executable, '-m', 'pip', 'install', model_path])
print(f"{model_file_name} model installed correctly.")
