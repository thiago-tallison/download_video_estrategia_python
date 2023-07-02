import json
import cv2
import os
import requests
from tqdm import tqdm


def load_json(file_path):
    with open(file_path) as file:
        return json.load(file)


def create_directory(directory_path):
    os.makedirs(directory_path, exist_ok=True)


def check_file_exists(file_path):
    return os.path.exists(file_path)


def download_file(url, file_path, title):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))

    file_progress_bar = tqdm(
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        miniters=1,
        desc="Baixando",
    )

    with open(file_path, "wb") as file:
        for data in response.iter_content(chunk_size=1024):
            # progress_bar.update(len(data))
            file_progress_bar.update(len(data))
            file.write(data)

    # progress_bar.close()
    file_progress_bar.close()
    print("Download concluído!")


def select_resolution(resolutions):
    preferred_resolution = None
    resolutions_list = ["720p", "480p"]

    for resolution in resolutions_list:
        if resolution in resolutions:
            preferred_resolution = resolution
            break

    if not preferred_resolution:
        preferred_resolution = next(iter(resolutions.keys()))

    return resolutions[preferred_resolution]


def is_video_corrupted(file_path):
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return True  # Unable to open the video file

        # Read the first frame
        ret, frame = cap.read()

        if not ret:
            return True  # Unable to read the first frame

        # Check if the frame is valid
        if frame is None or frame.size == 0:
            return True  # Invalid frame

        return False  # Video file is not corrupted

    except Exception:
        return True  # Error occurred during video file processing


def download_videos(data):
    for lesson in data:
        lesson_name = lesson["nome"]
        videos = lesson["videos"]
        directory_path = lesson_name

        create_directory(directory_path)
        print(f"Baixando vídeos da lição: {lesson_name}")

        video_number = 1
        for video in videos:
            title = video["titulo"]
            resolutions = video["resolucoes"]

            file_name = f"Video {video_number} - {title}.mp4"
            file_path = os.path.join(directory_path, file_name)
            video_url = select_resolution(resolutions=resolutions)

            video_number += 1

            if check_file_exists(file_path):
                if is_video_corrupted(file_path=file_path):
                    print(f"Vídeo corrompido: {file_name}")
                    print("Deletando....")
                    os.remove(file_path)
                else:
                    continue

            print(f"Baixando vídeo: {title}")
            download_file(video_url, file_path, title)

    print("Todos os vídeos foram baixados com sucesso.")


def main():
    file_path = "lessons.json"
    data = load_json(file_path)
    download_videos(data)


if __name__ == "__main__":
    main()
