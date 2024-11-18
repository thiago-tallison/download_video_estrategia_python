import os
import json
import requests
from tqdm import tqdm
import cv2
import concurrent.futures
from datetime import datetime
import threading

# Lock para sincronizar a barra de progresso
tqdm_lock = threading.Lock()

def truncate_filename(file_path, max_length=190):
    """
    Trunca o nome do arquivo no caminho para atender ao limite de comprimento do caminho do sistema operacional.
    """
    if len(file_path) <= max_length:
        return file_path

    file_name, file_extension = os.path.splitext(file_path)
    truncated_length = max_length - len(file_extension) - len("...")

    if truncated_length < 0:
        return file_path

    truncated_name = file_name[:truncated_length]
    truncated_path = f"{truncated_name}...{file_extension}"
    return truncated_path

def is_video_corrupted(file_path):
    """
    Verifica se um arquivo de vídeo está corrompido.
    """
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return True

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None or frame.size == 0:
            return True

        return False

    except Exception:
        return True

def download_video(video_info):
    """
    Baixa um único vídeo.
    
    Parameters:
    - video_info (dict): Informações do vídeo a ser baixado
    """
    file_path = video_info['file_path']
    video_url = video_info['video_url']
    title = video_info['title']
    
    try:
        # Verificar se o arquivo já existe e não está corrompido
        if os.path.exists(file_path) and not is_video_corrupted(file_path):
            with tqdm_lock:
                print(f"Arquivo já existe: {file_path}")
            return

        # Criar a pasta se não existir
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with tqdm_lock:
            print(f"Baixando {file_path}...")

        # Realizar o download com progresso
        with requests.get(video_url, stream=True) as response:
            total_size = int(response.headers.get('content-length', 0))
            
            with tqdm_lock:
                progress_bar = tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc='',
                    bar_format='{bar}{percentage:>3.0f}% | {rate_fmt}',
                    leave=True
                )

            with open(file_path, 'wb') as file:
                for data_chunk in response.iter_content(chunk_size=1024):
                    file.write(data_chunk)
                    with tqdm_lock:
                        progress_bar.update(len(data_chunk))

            with tqdm_lock:
                progress_bar.close()

    except Exception as e:
        with tqdm_lock:
            print(f"Erro ao baixar o vídeo {title}: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)

def process_course(course_data, root_dir="aulas"):
    """
    Processa um curso e prepara a lista de vídeos para download.
    """
    discipline_name = "".join(c for c in course_data["nome"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
    discipline_dir = os.path.join(root_dir, discipline_name)
    
    videos_to_download = []
    
    for aula in course_data["aulas"]:
        aula_name = "".join(c for c in aula["nome"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
        aula_subdir = os.path.join(discipline_dir, aula_name)

        for j, video in enumerate(aula["videos"], start=1):
            video_title = "".join(c for c in video["titulo"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
            file_path = os.path.join(aula_subdir, f"Video {j} - {video_title}.mp4")
            truncated_file_path = truncate_filename(file_path)

            # Encontrar a melhor resolução disponível
            for resolution in ['720p', '480p', '360p']:
                video_url = video["resolucoes"].get(resolution)
                if video_url:
                    videos_to_download.append({
                        'file_path': truncated_file_path,
                        'video_url': video_url,
                        'title': video_title
                    })
                    break

    return videos_to_download

def main():
    # Criar o diretório raiz
    root_dir = "aulas"
    os.makedirs(root_dir, exist_ok=True)

    # Configurar o número máximo de downloads simultâneos
    max_concurrent_downloads = 5

    # Listar todos os arquivos JSON no diretório atual
    json_files = [f for f in os.listdir() if f.endswith(".json")]

    start_time = datetime.now()
    print(f"Iniciando downloads em {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    for json_file in json_files:
        try:
            # Carregar o conteúdo do arquivo JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)

            # Garantir que courses_data seja uma lista
            if not isinstance(courses_data, list):
                courses_data = [courses_data]

            # Processar cada curso e coletar todos os vídeos para download
            all_videos = []
            for course_data in courses_data:
                videos = process_course(course_data, root_dir)
                all_videos.extend(videos)

            # Realizar downloads em paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_downloads) as executor:
                executor.map(download_video, all_videos)

        except Exception as e:
            print(f"Erro ao processar o arquivo {json_file}: {str(e)}")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nDownload concluído em {duration.total_seconds():.2f} segundos!")
    print(f"Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Fim: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()