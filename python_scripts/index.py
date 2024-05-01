from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from PIL import Image
import numpy as np
from better_profanity import profanity
import json
from werkzeug.utils import secure_filename
import os

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load the pre-trained Inception V3 model
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
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Создание директории, если ее нет
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'file_path': file_path}), 200
# Load your bad words detection model or mechanism
# bad_words_model = load_bad_words_model()

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
        print("Email sent successfully")  # Добавляем отладочный вывод
    except Exception as e:
        print("Error sending email:", e)  # Добавляем отладочный вывод об ошибке

@app.route('/process_data', methods=['GET', 'POST'])
def process_data():
    if request.method == 'POST':
        # Handle POST request
        data = request.json
        image_path = data.get('image_path')
        text = data.get('text')
        
        # Perform processing on data
        result = detect_nudity_and_bad_words(image_path, text)
        
        # Return result in JSON format
        if result["nudity_probability"] == "This content is forbidden" or "*" in result["censored_text"]:
    # Если контент запрещен или содержит цензурные слова, отправляем подтверждающее письмо
            send_confirmation_email("keksidisusjsusn@gmail.com")

        return jsonify(result)

    elif request.method == 'GET':
        # Handle GET request
        text = request.args.get('text')
        image_path = request.args.get('image_path')

        # Perform processing on data
        result = detect_nudity_and_bad_words(image_path, text)

        # Return result in JSON format
        return jsonify(result)

    else:
        # Return a message if the request method is not POST or GET
        return jsonify({"error": "Method not allowed"}), 405


def detect_nudity_and_bad_words(image_path, text):
    # Load the image using Pillow
    image = Image.open(image_path)
    if image is None:
        return "Error: Unable to load image.", 500

    # Resize the image to match the model input size
    input_size = (299, 299)
    image_resized = image.resize(input_size)

    # Convert the image to a NumPy array
    image_np = np.array(image_resized)

    # Preprocess the image for the model
    image_preprocessed = tf.keras.applications.inception_v3.preprocess_input(image_np)

    # Perform nudity classification
    nudity_predictions = model.predict(image_preprocessed.reshape(1, *image_preprocessed.shape))

    # Decode the nudity prediction
    decoded_nudity_predictions = tf.keras.applications.inception_v3.decode_predictions(nudity_predictions, top=1)[0]
    predicted_nudity_class = decoded_nudity_predictions[0][1]
    nudity_probability = float(decoded_nudity_predictions[0][2])  # Convert to Python float

    # Check if the text contains profanity and censor it
    censored_text = profanity.censor(text)
    contains_profanity = profanity.contains_profanity(text)

    return {
        "predicted_nudity_class": predicted_nudity_class,
        "nudity_probability": "This content is forbidden" if nudity_probability > 0.50 else "Everything is alright",
        "censored_text": censored_text,
        "contains_profanity": contains_profanity
    }

if __name__ == "__main__":
    app.run(debug=True)
