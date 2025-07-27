Overthinking Buddy is a lightweight mental health journaling assistant built with Python and Streamlit. It enables users to log thoughts, detects emotions using pretrained models, and stores reflection data for pattern tracking over time.

Live Demo: https://overthinking-buddy.streamlit.app/

Technology Stack
Frontend: Streamlit (for interactive UI)

NLP:
Hugging Face Transformers (for emotion classification)
TextBlob (for sentiment scoring and POS tagging)
NLTK (provides tokenizers and taggers for TextBlob)

Database: SQLite (persistent storage of emotional logs)

Features
Free-text journaling with real-time NLP-based emotion detection
Sentiment analysis using TextBlob’s polarity and subjectivity scores
Emotion classification using distilbert-base-uncased via Hugging Face pipeline
Spiral level tracking based on emotion intensity
Local SQLite database (spiral_memory.db) to log and retrieve entries
Auto-download of required NLTK corpora (punkt, averaged_perceptron_tagger) at runtime for deployment compatibility
