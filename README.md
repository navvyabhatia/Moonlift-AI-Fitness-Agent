# Moonlift-AI-Fitness-Agent
Moonlift is an AI-Powered Fitness Coach designed with women’s wellness in mind. It creates personalized workouts based on energy, cycle phase, goals, schedule, and activity preferences. Built with Python, Streamlit, and Ollama, it provides private AI coaching that adapts using saved preferences and workout history, making fitness personal each day.

# Project Objective
A workout plan can feel unrealistic when it ignores energy, soreness, time, or changing preferences. Moonlift brings these details into one place so users can request a session that fits their day. It was designed with women's wellness in mind while letting each person choose the information they share.

# Objectives
- Generate workouts that reflect daily energy, cycle phase, time, and constraints.
- Let users choose activities they enjoy and avoid those they dislike.
- Use previous sessions and feedback to make later recommendations more relevant.
- Provide an easy way to revisit conversations and workouts.
- Keep the AI model and saved data on the user's own machine.

# Technologies Used
- Python
- Streamlit — provides the user interface
- Ollama — runs the llama3.1:8b model locally
  
# How it Works
1. Create a profile and choose your preferred activities.
2. Enter how you feel, your cycle phase, available time, and any limitations.
3. Moonlift uses those details to generate a workout with Ollama.
4. Review the workout and ask follow-up questions.
5. Return to your saved conversations and preferences later.

# Repository Structure
moonlift/
├── app.py
├── ARCHITECTURE.md
├── Demo.mp4
└── README.md

# Future Recommendations for Improvements
- Show workout progress more clearly.
- Make the app easier to use on phones.
- Let users change their workouts.
- Offer the app in more languages.
