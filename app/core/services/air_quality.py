import requests
from datetime import datetime

class AirQualityMonitor:
    def __init__(self, api_config):
        self.api_key = api_config['key']
        self.endpoint = api_config['endpoint']

    def get_air_quality(self, latitude, longitude):
        try:
            # Simulate air quality data (replace with actual API call)
            return {
                'aqi': 45,
                'category': 'Good',
                'pollutants': {
                    'pm25': 10.5,
                    'pm10': 20.3,
                    'o3': 35.2
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Air Quality Error: {str(e)}")
            return None

    def get_recommendations(self, aqi):
        if aqi <= 50:
            return "🌿 Air quality is good! Perfect for outdoor activities."
        elif aqi <= 100:
            return "😊 Moderate air quality. Consider reducing extended outdoor activities."
        else:
            return "⚠️ Poor air quality. Limit outdoor exposure."
