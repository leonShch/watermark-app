from flask import Flask, request, jsonify, render_template
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response


# Главная страница - отдаем HTML
@app.route('/')
def index():
    return render_template('index.html')


# API endpoint для обработки изображений
@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process_image():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        logger.info("📨 Получен запрос на обработку изображения")

        if not request.is_json:
            return jsonify({"error": "Content-Type должен быть application/json"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        action = data.get('action')
        image_data = data.get('image')

        if not action or action not in ['add', 'remove']:
            return jsonify({"error": "Invalid action. Use 'add' or 'remove'"}), 400

        if not image_data:
            return jsonify({"error": "No image data provided"}), 400

        # Извлекаем base64 данные
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        logger.info(f"📊 Обработка изображения: {image.size[0]}x{image.size[1]}")

        if action == 'remove':
            result_image = remove_watermark(image)
            message = "Водяной знак успешно удален"
        else:
            text = data.get('text', 'Watermark')
            color = data.get('color', '#FFFFFF')
            opacity = int(data.get('opacity', 50))
            result_image = add_watermark(image, text, color, opacity)
            message = "Водяной знак успешно добавлен"

        # Конвертируем обратно в base64
        buffered = BytesIO()
        if result_image.mode == 'RGBA':
            result_image = result_image.convert('RGB')
        result_image.save(buffered, format="PNG")
        result_b64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            "success": True,
            "processedImage": f"data:image/png;base64,{result_b64}",
            "message": message
        })

    except Exception as e:
        logger.error(f"💥 Ошибка: {str(e)}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


# Health check endpoint
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "watermark-app"})


@app.route('/test')
def test():
    return jsonify({"message": "Сервер работает!", "status": "ok"})


# Функции обработки изображений
def remove_watermark(image):
    """Удаление водяного знака"""
    logger.info("🔧 Вызов remove_watermark")
    # TODO: ВСТАВЬТЕ ВАШ АЛГОРИТМ УДАЛЕНИЯ ВОДЯНОГО ЗНАКА
    return image


def add_watermark(image, text, color, opacity):
    """Добавление водяного знака"""
    logger.info("🔧 Вызов add_watermark")

    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)

    try:
        font_size = max(36, min(image.size) // 8)
        font = ImageFont.truetype("Arial.ttf", font_size)
    except:
        try:
            font = ImageFont.load_default()
        except:
            font = None

    # Позиционирование текста
    if font:
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 20
        text_height = 30

    x = (image.width - text_width) // 2
    y = (image.height - text_height) // 2

    # Цвет и прозрачность
    rgb = hex_to_rgb(color)
    alpha = int(255 * opacity / 100)
    fill_color = (*rgb, alpha)

    # Добавляем тень для лучшей читаемости
    if font:
        shadow_color = (0, 0, 0, alpha // 3)
        draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=fill_color)
    else:
        draw.text((x, y), text, fill=fill_color)

    return Image.alpha_composite(image, watermark)


def hex_to_rgb(hex_color):
    """Конвертация HEX в RGB"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


if __name__ == '__main__':
    # Используем порт 5001 вместо 5000
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print("=" * 60)
    print("🚀 Watermark App Server запущен!")
    print(f"📍 Порт: {port}")
    print(f"🔧 Режим отладки: {debug}")
    print("=" * 60)

    # Проверяем, доступен ли порт
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Порт {port} занят! Попробуйте другой порт.")
            print("💡 Попробуйте: python app.py --port 5002")
        else:
            raise e