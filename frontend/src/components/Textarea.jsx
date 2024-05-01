import React, { useState, useRef } from 'react';
import axios from 'axios';

const Textarea = () => {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [imageFile, setImageFile] = useState(null);
    const [videoFile, setVideoFile] = useState(null);
    const recognition = useRef(null);

    const handleSubmit = async () => {
        try {
            let imagePath = null;
            let videoPath = null;

            if (imageFile) {
                const formData = new FormData();
                formData.append('file', imageFile);

                const fileResponse = await axios.post('http://localhost:5000/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                imagePath = fileResponse.data.file_path;
            }

            if (videoFile) {
                const formData = new FormData();
                formData.append('file', videoFile);

                const fileResponse = await axios.post('http://localhost:5000/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                videoPath = fileResponse.data.file_path;
            }

            const response = await axios.post('http://localhost:5000/process_data', {
                text: text || recognition.currentTranscript,
                image_path: imagePath,
                video_path: videoPath
            });

            console.log(response.data);
            setResult(response.data);
        } catch (error) {
            console.error('Ошибка отправки данных:', error);
        }
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file.type.startsWith('image')) {
            setImageFile(file);
        } else if (file.type.startsWith('video')) {
            setVideoFile(file);
        }
    };

    const handleChange = (event) => {
        setText(event.target.value);
    };

    const handleSpeechRecognition = () => {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Распознавание речи не поддерживается в вашем браузере.");
            return;
        }

        if (recognition.current) {
            recognition.current.abort();
        }

        const recognitionInstance = new window.webkitSpeechRecognition();
        recognitionInstance.lang = 'ru-RU';
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = true;

        recognitionInstance.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map((result) => result[0])
                .map((result) => result.transcript)
                .join('');

            setText(transcript);
            recognition.currentTranscript = transcript;
        };

        recognitionInstance.onend = () => {
            console.log('Распознавание речи завершено.');
            handleSubmit(); // Автоматически отправляем текст после окончания распознавания речи
        };

        recognitionInstance.start();
        recognition.current = recognitionInstance;
    };

    return (
        <div className="container">
            <h2>Text Area</h2>
            <div className="form-group">
                <textarea
                    className="form-control"
                    value={text}
                    onChange={handleChange}
                    placeholder="Enter your text here..."
                />
            </div>
            <div className="form-group">
                <label htmlFor="fileInput">Upload Image:</label>
                <input
                    type="file"
                    className="form-control-file"
                    id="fileInput"
                    onChange={handleFileChange}
                    accept="image/*,video/*"
                />
            </div>
            <button className="btn btn-primary mr-2" onClick={handleSpeechRecognition}>
                Recognize Speech
            </button>
            <button className="btn btn-primary" onClick={handleSubmit}>
                Submit
            </button>
            {result && (
                <div className="result">
                    <h3>Result:</h3>
                    <p>Predicted Nudity Class: {result.predicted_nudity_class}</p>
                    <p>Nudity Probability: {result.nudity_probability}</p>
                    <p>Censored Text: {result.censored_text}</p>
                    <p>Contains Profanity: {result.contains_profanity.toString()}</p>
                    <div className='ugu'>
                    {result && (result.nudity_probability === "This content is forbidden" || result.censored_text.includes("***")) && (
                        <div>
                            Your post is currently awaiting confirmation from the admins.
                        </div>
                    )}
                </div>
                </div>
            )}
        </div>
    );
};

export default Textarea;
