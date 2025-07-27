import streamlit as st
import random
from datetime import datetime
from transformers import pipeline
import time
import sqlite3
from utils.style_utils import inject_global_styles
inject_global_styles()

def initialize_database():
    conn = sqlite3.connect("user_journal.db")  # Use single database
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_text TEXT,
            mood TEXT,
            spiral_level INTEGER,
            pattern TEXT,
            emotion TEXT,
            response_type TEXT
        )
    """)
    conn.commit()
    conn.close()

# Call the initializer at startup
initialize_database()

# Page config
st.set_page_config(
    page_title="Overthinking Buddy",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #ff9ff3;
        --secondary: #f368e0;
        --accent: #ff6b6b;
        --background: #fff9ff;
        --text: #5f27cd;
    }
    
    .stApp {
        background-color: var(--background);
    }
    
    h1, h2, h3 {
        color: var(--text) !important;
        font-family: 'Arial Rounded MT Bold', sans-serif;
    }
    
    .stButton>button {
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    .stButton>button:hover {
        background-color: var(--secondary) !important;
    }
    
    .stTextArea>div>div>textarea {
        border-radius: 15px !important;
        border: 2px solid var(--primary) !important;
    }
    
    .css-1d391kg {
        background-color: #fde8ff !important;
        border-right: 3px dotted var(--secondary);
    }
    
    .stExpander {
        border: 1px solid var(--primary) !important;
        border-radius: 15px !important;
    }
    
    .stMetric {
        background-color: #fef6ff !important;
        border-radius: 10px !important;
        padding: 10px !important;
        border-left: 3px solid var(--accent) !important;
    }
    
    .followup-btn {
        margin-bottom: 8px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_mood' not in st.session_state:
    st.session_state.user_mood = "🌸 Neutral"

# Load models with error handling
@st.cache_resource(show_spinner="Loading analysis models...")
def load_models():
    try:
        classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1  # Use CPU
        )
        return classifier
    except Exception as e:
        st.error(f"Model loading failed: {str(e)}")
        return None

def simple_pattern_detection(text):
    """Fallback pattern detection when models fail"""
    overthinking_keywords = {
        "catastrophic thinking": ["worst", "disaster", "terrible", "awful", "horrible"],
        "rumination": ["over and over", "can't stop thinking", "keep thinking"],
        "self-doubt": ["not good enough", "can't do this", "failure", "stupid"],
        "anxiety spiral": ["what if", "anxious", "nervous", "scared", "panic"],
        "decision paralysis": ["can't decide", "don't know", "what should", "which one"]
    }
    
    text_lower = text.lower()
    for pattern, keywords in overthinking_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return pattern, 0.8  # Medium confidence
    
    return "normal reflection", 0.5

def detect_overthinking_pattern(text, classifier):
    """Detect overthinking patterns using the classifier"""
    if classifier is None:
        return simple_pattern_detection(text)
    
    try:
        result = classifier(
            text,
            candidate_labels=[
                "catastrophic thinking",
                "rumination", 
                "self-doubt",
                "anxiety spiral",
                "decision paralysis",
                "normal reflection"
            ]
        )
        return result['labels'][0], result['scores'][0]
    except Exception as e:
        st.warning(f"Pattern detection failed: {str(e)}")
        return simple_pattern_detection(text)

def get_spiral_level(text, pattern):
    """Calculate overthinking intensity (1-10)"""
    negative_words = ['worried', 'anxious', 'scared', 'terrible', 'awful', 'hate', 'stupid']
    questions = text.count('?')
    negative_count = sum(1 for word in negative_words if word in text.lower())
    
    base_score = min(len(text) // 50, 5)
    question_score = min(questions * 1.5, 3)
    negative_score = min(negative_count * 0.5, 2)
    
    total = int(base_score + question_score + negative_score)
    return min(max(total, 1), 10)

def get_mood_emoji(text):
    """Simple mood detection"""
    positive_words = ['happy', 'joy', 'excited', 'good', 'great', 'love']
    negative_words = ['sad', 'angry', 'hate', 'awful', 'terrible']
    
    if any(word in text.lower() for word in positive_words):
        return random.choice(["🌈 Hopeful", "✨ Excited", "🌸 Peaceful"])
    elif any(word in text.lower() for word in negative_words):
        return random.choice(["🌀 Anxious", "🌧️ Sad", "🌪️ Overwhelmed"])
    else:
        return random.choice(["🌼 Neutral", "🌿 Contemplative", "☁️ Pensive"])

def get_preferred_response_type(chat_history=None):
    conn = sqlite3.connect("spiral_memory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT response_type FROM spiral_logs WHERE spiral_level >= 6")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "validation"  # default if no history

    types = [r[0] for r in rows if r[0]]
    most_common = Counter(types).most_common(1)[0][0]
    return most_common

from collections import Counter
import datetime
def detect_spiral_patterns():
    conn = sqlite3.connect("spiral_memory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp, spiral_level, detected_emotion  FROM spiral_logs")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None  # not enough data

    hours = []
    weekdays = []
    emotions = []

    for row in rows:
        ts, level, emotion = row
        dt = datetime.datetime.fromisoformat(ts)
        if int(level) >= 6:  # consider only high spirals
            hours.append(dt.hour)
            weekdays.append(dt.strftime("%A"))
            emotions.append(emotion)

    if not hours or not weekdays:
        return None

    # Get most common hour and day
    common_hour = Counter(hours).most_common(1)[0][0]
    common_day = Counter(weekdays).most_common(1)[0][0]
    common_emotion = Counter(emotions).most_common(1)[0][0] if emotions else None

    return {
        "hour": common_hour,
        "day": common_day,
        "emotion": common_emotion
    }


def generate_buddy_response(text, pattern, response_type, spiral_level, classifier):
    """Generate more personalized responses using ML"""
    preferred_tone = get_preferred_response_type(st.session_state.chat_history)
    if response_type == "mirror_me":
        response_type = preferred_tone
    # Get emotional tone
    try:
        emotion_result = classifier(
            text,
            candidate_labels=["fear", "anger", "sadness", "joy", "love", "surprise", "anxiety"]
        )
        dominant_emotion = emotion_result['labels'][0]
        emotion_confidence = emotion_result['scores'][0]
    except:
        dominant_emotion = "emotion"
        emotion_confidence = 0
    
    # Enhanced responses incorporating ML insights
    responses = {
        "validation": {
            "low": [
                f"I sense {dominant_emotion} in your words. That’s completely valid. It's okay to feel what you're feeling — no judgment here. Emotions are part of being human, and I'm here to hold space for you.",
                f"Your feelings of {dominant_emotion} make total sense in this situation. You’re not overreacting — you’re reacting. Whatever you’re carrying right now, I want you to know it’s real, and I’m not going anywhere.",
                f"I hear you, and this {dominant_emotion} is a normal response. You don’t need to justify it — just feeling it is enough. Let's just take this moment to sit with it, together."
            ],
            "high": [
                f"This {dominant_emotion} feels overwhelming, I can tell — and that’s completely valid. Sometimes the weight of things hits us like a wave, and it’s okay to feel like you're drowning. I’m right here with you in this.",
                f"Your {dominant_emotion} is coming through strongly, and that sounds really exhausting. It’s okay to be tired of carrying so much. You’re allowed to just exist right now — no fixing, no faking.",
                f"I can feel the intensity of this {dominant_emotion}, and you don't have to go through it alone. Whatever triggered this, it matters because *you* matter. I'm listening, fully and without judgment."
            ]
        },
        "tough_love": {
            "low": [
                f"That {dominant_emotion} is real, and I’m not dismissing it — but let’s gently ask: is this thought helping you or hurting you? Sometimes our minds trick us into believing fear as fact.",
                f"I see the {dominant_emotion}, and it’s completely okay to feel it — but is this worry based on solid ground? Let’s pause and look at what’s true, not just what’s loud.",
                f"Your {dominant_emotion} is valid, truly. But I want to challenge you — is this belief serving your peace, or stealing it? You’re stronger than the story anxiety is telling you right now."
            ],
            "high": [
                f"This {dominant_emotion} storm is loud, but you are not powerless inside it. Let's anchor in what we know is true, even if it’s just one small fact. Start there, gently.",
                f"Your brain is turning up the volume on this {dominant_emotion}, and that’s okay — but let’s not take every thought as gospel. You’ve faced harder things than this before, haven’t you?",
                f"That {dominant_emotion} is shouting right now, but it's not the whole truth. Take a deep breath. Come back to the evidence. What would you say to a friend thinking this?"
            ]
        },
        "humor": {
            "low": [
                f"Okay but... your brain really said ‘let me feel *all* the {dominant_emotion} today’? 😅 Honestly, same. Emotions can be drama queens sometimes — and that’s kinda what makes us awesome.",
                f"Plot twist: What if this {dominant_emotion} is just your inner drama director yelling ‘Action!’ again? Maybe give them a coffee and tell them to chill. ☕️",
                f"Your {dominant_emotion} deserves an Oscar for Most Dramatic Performance. 🏆 It’s putting on a whole production in your head — should we name it something? The Spiral Saga?"
            ],
            "high": [
                f"Breaking News: Local brain declares national {dominant_emotion} emergency! 🗞️ No survivors… except you, because you’re strong and slightly sarcastic. You got this.",
                f"Your {dominant_emotion} just wrote a full-on Netflix drama. Season 2 pending. But maybe — just maybe — you can take back the director's chair today. 🎬",
                f"Okay this {dominant_emotion} is working *overtime*. Someone give it a lunch break. You, on the other hand, deserve peace... and probably a cookie. 🍪"
            ]
        },
        "distraction": {
                "low": [
                f"Let’s take a little break from this {dominant_emotion}. What’s something small that brought you even 2% joy this week? Let’s go there, even if just for a moment.",
                f"Your {dominant_emotion} might just need a pause, not a solution. So, tell me: what’s your comfort food? Or the last movie that made you laugh out loud?",
                f"Mental reset time: What’s something unrelated to this {dominant_emotion}? Maybe a silly childhood memory? Something that reminds you who you are beyond the spiral?"
            ],
            "high": [
                f"EMERGENCY DISTRACTION 🚨 Your {dominant_emotion} is looping — let’s name 5 things you can see, 4 you can touch, 3 you can hear... you know the drill. Ground yourself.",
                f"Your {dominant_emotion} is like a playlist on repeat. Let’s skip to a better track — tell me your favorite feel-good memory or comfort series to binge.",
                f"Spiral interrupt in progress! 🛑 Let’s pivot. What’s a place you dream of visiting? Let’s talk about that instead — sometimes the brain just needs new scenery, even imaginary."
            ]
        }
    }
    
    intensity = "high" if spiral_level >= 6 else "low"
    return random.choice(responses[response_type][intensity])

from collections import Counter
def get_preferred_response_type(history):
    if not history:
        return "validation"
    
    weights = {"validation": 0, "tough_love": 0, "humor": 0, "distraction": 0}
    total = len(history)

    for i, entry in enumerate(history):
        rt = entry.get("response_type")
        if rt in weights:
            weight = 1 + (i / total)  # later entries count more
            weights[rt] += weight
    
    return max(weights, key=weights.get)

def get_personality_type(pattern_history):
    """Determine overthinking personality type"""
    if not pattern_history:
        return "The New Overthinker"
    
    pattern_counts = {}
    for pattern in pattern_history:
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    dominant_pattern = max(pattern_counts, key=pattern_counts.get)
    
    types = {
        "catastrophic thinking": "The Catastrophizer",
        "rumination": "The Retrospective Overanalyzer", 
        "self-doubt": "The Self-Doubt Ninja",
        "anxiety spiral": "The Spiral Queen",
        "decision paralysis": "The Indecisive Icon",
        "normal reflection": "The Balanced Thinker"
    }
    
    return types.get(dominant_pattern, "The Overthinker")
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("user_journal.db", check_same_thread=False)
c = conn.cursor()

# Create a table to store journal entries if it doesn't already exist
c.execute("""
CREATE TABLE IF NOT EXISTS journal (
    timestamp TEXT,
    input_text TEXT,
    mood TEXT,
    spiral_level INTEGER,
    pattern TEXT,
    emotion TEXT,
    response_type TEXT
)
""")
conn.commit()

from datetime import datetime
def save_entry(input_text, mood, spiral_level, pattern, emotion, response_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect("user_journal.db")
    c = conn.cursor()
    c.execute("""
    INSERT INTO journal (timestamp, input_text, mood, spiral_level, pattern, emotion, response_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, input_text, mood, spiral_level, pattern, emotion, response_type))
    conn.commit()
    conn.close()
    
    # Also update session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    st.session_state.chat_history.append({
        'input': input_text,
        'pattern': pattern,
        'spiral_level': spiral_level,
        'response': "",  # Will be added later
        'response_type': response_type,
        'mood': mood,
        'timestamp': timestamp
    })
