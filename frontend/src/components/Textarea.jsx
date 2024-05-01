import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const Textarea = () => {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [imageFile, setImageFile] = useState(null);
    const [posts, setPosts] = useState(() => {
        const savedPosts = localStorage.getItem('posts');
        return savedPosts ? JSON.parse(savedPosts) : [];
    });
    const [lastText, setLastText] = useState('');
    const [lastImageFile, setLastImageFile] = useState(null);
    const recognition = useRef(null);

    useEffect(() => {
        const savedResult = localStorage.getItem('result');
        if (savedResult) {
            setResult(JSON.parse(savedResult));
        }

        const savedPosts = localStorage.getItem('posts');
        if (savedPosts) {
            setPosts(JSON.parse(savedPosts));
        }
    }, []);

    useEffect(() => {
        if (result) {
            localStorage.setItem('result', JSON.stringify(result));
        }
    }, [result]);

    useEffect(() => {
        if (posts) {
            localStorage.setItem('posts', JSON.stringify(posts));
        }
    }, [posts]);

    const handleSubmit = async () => {
        try {
            let imagePath = null;

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

            const response = await axios.post('http://localhost:5000/process_data', {
                text: text || recognition.currentTranscript,
                image_path: imagePath
            });

            setResult(response.data);

            if (response.data.nudity_probability !== "This content is forbidden" && !response.data.censored_text.includes("***")) {
                const newPost = { text: lastText || text, image_path: lastImageFile || imagePath };
                setPosts([...posts, newPost]);
                setText('');
                setImageFile(null);
                setLastText('');
                setLastImageFile(null);
            }
        } catch (error) {
            console.error('Ошибка отправки данных:', error);
        }
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        setImageFile(file);
        setLastImageFile(file);
    };
    const handleDeletePost = (index) => {
        const updatedPosts = [...posts];
        updatedPosts.splice(index, 1); // Удаляем пост из массива по его индексу
        setPosts(updatedPosts); // Обновляем состояние постов
        // Обновляем данные в локальном хранилище
        localStorage.setItem('posts', JSON.stringify(updatedPosts));
    };
    const handleChange = (event) => {
        setText(event.target.value);
        setLastText(event.target.value);
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
            setLastText(transcript);
        };

        recognitionInstance.onend = () => {
            console.log('Распознавание речи завершено.');
            handleSubmit();
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
                    accept="image/*"
                />
            </div>
            <button className="btn btn-primary mr-2" onClick={handleSpeechRecognition}>
                Recognize Speech
            </button>
            <button className="btn btn-primary" onClick={handleSubmit}>
                Create Post
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
                                {new URLSearchParams(window.location.search).get('approved') === 'true' ? (
                                    <div className='success'>Congratulations, your publication has been confirmed by admin!</div>
                                ) : (
                                    <div>Your post is currently awaiting confirmation from the admins.</div>
                                )}
                            </div>
                        )}
                        <button className="btn btn-primary mt-2" onClick={() => setResult(null)}>Clear Result</button>
                    </div>
                </div>
            )}

            <div className="post-list">
                {posts.map((post, index) => (
                    <div key={index} className="card mt-3">
                        <div className="card-body">
                            <p className="card-text">{post.text}</p>
                            {post.image_path && <img src={post.image_path} alt="post" className="img-fluid" />}
                            <button className="btn btn-danger" onClick={() => handleDeletePost(index)}>Delete Post</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Textarea;
