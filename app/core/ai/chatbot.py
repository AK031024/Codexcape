import google.generativeai as genai
from datetime import datetime

class EnvironmentalTurtle:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])
        self.personality = """
        You are EcoTurtle, a friendly and knowledgeable environmental assistant with the personality of a wise turtle. 
        You are passionate about environmental conservation and helping users reduce their carbon footprint.
        Always maintain a gentle, encouraging tone and include relevant emojis.
        Keep responses concise but informative, and focus on actionable environmental tips.
        """

    def get_response(self, user_input, user_logs=None):
        context = f"""
        User's recent carbon logs: {user_logs if user_logs else 'No recent logs'}
        Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        prompt = f"{self.personality}\n{context}\nUser: {user_input}"
        
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"🐢 Oops! I'm having trouble connecting right now. Please try again! Error: {str(e)}"

    def get_eco_tip(self, user_activity):
        prompt = f"""
        Based on this user activity: {user_activity}
        Provide a short, specific eco-friendly tip to reduce environmental impact.
        Keep it encouraging and practical.
        Include an appropriate emoji.
        Maximum 2 sentences.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "🌱 Keep up the great work on your sustainability journey!"

    def get_background_prompt(self, user_mood=None):
        prompts = {
            'default': "Create a serene nature scene with gentle movement",
            'active': "Dynamic forest canopy with sunlight filtering through leaves",
            'calm': "Peaceful ocean waves with subtle ripples",
            'motivated': "Vibrant sunrise over mountains with moving clouds"
        }
        return prompts.get(user_mood, prompts['default'])
