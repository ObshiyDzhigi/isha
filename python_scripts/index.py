from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from PIL import Image
import numpy as np
from better_profanity import profanity
import json
from werkzeug.utils import secure_filename
import os
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

@app.route('/process_data', methods=['GET', 'POST'])
def process_data():
    if request.method == 'POST':
        # Handle POST request
        data = request.json
        image_path = data.get('image_path')
        text = data.get('text')
        

        result = detect_nudity_and_bad_words(image_path, text)
        
   
        if result["nudity_probability"] == "This content is forbidden" or "*" in result["censored_text"]:

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