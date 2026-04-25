import google.generativeai as genai
from datetime import datetime
import requests

class NewsFetcher:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def fetch_environmental_news(self):
        prompt = """
        Generate 5 current and significant environmental news stories.
        Focus on:
        1. Climate change developments
        2. Renewable energy advancements
        3. Conservation efforts
        4. Sustainable innovations
        5. Environmental policies

        Format each story as:
        TITLE: [Compelling Title]
        DATE: [Current Date]
        DESCRIPTION: [2-3 engaging sentences]
        IMPACT: [Brief environmental impact]

        Make it factual, current, and engaging.
        """

        try:
            response = self.model.generate_content(prompt)
            news_text = response.text.strip()
            
            # Parse the generated news into structured format
            news_items = []
            stories = news_text.split('\n\n')
            
            for story in stories:
                if 'TITLE:' in story:
                    lines = story.split('\n')
                    news_item = {
                        'title': lines[0].replace('TITLE:', '').strip(),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'description': next((line.replace('DESCRIPTION:', '').strip() 
                                          for line in lines if 'DESCRIPTION:' in line), ''),
                        'impact': next((line.replace('IMPACT:', '').strip() 
                                     for line in lines if 'IMPACT:' in line), '')
                    }
                    news_items.append(news_item)
            
            return news_items
        except Exception as e:
            print(f"News Generation Error: {str(e)}")
            return None

    def get_news_summary(self):
        prompt = """
        Provide a brief summary of the most significant environmental developments today.
        Include major climate actions, policy changes, and breakthrough technologies.
        Format: 3-4 concise bullet points with emojis.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "🌍 Stay tuned for environmental updates!"
