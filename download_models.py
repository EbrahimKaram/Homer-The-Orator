import os
import requests
from tqdm import tqdm

MODELS_URLS = {
    "kokoro-v1.0.int8.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
}

def download_file(url, filename):
    if os.path.exists(filename):
        print(f"✅ {filename} already exists. Skipping.")
        return

    print(f"⬇️ Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
    print(f"✅ Downloaded {filename} successfully!\n")

if __name__ == "__main__":
    print("Starting Kokoro models download...")
    for filename, url in MODELS_URLS.items():
        download_file(url, filename)
    print("🎉 All models are ready!")


# Homer reads the web for you. Send any article link or paste text directly, and Homer will reply with a voice note so you can listen instead of read.