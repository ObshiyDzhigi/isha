from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from PIL import Image
import numpy as np
from better_profanity import profanity
import json
from werkzeug.utils import secure_filename
import os
import cv2
import pytesseract
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})
pytesseract.pytesseract.tesseract_cmd = "D:\\tess\\tesseract.exe"
model = tf.keras.applications.InceptionV3(weights='imagenet')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'file_path': file_path}), 200

def send_confirmation_email(receiver_email):
    sender_email = "zhigazh2017@gmail.com"
    password = "tozxzpsswjtkjbqj"

    subject = "Confirmation Email"
    body = f"You have to confirm the publication of this post. Click <a href='http://localhost:3000?approved=true'>here</a>"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("Email sent successfully")  
    except Exception as e:
        print("Error sending email:", e)  

def detect_video_nudity_and_bad_words(video_path):
    # Открыть видео
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    total_nudity_probability = 0

    # Обработка каждого кадра
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Обработка каждого кадра как изображения
        frame_count += 1
        resized_frame = cv2.resize(frame, (299, 299))
        preprocessed_frame = tf.keras.applications.inception_v3.preprocess_input(resized_frame)
        predictions = model.predict(preprocessed_frame.reshape(1, *preprocessed_frame.shape))
        nudity_probability = tf.keras.applications.inception_v3.decode_predictions(predictions, top=1)[0][0][2]
        total_nudity_probability += nudity_probability

    # Среднее значение вероятности неприемлемого контента
    average_nudity_probability = total_nudity_probability / frame_count

    return "Video", average_nudity_probability, "", False

# Обработчик маршрута для обработки данных
@app.route('/process_data', methods=['GET', 'POST'])
def process_data():
    if request.method == 'POST':
        # Handle POST request
        data = request.json
        image_path = data.get('image_path')
        text = data.get('text')

        # Вызов функции обработки изображения или видео
        if image_path.lower().endswith(('.mp4', '.avi', '.mkv')):
            result = detect_video_nudity_and_bad_words(image_path)
        else:
            result = detect_nudity_and_bad_words(image_path, text)

        # Если содержимое запрещено, отправить электронное письмо подтверждения
        print("Result:", result)
        print("Type of Result:", type(result))

        if isinstance(result, dict) and result.get('nudity_probability') == "This content is forbidden":
            send_confirmation_email("keksidisusjsusn@gmail.com")

        return jsonify(result)

    elif request.method == 'GET':
        text = request.args.get('text')
        image_path = request.args.get('image_path')

        result = detect_nudity_and_bad_words(image_path, text)

        return jsonify(result)

    else:
        return jsonify({"error": "Method not allowed"}), 405



def load_profanity_words(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        profanity_words = [line.strip() for line in file]
    return profanity_words

def detect_nudity_and_bad_words(image_path, text):
    # Загрузка списка запрещенных слов из файла
    profanity_words = load_profanity_words('C:\\Users\\Zhiger\\Desktop\\nudity-recognizer-main\\python_scripts\\profanity_words.txt')

    # Обработка изображения
    image = Image.open(image_path)
    if image is None:
        return "Error: Unable to load image.", 500
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    input_size = (299, 299)
    image_resized = image.resize(input_size)
    image_np = np.array(image_resized)
    image_preprocessed = tf.keras.applications.inception_v3.preprocess_input(image_np)
    nudity_predictions = model.predict(image_preprocessed.reshape(1, *image_preprocessed.shape))
    decoded_nudity_predictions = tf.keras.applications.inception_v3.decode_predictions(nudity_predictions, top=1)[0]
    predicted_nudity_class = decoded_nudity_predictions[0][1]
    nudity_probability = float(decoded_nudity_predictions[0][2])

    # Проверка текста на изображении
    extracted_text = pytesseract.image_to_string(image)
    censored_text = profanity.censor(extracted_text)
    contains_profanity = any(word in extracted_text.lower() for word in profanity_words)

    if contains_profanity:
        # Если на изображении обнаружены запрещенные слова, вернуть текст изображения
        return {
            "predicted_nudity_class": predicted_nudity_class,
            "nudity_probability": "This content is forbidden" if nudity_probability > 0.50 else "Everything is alright",
            "censored_text": censored_text,
            "contains_profanity": contains_profanity
        }
    else:
        # Иначе вернуть текст, введенный пользователем
        censored_user_text = profanity.censor(text)
        user_contains_profanity = any(word in text.lower() for word in profanity_words)
        return {
            "predicted_nudity_class": predicted_nudity_class,
            "nudity_probability": "This content is forbidden" if nudity_probability > 0.50 else "Everything is alright",
            "censored_text": censored_user_text,
            "contains_profanity": user_contains_profanity
        }
if __name__ == "__main__":
    app.run(debug=True)