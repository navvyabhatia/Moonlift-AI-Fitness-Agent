import streamlit as st
from datetime import datetime
import json
import os
import uuid
import re

from dotenv import load_dotenv

from src.config import settings
from src.models import DailyContext
from src.integrations import get_mock_user_history
from src.recommender import generate_recommendation
from src.vector_store import store_user_context, retrieve_user_history, user_exists, store_feedback, get_user_feedback

load_dotenv()

st.set_page_config(page_title="Moon Lift", page_icon="🌙", layout="wide")

# File paths and utility functions
HISTORY_FILE = "chat_history.json"
PREFS_FILE = "user_preferences.json"
CONVERSATIONS_FILE = "conversations.json"

def load_history():
    """Load chat history for the current user"""
    user_id = st.session_state.get("user_id")
    if not user_id or not st.session_state.get("onboarded", False):
        # Return empty history for new users or users without proper ID
        return []
    
    history_file = f"chat_history_{user_id}.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    """Save chat history for the current user"""
    user_id = st.session_state.get("user_id")
    if not user_id or not st.session_state.get("onboarded", False):
        # Don't save history for new users or users without proper ID
        return
    
    history_file = f"chat_history_{user_id}.json"
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def load_conversations():
    """Load all conversation sessions for the current user"""
    user_id = st.session_state.get("user_id")
    if not user_id or not st.session_state.get("onboarded", False):
        # Return empty conversations for new users or users without proper ID
        return []
    
    if os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, "r") as f:
            all_conversations = json.load(f)
            # Return conversations for current user only
            return all_conversations.get(user_id, [])
    return []

def save_conversations(conversations):
    """Save conversations for the current user"""
    user_id = st.session_state.get("user_id")
    if not user_id or not st.session_state.get("onboarded", False):
        # Don't save conversations for new users or users without proper ID
        return
    
    # Load existing conversations
    if os.path.exists(CONVERSATIONS_FILE):
        try:
            all_conversations = json.load(open(CONVERSATIONS_FILE, "r"))
        except:
            all_conversations = {}
    else:
        all_conversations = {}
    
    # Update current user's conversations
    all_conversations[user_id] = conversations
    
    # Save all conversations
    with open(CONVERSATIONS_FILE, "w") as f:
        json.dump(all_conversations, f, indent=2)

def save_current_conversation():
    """Save the current session as a conversation"""
    if st.session_state.get("session_content") and st.session_state.get("user_id"):
        conversations = load_conversations()
        
        # Create conversation object
        conversation = {
            "id": str(uuid.uuid4())[:8],
            "title": generate_conversation_title(st.session_state.session_content),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": st.session_state.session_content.copy(),
            "user_name": st.session_state.get("user_name", "User"),
            "quick_inputs": {
                "feeling": st.session_state.get("feeling", ""),
                "cycle_phase": st.session_state.get("cycle_phase", ""),
                "duration": st.session_state.get("duration", ""),
                "constraints": st.session_state.get("constraints", "")
            }
        }
        
        # Add to conversations (most recent first)
        conversations.insert(0, conversation)
        
        # Keep only last 20 conversations
        conversations = conversations[:20]
        
        save_conversations(conversations)

def generate_conversation_title(messages):
    """Generate a title for the conversation based on first workout recommendation"""
    for msg in messages:
        if msg["role"] == "assistant" and "Today's Workout Plan" in msg["content"]:
            # Extract the first line after "Today's Workout Plan"
            lines = msg["content"].split('\n')
            for line in lines:
                if "Since you" in line or "Let's" in line or "I'll" in line:
                    return line.strip()[:50] + "..." if len(line.strip()) > 50 else line.strip()
    
    # Fallback to date-based title
    return f"Workout - {datetime.now().strftime('%m/%d')}"

def load_conversation(conversation_id):
    """Load a specific conversation into the current session"""
    conversations = load_conversations()
    
    for conv in conversations:
        if conv["id"] == conversation_id:
            # Load conversation into session
            st.session_state.session_content = conv["messages"].copy()
            st.session_state.first_recommendation_done = True
            st.session_state.new_session = False
            
            # Load quick inputs if available
            if "quick_inputs" in conv:
                st.session_state.feeling = conv["quick_inputs"].get("feeling", "")
                st.session_state.cycle_phase = conv["quick_inputs"].get("cycle_phase", "")
                st.session_state.duration = conv["quick_inputs"].get("duration", "")
                st.session_state.constraints = conv["quick_inputs"].get("constraints", "")
            
            return True
    
    return False

def load_preferences():
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    return {"likes": [], "dislikes": [], "onboarded": False}

def save_preferences(prefs):
    # Load existing preferences
    if os.path.exists(PREFS_FILE):
        try:
            existing = json.load(open(PREFS_FILE, "r"))
        except:
            existing = {}
    else:
        existing = {}
    
    # Handle multiple users format
    if "users" not in existing:
        existing = {"users": {}}
    
    # Add or update this user
    user_id = prefs.get("user_id", str(uuid.uuid4()))
    existing["users"][user_id] = prefs
    
    # Save back
    with open(PREFS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

# Session state initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize session state
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "nickname" not in st.session_state:
    st.session_state.nickname = None
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "preferences" not in st.session_state:
    st.session_state.preferences = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "first_recommendation_done" not in st.session_state:
    st.session_state.first_recommendation_done = False
if "new_session" not in st.session_state:
    st.session_state.new_session = True  # Start as new session
if "force_login" not in st.session_state:
    st.session_state.force_login = False
if "current_recommendation" not in st.session_state:
    st.session_state.current_recommendation = None
if "session_content" not in st.session_state:
    st.session_state.session_content = []

if "force_login" not in st.session_state:
    st.session_state.force_login = True

# Handle logout via query param
if "logout" in st.query_params:
    st.query_params.clear()
    st.session_state.force_login = True
    st.session_state.user_name = ""
    st.session_state.nickname = ""
    st.session_state.preferences = {}
    st.session_state.chat_history = []
    save_history([])
    save_preferences({})
    st.rerun()

# Debug log at the top
if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)
    st.write("Debug info:")
    st.write(f"Feeling: {st.session_state.get('feeling')}")
    st.write(f"Cycle: {st.session_state.get('cycle')}")
    st.write(f"Duration: {st.session_state.get('duration')}")
    st.write(f"Schedule: {st.session_state.get('schedule')}")

# If forced to login, show login UI and stop
if st.session_state.get("force_login") or not st.session_state.get("user_name"):
    st.subheader("Welcome to Moon Lift 🌙")
    tab1, tab2 = st.tabs(["Returning user", "New user"])
    with tab1:
        nickname_input = st.text_input("Enter your nickname to log in")
        if st.button("Log in"):
            all_prefs = load_preferences()
            st.write(f"Debug: Looking for nickname '{nickname_input}'")
            
            # Check if this is a simple preferences file (old format) or multiple users
            if isinstance(all_prefs, dict) and "users" in all_prefs:
                # Multiple users format
                users = all_prefs["users"]
                st.write(f"Debug: Found {len(users)} users")
                for user_id, user_data in users.items():
                    nickname = user_data.get("nickname", "")
                    st.write(f"Debug: Checking user {user_id}: '{nickname}'")
                    if nickname == nickname_input:
                        st.write(f"Debug: Found matching user!")
                        st.session_state.user_name = user_data["user_name"]
                        st.session_state.nickname = user_data["nickname"]
                        st.session_state.user_id = user_id
                        st.session_state.preferences = user_data
                        st.session_state.chat_history = load_history()
                        st.session_state.force_login = False
                        st.success(f"Welcome, {user_data['user_name']}!")
                        st.rerun()
                        break
                else:
                    st.error("Nickname not found. Try again or sign up as a new user.")
            else:
                st.error("No users found. Please sign up as a new user.")
    with tab2:
        with st.expander("🌙 Let's set you up.", expanded=True):
            name = st.text_input("Your name")
            lifestyle = st.selectbox("Lifestyle", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"])
            exercise_week = st.slider("How many days a week do you exercise?", 0, 7, 3)
            goal = st.selectbox("What do you want to achieve?", ["Strength", "Fat loss", "Mobility", "Endurance", "Stress relief"])
            like_options = ["Yoga", "Running", "Weightlifting", "Cycling", "Dance", "Swimming", "Walking", "HIIT", "Pilates"]
            likes = st.multiselect("Activities you like", like_options)
            dislikes = st.multiselect("Activities you dislike", like_options)
            if st.button("Sign up"):
                if not name or not likes:
                    st.error("Please enter your name and at least one liked activity.")
                else:
                    import random
                    # Moon-themed creative nicknames
                    moon_words = ["luna", "moon", "celestial", "stellar", "cosmic", "nova", "star", "galaxy", "orbit", "eclipse", "aurora", "nebula", "comet", "meteor", "phases", "tides", "glow", "shine", "beam", "radiant"]
                    fitness_words = ["fit", "strong", "power", "lift", "flow", "move", "flex", "core", "pulse", "vibe", "energy", "force", "zen", "calm", "balance", "grace", "agility", "vitality"]
                    
                    # Create base from name
                    base = name.strip().lower().replace(" ", "")[:3] if len(name.strip()) > 3 else name.strip().lower()
                    
                    # Generate creative combinations
                    moon_word = random.choice(moon_words)
                    fitness_word = random.choice(fitness_words)
                    suffix = random.randint(100, 999)
                    
                    # Different nickname patterns
                    patterns = [
                        f"{moon_word}{fitness_word}{suffix}",
                        f"{base}{moon_word}{suffix}",
                        f"{moon_word}{base}{suffix}",
                        f"{fitness_word}{moon_word}{suffix}",
                    ]
                    
                    nickname = random.choice(patterns)
                    st.session_state.user_name = name
                    st.session_state.nickname = nickname
                    st.session_state.preferences = {
                        "user_name": name,
                        "nickname": nickname,
                        "user_id": st.session_state.user_id,
                        "onboarded": True,
                        "lifestyle": lifestyle,
                        "exercise_week": exercise_week,
                        "goal": goal,
                        "likes": likes,
                        "dislikes": dislikes
                    }
                    save_preferences(st.session_state.preferences)
                    st.success(f"Your nickname is: **{nickname}** — use this to log in next time!")
                    st.session_state.force_login = False
                    st.rerun()
    st.stop()

st.title("Moon Lift 🌙")
st.markdown("*for women by women*")

def load_preferences():
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    return {"likes": [], "dislikes": [], "onboarded": False}

def save_preferences(prefs):
    # Load existing preferences
    if os.path.exists(PREFS_FILE):
        try:
            existing = json.load(open(PREFS_FILE, "r"))
        except:
            existing = {}
    else:
        existing = {}
    
    # Handle multiple users format
    if "users" not in existing:
        existing = {"users": {}}
    
    # Add or update this user
    user_id = prefs.get("user_id", str(uuid.uuid4()))
    existing["users"][user_id] = prefs
    
    # Save back
    with open(PREFS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Never load preferences automatically; only load after explicit login
if "preferences" not in st.session_state:
    st.session_state.preferences = {}

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "first_recommendation_done" not in st.session_state:
    st.session_state.first_recommendation_done = False

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "generate_rec" not in st.session_state:
    st.session_state.generate_rec = False

def render_message(role, content, timestamp=None, activities_with_feedback=None, msg_index=None):
    with st.chat_message(role):
        if timestamp:
            st.caption(f"{timestamp}")
        st.markdown(content)
        if role == "assistant" and activities_with_feedback and msg_index is not None:
            st.markdown("**Did you like these activities?**")
            cols = st.columns(len(activities_with_feedback))
            for i, act in enumerate(activities_with_feedback):
                with cols[i]:
                    st.markdown(f"**{act}**")
                    col_like, col_dislike = st.columns(2)
                    with col_like:
                        if st.button("👍", key=f"like_{msg_index}_{i}_{act}"):
                            store_feedback(st.session_state.user_id, act, "like")
                            st.rerun()
                    with col_dislike:
                        if st.button("👎", key=f"dislike_{msg_index}_{i}_{act}"):
                            store_feedback(st.session_state.user_id, act, "dislike")
                            st.rerun()

# Main app layout with sidebar
if st.session_state.user_name:
    # Create sidebar for conversation history
    with st.sidebar:
        st.title("Workout History")
        
        # New conversation button
        if st.button("New Workout", type="primary", use_container_width=True):
            # Clear current session and start fresh
            st.session_state.session_content = []
            st.session_state.first_recommendation_done = False
            st.session_state.new_session = True
            st.session_state.current_recommendation = None
            # Clear quick inputs
            for key in ["feeling", "cycle_phase", "duration", "constraints"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # Load and display conversation history
        conversations = load_conversations()
        
        if conversations:
            st.subheader("Past Workouts")
            
            for conv in conversations:
                with st.expander(f"Date: {conv['date']}", expanded=False):
                    # Display conversation title
                    st.write(f"**{conv['title']}**")
                    
                    # Load conversation button
                    if st.button(f"Load", key=f"load_{conv['id']}", use_container_width=True):
                        if load_conversation(conv['id']):
                            st.success("Conversation loaded!")
                            st.rerun()
                        else:
                            st.error("Failed to load conversation")
                    
                    # Delete conversation button
                    if st.button(f"Delete", key=f"delete_{conv['id']}", use_container_width=True):
                        conversations = [c for c in conversations if c['id'] != conv['id']]
                        save_conversations(conversations)
                        st.rerun()
        else:
            st.info("No past workouts yet. Start your first workout above!")
    
    # Main content area
    with st.container():
        # Welcome message - simple for all users
        if st.session_state.user_name:
            # Add logout button in top right corner
            col1, col2, col3 = st.columns([6, 2, 2])
            with col3:
                if st.button("Logout", type="secondary"):
                    st.session_state.force_login = True
                    st.session_state.user_name = ""
                    st.session_state.nickname = ""
                    st.session_state.chat_history = []
                    st.session_state.current_recommendation = None
                    st.session_state.session_content = []
                    st.session_state.first_recommendation_done = False
                    st.session_state.new_session = True
                    save_history([])
                    st.rerun()
            with col1:
                # Display nickname with welcome message
                nickname = st.session_state.get("nickname", "User")
                st.success(f"Welcome, {st.session_state.user_name}! 🌙 Your nickname: **{nickname}**")

# Returning user login by nickname
if not st.session_state.user_name:
    st.subheader("Welcome to Moon Lift ")
    tab1, tab2 = st.tabs(["Returning user", "New user"])
    with tab1:
        nickname_input = st.text_input("Enter your nickname to log in")
        if st.button("Log in"):
            # Search for nickname in all user preferences
            found_user = None
            try:
                # Try to load from individual user files or database
                from src.vector_store import user_exists
                if user_exists(nickname_input):
                    # User exists in vector store, they're returning
                    st.session_state.user_name = nickname_input.split("Luna")[0].split("Crescent")[0].split("FullMoon")[0].split("NewMoon")[0].split("Waxing")[0].split("Waning")[0].split("Gibbous")[0].split("Quarter")[0].split("Eclipse")[0].split("Lunar")[0]
                    st.session_state.nickname = nickname_input
                    st.session_state.user_id = nickname_input  # Use nickname as user_id for now
                    st.session_state.preferences = {
                        "user_name": st.session_state.user_name,
                        "nickname": nickname_input,
                        "user_id": st.session_state.user_id,
                        "onboarded": True
                    }
                    st.session_state.chat_history = load_history()
                    st.rerun()
                else:
                    st.error("Nickname not found. Try again or sign up as a new user.")
            except Exception:
                # Fallback to file-based search
                all_prefs = load_preferences()
                if all_prefs.get("nickname") == nickname_input:
                    st.session_state.user_name = all_prefs["user_name"]
                    st.session_state.nickname = all_prefs["nickname"]
                    st.session_state.user_id = all_prefs["user_id"]
                    st.session_state.preferences = all_prefs
                    st.session_state.chat_history = load_history()
                    st.rerun()
                else:
                    st.error("Nickname not found. Try again or sign up as a new user.")
    with tab2:
        with st.expander(" Let's set you up.", expanded=True):
            name = st.text_input("Your name")
            lifestyle = st.selectbox("Lifestyle", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"])
            exercise_week = st.slider("How many days a week do you exercise?", 0, 7, 3)
            goal = st.selectbox("What do you want to achieve?", ["Strength", "Fat loss", "Mobility", "Endurance", "Stress relief"])
            
            # Organized activity categories
            st.write("**Select activities you like:**")
            
            # Add search functionality
            search_term = st.text_input(" Search activities (optional)", placeholder="Type to search for specific activities...")
            
            # Debug info
            if search_term:
                st.write(f" Searching for: '{search_term}'")
            
            # Cardio Exercises
            with st.expander(" Cardio Exercises", expanded=False):
                cardio_options = [
                    "Stair Climbing", "Walking (brisk)", "Running/Jogging", "Cycling/Biking", "Swimming", 
                    "Elliptical Machine", "Dancing/Dance Fitness", "Rowing/Rowing Machine", "Hiking", 
                    "Jumping Rope", "HIIT (High-Intensity Interval Training)", "Jumping Jacks", "High Knees",
                    "Burpees", "Mountain Climbers", "Sprinting", "Kickboxing", "Step Aerobics"
                ]
                # Filter by search term
                if search_term:
                    filtered_cardio = [opt for opt in cardio_options if search_term.lower() in opt.lower()]
                    st.write(f"Debug: Cardio options matching '{search_term}': {filtered_cardio}")
                    if filtered_cardio:
                        st.write(f" Found {len(filtered_cardio)} matching activities")
                        cardio_likes = st.multiselect("Cardio activities", filtered_cardio, key="cardio_likes", max_options=len(filtered_cardio))
                    else:
                        st.write(" No matching cardio activities")
                        cardio_likes = []
                else:
                    cardio_likes = st.multiselect("Cardio activities", cardio_options, key="cardio_likes", max_options=len(cardio_options))
            
            # Strength Training
            with st.expander(" Strength Training", expanded=False):
                strength_options = [
                    "Push-ups", "Pull-ups", "Squats", "Lunges", "Plank", "Deadlifts", "Bench Press", 
                    "Shoulder Press", "Bicep Curls", "Tricep Dips", "Lat Pulldowns", "Leg Press", 
                    "Calf Raises", "Russian Twists", "Wall Sits", "Glute Bridges", "Leg Raises",
                    "Chest Flys", "Lateral Raises", "Hammer Curls", "Skull Crushers", "Good Mornings"
                ]
                # Filter by search term
                if search_term:
                    filtered_strength = [opt for opt in strength_options if search_term.lower() in opt.lower()]
                    st.write(f"Debug: Strength options matching '{search_term}': {filtered_strength}")
                    if filtered_strength:
                        st.write(f" Found {len(filtered_strength)} matching activities")
                        strength_likes = st.multiselect("Strength activities", filtered_strength, key="strength_likes", max_options=len(filtered_strength))
                    else:
                        st.write(" No matching strength activities")
                        strength_likes = []
                else:
                    strength_likes = st.multiselect("Strength activities", strength_options, key="strength_likes", max_options=len(strength_options))
            
            # Yoga & Flexibility
            with st.expander(" Yoga & Flexibility", expanded=True):
                yoga_options = [
                    "Yoga", "Pilates", "Stretching (Dynamic/Static)", "Foam Rolling", "Tai Chi", 
                    "Cat-Cow", "Child's Pose", "Downward Dog", "Warrior Pose", "Tree Pose", 
                    "Bridge Pose", "Cobra Pose", "Chair Pose", "Triangle Pose", "Pigeon Pose",
                    "Sun Salutation", "Corpse Pose", "Happy Baby", "Seated Forward Bend"
                ]
                # Filter by search term
                if search_term:
                    filtered_yoga = [opt for opt in yoga_options if search_term.lower() in opt.lower()]
                    if filtered_yoga:
                        st.write(f" Found {len(filtered_yoga)} matching activities")
                        yoga_likes = st.multiselect("Yoga & flexibility activities", filtered_yoga, key="yoga_likes", max_options=len(filtered_yoga))
                    else:
                        st.write(" No matching yoga activities")
                        yoga_likes = []
                else:
                    yoga_likes = st.multiselect("Yoga & flexibility activities", yoga_options, key="yoga_likes", max_options=len(yoga_options))
            
            # Core & Abs
            with st.expander(" Core & Abs", expanded=False):
                core_options = [
                    "Crunches", "Sit-ups", "Side Planks", "Bird Dog", "Bicycle Crunches", 
                    "Leg Lifts", "Reverse Crunches", "Mountain Climbers", "Plank Variations",
                    "Dead Bug", "Pallof Press", "Cable Crunches", "Hanging Leg Raises"
                ]
                # Filter by search term
                if search_term:
                    filtered_core = [opt for opt in core_options if search_term.lower() in opt.lower()]
                    if filtered_core:
                        st.write(f" Found {len(filtered_core)} matching activities")
                        core_likes = st.multiselect("Core & abs activities", filtered_core, key="core_likes", max_options=len(filtered_core))
                    else:
                        st.write(" No matching core activities")
                        core_likes = []
                else:
                    core_likes = st.multiselect("Core & abs activities", core_options, key="core_likes", max_options=len(core_options))
            
            # Bodyweight & Functional
            with st.expander(" Bodyweight & Functional", expanded=False):
                functional_options = [
                    "Bodyweight/weights training", "TRX", "Resistance Bands", "Medicine Ball",
                    "Kettlebell Swings", "Box Jumps", "Agility Ladder", "Battle Ropes",
                    "Sled Push/Pull", "Farmer's Walks", "Tire Flips", "Sandbag Training"
                ]
                # Filter by search term
                if search_term:
                    filtered_functional = [opt for opt in functional_options if search_term.lower() in opt.lower()]
                    if filtered_functional:
                        st.write(f"🔍 Found {len(filtered_functional)} matching activities")
                        functional_likes = st.multiselect("Functional training activities", filtered_functional, key="functional_likes", max_options=len(filtered_functional))
                    else:
                        st.write("🔍 No matching functional activities")
                        functional_likes = []
                else:
                    functional_likes = st.multiselect("Functional training activities", functional_options, key="functional_likes", max_options=len(functional_options))
            
            # Low Impact & Recovery
            with st.expander("🌿 Low Impact & Recovery", expanded=False):
                recovery_options = [
                    "Swimming (leisure)", "Water Aerobics", "Recumbent Bike", "Incline Walking",
                    "Elliptical (low resistance)", "Gentle Yoga", "Stretching", "Foam Rolling",
                    "Massage Gun", "Active Recovery", "Walking Meditation"
                ]
                # Filter by search term
                if search_term:
                    filtered_recovery = [opt for opt in recovery_options if search_term.lower() in opt.lower()]
                    if filtered_recovery:
                        st.write(f"🔍 Found {len(filtered_recovery)} matching activities")
                        recovery_likes = st.multiselect("Low impact & recovery activities", filtered_recovery, key="recovery_likes", max_options=len(filtered_recovery))
                    else:
                        st.write("🔍 No matching recovery activities")
                        recovery_likes = []
                else:
                    recovery_likes = st.multiselect("Low impact & recovery activities", recovery_options, key="recovery_likes", max_options=len(recovery_options))
            
            # Combine all likes
            likes = cardio_likes + strength_likes + yoga_likes + core_likes + functional_likes + recovery_likes
            
            # Dynamic dislikes - only show activities not already liked
            all_options = cardio_options + strength_options + yoga_options + core_options + functional_options + recovery_options
            available_for_dislikes = [opt for opt in all_options if opt not in likes]
            
            if available_for_dislikes:
                st.write("**Select activities you dislike:**")
                dislikes = st.multiselect("Disliked activities", available_for_dislikes, key="dislikes_select")
            else:
                dislikes = []
                st.info("All activities have been selected as liked!")
            
            # Sign up button moved outside expander
            st.markdown("---")
            if st.button("🌙 Sign Up", type="primary", use_container_width=True):
                if not name or not likes:
                    st.error("Please enter your name and at least one liked activity.")
                else:
                    # Generate nickname: user name + moon phase themed name
                    import random
                    moon_themes = ["Luna", "Crescent", "FullMoon", "NewMoon", "Waxing", "Waning", "Gibbous", "Quarter", "Eclipse", "Lunar"]
                    # Clean name: remove spaces and special characters, keep original for display
                    clean_name = name.strip().replace(" ", "").replace("-", "").replace("_", "")
                    moon_theme = random.choice(moon_themes)
                    nickname = f"{clean_name}{moon_theme}"
                    
                    # Set user_id first
                    st.session_state.user_id = nickname
                    
                    st.session_state.user_name = name
                    st.session_state.nickname = nickname
                    st.session_state.preferences["user_name"] = name
                    st.session_state.preferences["nickname"] = nickname
                    st.session_state.preferences["user_id"] = st.session_state.user_id
                    st.session_state.preferences["onboarded"] = True
                    st.session_state.preferences["lifestyle"] = lifestyle
                    st.session_state.preferences["exercise_week"] = exercise_week
                    st.session_state.preferences["goal"] = goal
                    st.session_state.preferences["likes"] = likes
                    st.session_state.preferences["dislikes"] = dislikes
                    save_preferences(st.session_state.preferences)
                    
                    # Store success message in session state to show after rerun
                    st.session_state.signup_success = True
                    st.session_state.generated_nickname = nickname
                    st.session_state.original_name = name
                    
                    st.rerun()
else:
    # Main logged-in UI
    # Show welcome message for newly onboarded users
    if st.session_state.get("signup_success"):
        st.success("🎉 Account created successfully!", icon="✅")
        st.markdown("---")
        st.markdown("## 🌙 Welcome to Moon Lift!")
        st.markdown(f"### **Your Nickname: {st.session_state.get('generated_nickname', 'N/A')}**")
        st.markdown("Use this nickname to log in next time!")
        st.markdown("---")
        st.info(f"👋 Welcome, {st.session_state.get('original_name', 'User')}! Your personalized workout journey starts now.")
        # Clear the success flag after showing
        st.session_state.signup_success = False
        
    st.markdown("---")
    st.subheader("Welcome to Moon Lift 🌙")
    st.write("""
    I'm your AI gym coach. I'll recommend daily workouts based on how you feel, your cycle phase, and your schedule. I remember your preferences and adapt over time. Let's get moving!""")

    # Quick inputs section
    st.markdown("---")
    st.subheader("Quick Inputs")
    
    # Quick input columns
    col1, col2, col3 = st.columns(3)
    with col1:
        feeling = st.selectbox(
            "How are you feeling?",
            ["Energetic", "Tired", "Sore", "Stressed", "Motivated", "Relaxed","Restless","Other"],
            key="feeling",
            index=None
        )
    with col2:
        cycle_phase = st.selectbox(
            "Cycle phase",
            ["Follicular", "Ovulation", "Luteal", "Menstrual", "Not sure"],
            key="cycle_phase",
            index=None
        )
    with col3:
        duration = st.selectbox(
            "Duration",
            ["15 min", "30 min", "45 min", "60 min"],
            key="duration",
            index=None
        )
    
    # Constraints text input
    constraints = st.text_input("Anything else you would like me to know?", key="constraints", placeholder="e.g., no equipment, bad knee, prefer indoor exercises")

    # Validation
    if not all([feeling, cycle_phase, duration]):
        st.warning("Please fill in all quick inputs to get a recommendation")
        st.stop()  # Stop execution instead of return

    # Show current recommendation if available
    if st.session_state.session_content:
        st.markdown("---")
        st.subheader("Current Session")
        for content in st.session_state.session_content:
            with st.chat_message(content["role"]):
                st.markdown(content["content"])

    # Get recommendation button (only show if no recommendation yet)
    if not st.session_state.first_recommendation_done:
        if st.button("Get Recommendation", type="primary"):
            with st.spinner("Generating your personalized workout..."):
                try:
                    context = DailyContext(
                        time_available=duration,
                        energy_level={
                            "Energetic": 8,
                            "Motivated": 7,
                            "Relaxed": 6,
                            "Neutral": 5,
                            "Restless": 4,
                            "Sore": 3,
                            "Tired": 2,
                            "Stressed": 2,
                            "Other": 5
                        }.get(feeling, 5),
                        soreness=feeling if feeling == "Sore" else "None",
                        cycle_phase=cycle_phase,
                        schedule_constraints=constraints if constraints.strip() else "None",
                        primary_goal=st.session_state.preferences.get("goal", "General fitness"),
                        user_id=st.session_state.user_id
                    )
                    # Store user preferences separately for LLM access
                    user_preferences = {
                        "liked_activities": st.session_state.preferences.get("likes", []),
                        "disliked_activities": st.session_state.preferences.get("dislikes", [])
                    }
                    
                    # Check if user is actually new (no real workout history)
                    try:
                        from src.vector_store import get_user_workout_history
                        user_workouts = get_user_workout_history(st.session_state.user_id, days_back=30)
                        if user_workouts:
                            # User has real workout history, use it
                            from src.models import UserHistory, WorkoutHistoryItem
                            real_workouts = []
                            for workout in user_workouts:
                                real_workouts.append(WorkoutHistoryItem(
                                    date=workout["date"],
                                    workout=workout["workout_plan"],
                                    perceived_effort="Moderate",  # Default since we don't have this data
                                    exercises=workout["exercises"],
                                    duration=workout["duration"],
                                    user_feeling=workout["user_feeling"],
                                    cycle_phase=workout["cycle_phase"]
                                ))
                            history = UserHistory(workouts=real_workouts, conversations=[], last_workout_date=user_workouts[0]["date"], workout_frequency={})
                        else:
                            # Truly new user, use empty history
                            from src.models import UserHistory
                            history = UserHistory(workouts=[], conversations=[], last_workout_date="", workout_frequency={})
                    except Exception:
                        # Fallback to empty history for new users
                        from src.models import UserHistory
                        history = UserHistory(workouts=[], conversations=[], last_workout_date="", workout_frequency={})
                    try:
                        past_context = retrieve_user_history(st.session_state.user_id)
                    except Exception:
                        past_context = []
                    try:
                        feedback = get_user_feedback(st.session_state.user_id)
                    except Exception:
                        feedback = []
                    
                    result = generate_recommendation(context, history, settings, past_context, feedback, user_preferences)
                    st.session_state.last_error = None
                    
                except Exception as e:
                    st.session_state.last_error = f"LLM error: {e}"
                    st.error(f"Error generating recommendation: {e}")
                    st.error("Please make sure Ollama is running and the model is available.")
                    st.stop()
                
                # Add to chat history (for memory) and session content
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                user_msg = f"Feeling: {feeling}, Cycle: {cycle_phase}, Duration: {duration}, Constraints: {constraints if constraints.strip() else 'None'}"
                assistant_msg = result.recommendation  # Use the LLM's full response directly
                
                # Store in chat history for memory (not displayed)
                st.session_state.chat_history.append({"role": "user", "content": user_msg, "timestamp": timestamp})
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg, "timestamp": timestamp})
                save_history(st.session_state.chat_history)
                
                # Store detailed workout and conversation history
                try:
                    from src.vector_store import store_workout_history, store_conversation_history
                    # Store workout history
                    store_workout_history(
                        user_id=st.session_state.user_id,
                        workout_plan=result.recommendation,
                        context=context,
                        exercises=[]  # Will be extracted automatically
                    )
                    # Store conversation history
                    store_conversation_history(
                        user_id=st.session_state.user_id,
                        role="user",
                        content=user_msg,
                        workout_generated=False
                    )
                    store_conversation_history(
                        user_id=st.session_state.user_id,
                        role="assistant",
                        content=assistant_msg,
                        workout_generated=True
                    )
                except Exception as e:
                    print(f"Error storing detailed history: {e}")
                
                # Add to session content for display
                st.session_state.session_content.append({"role": "user", "content": user_msg})
                st.session_state.session_content.append({"role": "assistant", "content": assistant_msg})
                
                # Save conversation to history
                save_current_conversation()
                
                # Store current recommendation for compatibility
                st.session_state.current_recommendation = assistant_msg
                st.session_state.first_recommendation_done = True
                st.session_state.new_session = False  # Mark as current session
                st.rerun()

    # Follow-up section
    if st.session_state.first_recommendation_done:
        st.markdown("---")
        st.subheader("Follow-up Questions")
        with st.form("follow_up_form"):
            follow_up = st.text_input("Ask anything about your workout or fitness", key="follow_up_input", placeholder="e.g., How do I modify this for beginners? What if I don't have equipment?")
            send_follow = st.form_submit_button("Send Follow-up", type="secondary")
            
            if send_follow:
                if follow_up.strip():
                    with st.spinner("Thinking..."):
                        try:
                            # Call Llama for follow-up response
                            from src.llm import OpenAI
                            from src.config import Settings
                            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
                            
                            # Create context-aware follow-up prompt
                            conversation_context = ""
                            if st.session_state.chat_history:
                                # Get last few messages for context
                                recent_msgs = st.session_state.chat_history[-4:]
                                for msg in recent_msgs:
                                    role = "User" if msg["role"] == "user" else "Assistant"
                                    conversation_context += f"{role}: {msg['content']}\n\n"
                            
                            follow_up_prompt = f"""You are a supportive AI fitness coach. Based on this conversation:

{conversation_context}

The user now asks: {follow_up.strip()}

Provide a helpful, detailed response that addresses their specific question. If they ask about exercise modifications, alternatives, or explanations, be thorough and practical. Keep your response conversational and encouraging."""
                            
                            response = client.chat.completions.create(
                                model=settings.openai_model,
                                messages=[
                                    {"role": "system", "content": "You are a supportive, knowledgeable AI fitness coach. Provide detailed, helpful answers to fitness questions."},
                                    {"role": "user", "content": follow_up_prompt}
                                ],
                                max_tokens=800,
                                temperature=0.7
                            )
                            response_text = response.choices[0].message.content
                        except Exception as e:
                            response_text = f"I'm here to help! You asked: {follow_up.strip()}\n\nCould you tell me more about what you'd like to know? I can provide exercise modifications, alternatives, or answer any fitness questions you have."
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.chat_history.append({"role": "user", "content": follow_up.strip(), "timestamp": timestamp})
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text, "timestamp": timestamp})
                    save_history(st.session_state.chat_history)
                    
                    # Store conversation history for follow-ups
                    try:
                        from src.vector_store import store_conversation_history
                        store_conversation_history(
                            user_id=st.session_state.user_id,
                            role="user",
                            content=follow_up.strip(),
                            workout_generated=False
                        )
                        store_conversation_history(
                            user_id=st.session_state.user_id,
                            role="assistant",
                            content=response_text,
                            workout_generated=False
                        )
                    except Exception as e:
                        print(f"Error storing follow-up history: {e}")
                    
                    # Add to session content for display (accumulates)
                    st.session_state.session_content.append({"role": "user", "content": follow_up.strip()})
                    st.session_state.session_content.append({"role": "assistant", "content": response_text})
                    
                    # Update current recommendation for compatibility
                    st.session_state.current_recommendation = response_text
                    st.rerun()

    # Action buttons
    st.markdown("---")
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.current_recommendation = None
        st.session_state.session_content = []
        st.session_state.first_recommendation_done = False
        st.session_state.new_session = True
        save_history([])
        st.rerun()
