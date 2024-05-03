import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf
from better_profanity import profanity
import speech_recognition as sr
import cv2

# Load the pre-trained Inception V3 model
model = tf.keras.applications.InceptionV3(weights='imagenet')

# Initialize Tkinter
root = tk.Tk()
root.title("SafeNet")

# Create a custom style for buttons
button_style = {'font': ('Arial', 12), 'bg': 'lightblue'}

def get_text_input():
    return text_entry.get()

def speech_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Говорите...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="ru-RU, en-US")
        return text
    except sr.UnknownValueError:
        print("Не разобрал вашу речь, повторите ещё раз!")
        return ""

def detect_nudity_and_bad_words(image_or_video, text=None):
    if isinstance(image_or_video, str):  # if it's a path
        if image_or_video.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return detect_image_nudity_and_bad_words(image_or_video, text)
        elif image_or_video.lower().endswith(('.mp4', '.avi', '.mkv')):
            return detect_video_nudity_and_bad_words(image_or_video)
        else:
            print("Unsupported file format")
            return None
    else:  # assume it's a video
        return detect_video_nudity_and_bad_words(image_or_video)

def detect_image_nudity_and_bad_words(image_path, text=None):
    # Load the image using Pillow
    image = Image.open(image_path)
    if image is None:
        print("Ошибка: не получается загрузить изображение")
        return

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
    if text:
        censored_text = profanity.censor(text)
        contains_profanity = profanity.contains_profanity(text)
    else:
        censored_text = ""
        contains_profanity = False

    return predicted_nudity_class, nudity_probability, censored_text, contains_profanity

def detect_video_nudity_and_bad_words(video_path):
    # Open the video capture
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    total_nudity_probability = 0

    # Process each frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Perform nudity classification on each frame (similar to image processing)
        frame_count += 1
        resized_frame = cv2.resize(frame, (299, 299))
        preprocessed_frame = tf.keras.applications.inception_v3.preprocess_input(resized_frame)
        predictions = model.predict(preprocessed_frame.reshape(1, *preprocessed_frame.shape))
        nudity_probability = tf.keras.applications.inception_v3.decode_predictions(predictions, top=1)[0][0][2]
        total_nudity_probability += nudity_probability

    # Calculate the average nudity probability over all frames
    average_nudity_probability = total_nudity_probability / frame_count

    return "Video", average_nudity_probability, "", False

def browse_image():
    filename = filedialog.askopenfilename(filetypes=[("Image files", ".jpg;.jpeg;.png;.gif")])
    if filename:
        # Display the image
        image = Image.open(filename)
        image.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo  # Keep a reference to avoid garbage collection
        image_label.filename = filename  # Store the filename as an attribute

def browse_video():
    filename = filedialog.askopenfilename(filetypes=[("Video files", ".mp4;.avi;*.mkv")])
    if filename:
        # Обрабатываем выбранное видео
        process_video(filename)

def process_video(video_path):
    # Обработка видео на запрещенный контент
    predicted_nudity_class, nudity_probability, censored_text, contains_profanity = detect_nudity_and_bad_words(video_path)
    
    # Вывод результатов на result_label
    result_label.config(text=f"Прогнозируемый класс: {predicted_nudity_class}\n"
                             f"Вероятность запрещенного контента: {'Такой контент недопустим' if nudity_probability > 0.50 else f'{nudity_probability:.2f} все нормально'}\n"
                             )

def send_text():
    text = get_text_input()
    if hasattr(image_label, 'filename'):
        filename = image_label.filename
        load_image_with_text(filename, text)

def load_image_with_text(filename, text):
    predicted_nudity_class, nudity_probability, censored_text, contains_profanity = detect_nudity_and_bad_words(filename, text)
    result_label.config(text=f"Прогнозируемый класс: {predicted_nudity_class}\n"
                             f"Вероятность запрещенного контента: {'Такой контент недопустим' if nudity_probability > 0.50 else f'{nudity_probability:.2f} все нормально'}\n"
                             f"Цензурированный текст: {censored_text}\n"
                             f"Содержит ли ненормативную лексику: {contains_profanity}")

# Create GUI elements
browse_image_button = tk.Button(root, text="Выбрать изображение", command=browse_image, **button_style)
browse_image_button.pack(fill=tk.X)

browse_video_button = tk.Button(root, text="Выбрать видео", command=browse_video, **button_style)
browse_video_button.pack(fill=tk.X)

text_entry = tk.Entry(root, width=50, **button_style)
text_entry.pack(fill=tk.X)

speech_button = tk.Button(root, text="Использовать голосовой ввод", command=lambda: text_entry.insert(tk.END, speech_input()), **button_style)
speech_button.pack(fill=tk.X)

send_button = tk.Button(root, text="Отправить", command=send_text, **button_style)
send_button.pack(fill=tk.X)

image_label = tk.Label(root)
image_label.pack()

result_label = tk.Label(root, text="", **button_style)
result_label.pack(fill=tk.X)

root.mainloop()