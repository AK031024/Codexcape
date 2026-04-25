import google.generativeai as genai

class BackgroundGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_background_description(self, theme="nature"):
        themes = {
            "nature": """
            Create a serene natural environment with:
            - Gentle swaying trees
            - Soft moving clouds
            - Subtle light effects
            - Calming color palette
            Focus on smooth, subtle movements and transitions.
            """,
            "ocean": """
            Design a peaceful ocean scene featuring:
            - Gentle waves
            - Floating particles
            - Underwater light rays
            - Marine life silhouettes
            Emphasize fluid movements and transparency.
            """,
            "forest": """
            Generate a dynamic forest atmosphere with:
            - Rustling leaves
            - Dappled sunlight
            - Floating seeds/pollen
            - Forest floor details
            Focus on organic movements and natural lighting.
            """
        }
        
        try:
            prompt = themes.get(theme, themes["nature"])
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Background Generation Error: {str(e)}")
            return None

    def get_animation_parameters(self, mood="calm"):
        parameters = {
            "calm": {
                "speed": "slow",
                "intensity": "low",
                "colors": ["#2E7D32", "#1B5E20", "#43A047"],
                "pattern": "waves"
            },
            "energetic": {
                "speed": "medium",
                "intensity": "high",
                "colors": ["#2E7D32", "#43A047", "#66BB6A"],
                "pattern": "particles"
            },
            "focused": {
                "speed": "slow",
                "intensity": "medium",
                "colors": ["#1B5E20", "#2E7D32", "#388E3C"],
                "pattern": "gradient"
            }
        }
        return parameters.get(mood, parameters["calm"])
