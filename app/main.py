from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from yandex_cloud.api import YandexCloudAPIClient
from yandex_cloud.models import mime_types
import io
import zipfile
import urllib.parse

app = Flask(__name__)
client = YandexCloudAPIClient()

# Глобальный словарь для кэширования
cache = {}


@app.route("/", methods=["GET"])
async def search():
    public_key = request.args.get(
        "public_key", ""
    )  # Получаем публичный ключ из параметров
    path = request.args.get("path")  # Получаем путь из параметров
    message = request.args.get("message")  # Получаем сообщение из параметров
    return render_template(
        "search.html", public_key=public_key, path=path, message=message
    )


@app.route("/view", methods=["GET"])
async def view():
    """Обрабатывает запросы для просмотра файлов и папок."""
    public_key = request.args.get("public_key")  # Получаем публичный ключ
    path = request.args.get("path", "")  # Получаем текущий путь
    file_type = request.args.get(
        "file_type", "Все файлы"
    )  # Получаем тип файла для фильтрации

    files = None

    # Формируем ключ для кэша
    cache_key = f"{public_key}|{path}"

    # Проверяем, есть ли данные в кэше
    if cache_key in cache:
        files = cache[cache_key]  # Загружаем данные из кэша
    else:
        if public_key:
            files = await client.get_files(
                public_key, path
            )  # Получаем файлы по публичному ключу и пути

            # Если файлы получены, сохраняем их в кэш
            if files is not None:
                cache[cache_key] = files

    # Если files равно None, перенаправляем на search с сообщением об ошибке
    if files is None:
        return redirect(
            url_for(
                "search",
                public_key=public_key,
                path=path,
                message="Хранилище не найдено.",
            )
        )

    # Фильтрация файлов по типу, если указан file_type
    if file_type and file_type != "Все файлы":
        files = [file for file in files if file.is_valid_mime_type(file_type)]

    return render_template(
        "view.html",
        files=files,
        public_key=public_key,
        current_path=path,
        mime_types=mime_types,
        file_type=file_type,
    )


@app.route("/folder/<path:folder_name>")
async def folder(folder_name):
    """Обрабатывает переход в папку."""
    public_key = request.args.get("public_key")
    return redirect(url_for("view", public_key=public_key, path=folder_name))


def get_file_name(download_url):
    parsed_url = urllib.parse.urlparse(download_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    return query_params.get("filename", [None])[0]


@app.route("/download_selected", methods=["POST"])
async def download_selected():
    selected_files = request.form.getlist(
        "selected_files"
    )  # Получаем список выбранных файлов
    if not selected_files:
        return "Не выбраны файлы для скачивания", 400

    # Создаем временный ZIP-архив
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for download_url in selected_files:
            # Скачиваем файл
            file_content = await client.download_file(download_url)

            # Извлекаем имя файла
            file_name = get_file_name(download_url)
            print(file_name)

            # Добавляем файл в архив
            zip_file.writestr(file_name, file_content)

    zip_buffer.seek(0)  # Возвращаем курсор в начало буфера
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name="selected_files.zip",
        mimetype="application/zip",
    )


@app.route("/download")
async def download_file():
    """Маршрут для скачивания файла по download_url"""
    download_url = request.args.get("download_url")  # Получаем ссылку на скачивание
    file_name = request.args.get("file_name")  # Имя файла

    if not download_url:
        return "Недостаточно параметров для скачивания", 400

    try:
        # Получаем содержимое файла с помощью твоего метода
        file_content = await client.download_file(download_url)

        if file_content is None:
            return "Ошибка при скачивании файла", 500

        # Используем BytesIO для передачи файла в памяти
        file_stream = io.BytesIO(file_content)
        file_stream.seek(0)  # Возвращаем курсор в начало файла

        # Отправляем файл клиенту
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=file_name,  # Имя файла для клиента
            mimetype="application/octet-stream",  # Тип файла
        )
    except Exception as e:
        return "Ошибка при скачивании файла", 500


if __name__ == "__main__":
    app.run(debug=True)
