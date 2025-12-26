import os

DATASET = "olistbr/brazilian-ecommerce"
DOWNLOAD_PATH = "data"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

os.system(f"kaggle datasets download -d {DATASET} -p {DOWNLOAD_PATH} --unzip")