def load_history():
    """Load chat history from database into session state"""
    conn = sqlite3.connect("user_journal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, input_text, mood, spiral_level, pattern, response_type FROM journal ORDER BY timestamp DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'timestamp': row[0],
            'input': row[1],
            'mood': row[2],
            'spiral_level': row[3],
            'pattern': row[4],
            'response_type': row[5],
            'response': ""  # Responses aren't stored in DB in current setup
        })
    
    return history
from textblob import TextBlob

def get_emotion_vector(text):
    emotion_vector = {
        "joy": 0.0,
        "sadness": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "guilt": 0.0
    }
    
    blob = TextBlob(text.lower())
    polarity = blob.sentiment.polarity
    words = blob.words

    # Heuristic: keywords + sentiment
    if any(word in words for word in ["happy", "excited", "love", "grateful", "smile", "laugh"]):
        emotion_vector["joy"] += 0.5 + max(polarity, 0)
    if any(word in words for word in ["sad", "lonely", "cry", "miss", "empty"]):
        emotion_vector["sadness"] += 0.5 - min(polarity, 0)
    if any(word in words for word in ["angry", "mad", "hate", "annoyed", "frustrated"]):
        emotion_vector["anger"] += 0.6
    if any(word in words for word in ["worried", "anxious", "scared", "panic", "fear"]):
        emotion_vector["fear"] += 0.6
    if any(word in words for word in ["sorry", "regret", "guilty", "ashamed"]):
        emotion_vector["guilt"] += 0.7

    # Normalize to 0-1
    max_val = max(emotion_vector.values()) or 1
    for key in emotion_vector:
        emotion_vector[key] = round(emotion_vector[key] / max_val, 2)
    
    return emotion_vector
