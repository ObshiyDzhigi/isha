import tensorflow as tf
from PIL import Image
import numpy as np
from better_profanity import profanity

# Load the pre-trained Inception V3 model
model = tf.keras.applications.InceptionV3(weights='imagenet')

# Load your bad words detection model or mechanism
# bad_words_model = load_bad_words_model()

profanity.load_censor_words_from_file('censor.txt')


def detect_nudity_and_bad_words(image_path):
    # Load the image using Pillow
    image = Image.open(image_path)
    if image is None:
        print("Error: Unable to load image.")
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
    nudity_probability = decoded_nudity_predictions[0][2]

    # Check if the text contains profanity and censor it
    text = input("Enter a text to check for profanity: ")
    censored_text = profanity.censor(text)
    contains_profanity = profanity.contains_profanity(text)

    return predicted_nudity_class, nudity_probability, censored_text, contains_profanity

if __name__ == "__main__":
    image_path = 'C:\\Users\\user\\Desktop\\Desktop\\projects\\Nudity_Detector\\assets\\ants.jpg'

    predicted_nudity_class, nudity_probability, censored_text, contains_profanity = detect_nudity_and_bad_words(image_path)
    print(f"Predicted Nudity Class: {predicted_nudity_class}")
    print(f"Nudity Probability: {nudity_probability:.4f}")
    print(f"Censored Text: {censored_text}")
    print(f"Contains Profanity: {contains_profanity}")
