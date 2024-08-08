import requests
import os
import subprocess

proxies = {
    'http': subprocess.run('git config --global http.proxy', capture_output=True, text=True).stdout.strip(),
    'https': subprocess.run('git config --global https.proxy', capture_output=True, text=True).stdout.strip()
}
chunk_size = 1024 * 1024  # 1MB chunks


def normal_download(url, file_name):
    response = requests.get(url, proxies=proxies)
    with open(file_name, 'wb') as file:
        file.write(response.content)
    print(f"File '{file_name}' has been downloaded successfully.")


def download_file(url, file_name):
    response = requests.get(url, stream=True, proxies=proxies)

    total_size = response.headers.get('content-length')
    if total_size is None or int(total_size) == 0:
        print(
            "Warning: Content-Length is missing or zero. Download progress will be estimated based on received chunks.")
        total_size = None
    else:
        total_size = int(total_size)

    # Check if the file already exists and get its size
    if os.path.exists(file_name):
        downloaded_size = os.path.getsize(file_name)
    else:
        downloaded_size = 0

    # Open the file in append-binary mode
    with open(file_name, 'ab') as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)
                if total_size:
                    print(f"Downloaded: {downloaded_size / total_size * 100:.2f}%")
                else:
                    print(f"Downloaded: {downloaded_size} bytes")

    print(f"File '{file_name}' has been downloaded successfully.")


if __name__ == '__main__':
    url = 'https://github.com/JJ17025/Auto-Inspection/archive/refs/heads/m2.zip'
    file_name = 'Auto-Inspection.zip'
    download_file(url, file_name)