from collections import Counter

def get_preferred_response_type(history):
    types = [entry['response_type'] for entry in history]
    if not types:
        return "validation"  # fallback
    counter = Counter(types)
    return counter.most_common(1)[0][0]
import pandas as pd
import io

def export_journal():
    # Convert chat history to DataFrame
    df = pd.DataFrame(st.session_state.chat_history)

    # Optional: format timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Convert to CSV in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    # Streamlit download button
    st.download_button(
        label="📥 Download My Spiral Journal",
        data=csv_data,
        file_name="spiral_journal.csv",
        mime="text/csv"
    )

def main():
    # Header with personality
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://em-content.zobj.net/source/microsoft-teams/363/pink-heart_1fa77.png", width=80)
    with col2:
        st.title("Overthinking Buddy")
        st.markdown("*Your chaotic-smart companion for thought spirals 🌪️🌸*")
    
    # Load models
    classifier = load_models()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🌸 Your Buddy Settings")
        
        response_type = st.selectbox(
            "How should I respond?",
            ["validation", "tough_love", "humor", "distraction", "mirror_me"],
            format_func=lambda x: {
                "validation": "🤗 Validate me",
                "tough_love": "💪 Be brutally honest",
                "humor": "😂 Make me laugh",
                "distraction": "🎯 Change the topic",
                "mirror_me": "🪞 Mirror my vibe (smart adaptive)"
            }[x]
        )

        
        st.markdown("---")
        st.markdown("### 📊 Your Overthinking Stats")
        st.markdown("---")
        if st.button("📈 Show My Spiral Trends", use_container_width=True):
            st.switch_page("pages/Trends.py")
            
        if st.session_state.chat_history:
            pattern_history = [entry['pattern'] for entry in st.session_state.chat_history]
            personality_type = get_personality_type(pattern_history)
            
            avg_spiral = sum(entry.get('spiral_level', 0) for entry in st.session_state.chat_history) / len(st.session_state.chat_history)
            st.metric("✨ Your Personality Type", personality_type)
            st.metric("🌀 Average Spiral Level", f"{avg_spiral:.1f}/10")
            st.metric("📅 Total Sessions", len(st.session_state.chat_history))
            
            # Mood tracker
            st.markdown("---")
            st.markdown("### 🌈 Your Mood Trends")
            recent_moods = [entry.get('mood', '🌸 Neutral') for entry in st.session_state.chat_history[-5:]]
            st.write("Recent moods:")
            cols = st.columns(len(recent_moods))
            for i, mood in enumerate(recent_moods):
                cols[i].write(f"• {mood}")
        else:
            st.write("Share your thoughts to see your stats!")
    
    # Main chat interface
    st.markdown("### 💭 What's swirling in that beautiful mind?")
    
    user_input = st.text_area(
        "Type your thoughts here...",
        placeholder="I keep thinking about that thing I said three years ago and now I'm convinced everyone hates me...",
        height=150,
        label_visibility="collapsed"
    )
    
    if st.button("Help me process this 🌸", type="primary", use_container_width=True):
        if user_input.strip():
            with st.spinner("Decoding your thoughts..."):
                try:
                    # Detect pattern
                    pattern, confidence = detect_overthinking_pattern(user_input, classifier)
                    
                    # Get spiral level and mood
                    spiral_level = get_spiral_level(user_input, pattern)
                    mood = get_mood_emoji(user_input)
                    
                    # Generate response
                    buddy_response = generate_buddy_response(user_input, pattern, response_type, spiral_level, classifier)
                    
                    # Display results
                    st.markdown("---")
                    
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("🌺 Detected Pattern", pattern.replace("_", " ").title())
                    with cols[1]:
                        st.metric("🌀 Spiral Intensity", f"{spiral_level}/10")
                    with cols[2]:
                        st.metric("🌈 Current Mood", mood)
                    
                    # Visual spiral meter
                    st.markdown("### Your Spiral Meter")
                    spiral_bar = "🌸" * spiral_level + "⚪" * (10 - spiral_level)
                    st.progress(spiral_level/10, text=f"`{spiral_bar}` {spiral_level}/10")
                    
                    # Buddy response
                    st.markdown("### 💖 Your Buddy Says:")
                    st.markdown(f"""
                    <div style="
                        background-color: #fff0f5;
                        padding: 15px;
                        border-radius: 15px;
                        border-left: 5px solid #ff9ff3;
                        margin-bottom: 20px;
                    ">
                        {buddy_response}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Save to history
                    st.session_state.chat_history.append({
                        'input': user_input,
                        'pattern': pattern,
                        'spiral_level': spiral_level,
                        'response': buddy_response,
                        'response_type': response_type,
                        'mood': mood,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    emotion_vector = get_emotion_vector(user_input)
                    save_entry(user_input, mood, spiral_level, pattern, str(emotion_vector), response_type)

                    pattern = detect_spiral_patterns()
                    if pattern:
                        st.markdown("---")
                        st.markdown("### 📊 Here's something I've noticed about you:")
                        st.markdown(f"""
                        - 🌙 You tend to spiral most often around **{pattern['hour']}:00**.
                        - 📅 **{pattern['day']}s** seem to be emotionally tougher than others.
                        - 😔 The most frequent emotion during your spirals is **{pattern['emotion']}**.
                        
                        Just bringing this to your awareness. Let me know if you want help making sense of it.
                        """)

                    # Add follow-up buttons after each response
                    st.markdown("---")
                    st.markdown("### 💬 Continue this conversation:")
                    cols = st.columns(2)
                    with cols[0]:
                        if st.button(" Tell me more about this", key="more", use_container_width=True):
                            user_input = f"About what you said: '{buddy_response[:50]}...' - can you elaborate?"
                    with cols[1]:
                        if st.button(" Change the subject", key="change", use_container_width=True):
                            user_input = "Actually, I'd like to talk about something else..."
                    
                except Exception as e:
                    st.error(f"Oops! Something went wrong: {str(e)}")
                    st.info("Here's a generic response to help:")
                    st.markdown(f"""
                    <div style="
                        background-color: #fff0f5;
                        padding: 15px;
                        border-radius: 15px;
                        border-left: 5px solid #ff9ff3;
                        margin-bottom: 20px;
                    ">
                        I'm here for you. Whatever you're feeling is valid. Try taking three deep breaths with me?
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("Please share what's on your mind first!")
    
    # Show recent history
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 📖 Your Thought Journal")
        if st.button("📤 Export My Journal Data", use_container_width=True):
            export_journal()

        for i, entry in enumerate(reversed(st.session_state.chat_history[-3:])):
            with st.expander(f"🗓️ {entry['timestamp']} | {entry['mood']} | Level {entry['spiral_level']}"):
                st.markdown(f"**Your thoughts:**")
                st.markdown(f'<div style="background-color:#faf5ff; padding:10px; border-radius:10px;">{entry["input"]}</div>', unsafe_allow_html=True)
                
                st.markdown(f"**🌸 Buddy response ({entry['response_type'].replace('_', ' ').title()}):**")
                st.markdown(f'<div style="background-color:#fff0f5; padding:10px; border-radius:10px;">{entry["response"]}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()