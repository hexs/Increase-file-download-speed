import requests
import os
import sys
from multiprocessing import Pool, cpu_count
import math
import shutil
import subprocess

proxies = {
    'http': subprocess.run('git config --global http.proxy', capture_output=True, text=True).stdout.strip(),
    'https': subprocess.run('git config --global https.proxy', capture_output=True, text=True).stdout.strip()
}
chunk_size = 1024 * 1024  # 1MB chunks
num_processes = min(128, cpu_count())
temp_dir = 'temp'


# Function to download a chunk of the file
def download_chunk(args):
    start, end, chunk_number, url, filename = args
    part_file = f"{filename}.part{chunk_number}"
    full_path = os.path.join(temp_dir, part_file)

    if os.path.exists(full_path):
        return end - start + 1  # Return the size of the chunk

    headers = {'Range': f'bytes={start}-{end}'}
    try:
        response = requests.get(url, proxies=proxies, headers=headers, timeout=30)
        response.raise_for_status()
        with open(full_path, 'wb') as f:
            f.write(response.content)
        return len(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading chunk {chunk_number}: {e}")
        return 0


# Function to show download progress
def show_progress(downloaded, total):
    percent = (downloaded / total) * 100
    sys.stdout.write(f"\rProgress: {downloaded:,}/{total:,} bytes ({percent:.2f}%)")
    sys.stdout.flush()


# Main download function
def download(url, filename):
    if filename in os.listdir():
        return
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Get the total file size
    response = requests.head(url, proxies=proxies)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    if total_size == 0:
        print("Unable to determine file size. Exiting.")
        return

    print(f"Total file size: {total_size:,} bytes")
    chunk_count = math.ceil(total_size / chunk_size)

    chunks = [(i * chunk_size, min((i + 1) * chunk_size - 1, total_size - 1), i, url, filename)
              for i in range(chunk_count)]

    # check flie ที่โหลดมา ว่าครบไหม
    while len(os.listdir(temp_dir)) < chunk_count:
        downloaded = 0
        try:  # download ไฟล์มาก่อน หาก error ให้ข้ามไปก่อน
            # Download chunks in parallel
            with Pool(num_processes) as pool:
                for size in pool.imap_unordered(download_chunk, chunks):
                    downloaded += size
                    show_progress(downloaded, total_size)

        except Exception as e:
            print(f"\nAn error occurred: {e}")

        print(f'  {len(os.listdir(temp_dir))}/{chunk_count}')
    print()
    print("Download completed. Combining chunks...")

    # Combine chunks into a single file
    with open(os.path.join(temp_dir, filename), 'wb') as outfile:
        for i in range(chunk_count):
            chunk_file = os.path.join(temp_dir, f"{filename}.part{i}")
            if os.path.exists(chunk_file):
                with open(chunk_file, 'rb') as infile:
                    shutil.copyfileobj(infile, outfile)
                os.remove(chunk_file)
    print(f"File '{filename}' has been downloaded and assembled successfully in the '{temp_dir}' directory.")

    # Move the final file to the current directory
    final_path = os.path.join(temp_dir, filename)
    if os.path.exists(final_path):
        shutil.move(final_path, filename)
        print(f"File moved to current directory: {filename}")


if __name__ == '__main__':
    print('proxies', proxies)
    print('num_processes', num_processes)
    download(
        'https://downloads.raspberrypi.com/raspios_full_arm64/images/raspios_full_arm64-2024-07-04/2024-07-04-raspios-bookworm-arm64-full.img.xz',
        '2024-07-04-raspios-bookworm-arm64-full.img.xz'
    )
    download(
        'https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2024-07-04/2024-07-04-raspios-bookworm-armhf.img.xz',
        '2024-07-04-raspios-bookworm-armhf.img.xz'
    )