from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from yandex_cloud.api import YandexCloudAPIClient
from yandex_cloud.models import mime_types
import io
import zipfile
import urllib.parse
from utils import setup_logger
from loguru import logger

# Инициализация приложения Flask
app = Flask(__name__)
client = YandexCloudAPIClient()

# Глобальный словарь для кэширования
cache = {}

# Настройка логирования
setup_logger()


@app.route("/", methods=["GET"])
async def search():
    """Отображает страницу поиска с необязательными параметрами."""
    public_key = request.args.get("public_key", "")  # Получаем публичный ключ
    path = request.args.get("path")  # Получаем путь
    message = request.args.get("message")  # Получаем сообщение
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

    # Формируем ключ для кэша по текущему запросу
    cache_key = f"{public_key}|{path}"

    # Пытаемся получить файлы из кэша
    files = cache.get(cache_key)

    # Загружаем файлы, если они отсутствуют в кэше
    if files is None and public_key:
        try:
            files = await client.get_files(public_key, path)
            if files is not None:
                cache[cache_key] = files  # Кэшируем файлы для будущих запросов
        except Exception as e:
            logger.error(f"Ошибка при получении файлов: {e}")  # Логируем ошибку
            return redirect(
                url_for(
                    "search",
                    public_key=public_key,
                    path=path,
                    message="Ошибка при получении файлов.",
                )
            )

    # Перенаправляем на поиск, если файлы не удалось получить
    if files is None:
        return redirect(
            url_for(
                "search",
                public_key=public_key,
                path=path,
                message="Хранилище не найдено.",
            )
        )

    # Фильтруем файлы по типу, если это указано
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
    public_key = request.args.get("public_key")  # Получаем публичный ключ
    return redirect(url_for("view", public_key=public_key, path=folder_name))


def get_file_name(download_url):
    """Извлекает имя файла из URL для скачивания."""
    parsed_url = urllib.parse.urlparse(download_url)  # Парсим URL
    query_params = urllib.parse.parse_qs(parsed_url.query)  # Получаем параметры запроса
    return query_params.get("filename", [None])[0]  # Возвращаем имя файла


@app.route("/download_selected", methods=["POST"])
async def download_selected():
    """Скачивает выбранные файлы в виде ZIP-архива."""
    selected_files = request.form.getlist(
        "selected_files"
    )  # Получаем список выбранных файлов

    if not selected_files:
        return (
            "Не выбраны файлы для скачивания",
            400,
        )  # Возвращаем ошибку, если файлы не выбраны

    try:
        # Создаем временный ZIP-архив
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for download_url in selected_files:
                # Скачиваем файл
                file_content = await client.download_file(download_url)

                # Извлекаем имя файла
                file_name = get_file_name(download_url)

                if file_name and file_content is not None:
                    zip_file.writestr(file_name, file_content)  # Добавляем файл в архив
                else:
                    logger.warning(
                        f"Не удалось скачать или извлечь имя файла для URL: {download_url}"
                    )

        zip_buffer.seek(0)  # Сбрасываем курсор буфера в начало
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="selected_files.zip",  # Имя файла для загрузки
            mimetype="application/zip",  # MIME-тип файла
        )

    except Exception as e:
        logger.error(f"Ошибка при создании ZIP-файла: {e}")  # Логируем ошибку
        return "Ошибка при создании архива.", 500


@app.route("/download")
async def download_file():
    """Маршрут для скачивания файла по URL для скачивания."""
    download_url = request.args.get("download_url")  # Получаем URL для скачивания
    file_name = request.args.get("file_name")  # Получаем имя файла

    if not download_url:
        return (
            "Недостаточно параметров для скачивания",
            400,
        )  # Возвращаем ошибку, если URL не указан

    try:
        # Получаем содержимое файла
        file_content = await client.download_file(download_url)

        if file_content is None:
            return (
                "Ошибка при скачивании файла",
                500,
            )  # Возвращаем ошибку, если не удалось скачать файл

        # Используем BytesIO для передачи файла в памяти
        file_stream = io.BytesIO(file_content)
        file_stream.seek(0)  # Сбрасываем курсор в начало

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=file_name,  # Имя файла для клиента
            mimetype="application/octet-stream",  # MIME-тип файла
        )

    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")  # Логируем ошибку
        return "Ошибка при скачивании файла", 500


if __name__ == "__main__":
    app.run(debug=True)  # Запуск приложения в режиме отладки
