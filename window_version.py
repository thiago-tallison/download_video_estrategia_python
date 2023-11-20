import os
import json
import requests
from tqdm import tqdm
import cv2

def truncate_filename(file_path, max_length=190):
    """
    Trunca o nome do arquivo no caminho para atender ao limite de comprimento do caminho do sistema operacional.

    Parameters:
    - file_path (str): O caminho completo do arquivo.
    - max_length (int): O comprimento máximo permitido para o caminho do arquivo.

    Returns:
    - str: O caminho do arquivo truncado.
    """
    if len(file_path) <= max_length:
        return file_path

    file_name, file_extension = os.path.splitext(file_path)
    truncated_length = max_length - len(file_extension) - len("...")

    if truncated_length < 0:
        # Não é possível truncar adequadamente, retornar o caminho original
        return file_path

    truncated_name = file_name[:truncated_length]
    truncated_path = f"{truncated_name}...{file_extension}"
    return truncated_path

# Criar o diretório raiz
root_dir = "aulas"
os.makedirs(root_dir, exist_ok=True)

# Listar todos os arquivos JSON no diretório atual
json_files = [f for f in os.listdir() if f.endswith(".json")]

def is_video_corrupted(file_path):
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return True

        ret, frame = cap.read()

        if not ret:
            return True

        if frame is None or frame.size == 0:
            return True

        return False

    except Exception:
        return True

# Iterar sobre cada arquivo JSON
for json_file in json_files:
    # Carregar o conteúdo do arquivo JSON com a codificação UTF-8
    with open(json_file, 'r', encoding='utf-8') as f:
        data_json = json.load(f)

    # Criar um subdiretório para cada disciplina usando a propriedade "nome"
    discipline_name = "".join(c for c in data_json["nome"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
    discipline_dir = os.path.join(root_dir, discipline_name)
    os.makedirs(discipline_dir, exist_ok=True)

    # Iterar sobre cada aula
    for i, aula in enumerate(data_json["aulas"], start=1):
        # Criar o subdiretório para a aula usando a propriedade "nome"
        aula_name = "".join(c for c in aula["nome"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
        aula_subdir = os.path.join(discipline_dir, aula_name)
        os.makedirs(aula_subdir, exist_ok=True)

        # Iterar sobre cada vídeo
        for j, video in enumerate(aula["videos"], start=1):
            # Verificar se o arquivo já existe e não está corrompido
            video_title = "".join(c for c in video["titulo"] if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
            file_path = os.path.join(aula_subdir, f"Video {j} - {video_title}.mp4")

            # Truncar o nome do arquivo para tornar o caminho mais curto
            truncated_file_path = truncate_filename(file_path)

            # Verificar se o arquivo já existe e se não está corrompido
            if os.path.exists(truncated_file_path) and not is_video_corrupted(truncated_file_path):
                print(f"O arquivo já existe e não está corrompido, pulando: {truncated_file_path}")
                continue

            # Tentar baixar a versão de acordo com a prioridade
            resolutions = ['720p', '480p', '360p']
            for resolution in resolutions:
                video_url = video["resolucoes"].get(resolution)
                if video_url:
                    break  # Usar a primeira versão disponível

            # Mostrar o log do vídeo que está sendo baixado
            print(f"Baixando ({j} de {len(aula['videos'])}): {truncated_file_path}")

            # Baixar o arquivo de vídeo usando o link fornecido
            with requests.get(video_url, stream=True) as response:
                # Usar o tqdm para mostrar o progresso do download
                with tqdm(total=int(response.headers.get('content-length', 0)), unit='B', unit_scale=True) as pbar:
                    with open(truncated_file_path, 'wb') as file:
                        for data_chunk in response.iter_content(chunk_size=1024):
                            file.write(data_chunk)
                            pbar.update(len(data_chunk))

print("Download concluído!")
