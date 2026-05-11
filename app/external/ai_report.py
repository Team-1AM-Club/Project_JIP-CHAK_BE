from openai import OpenAI
import os
 
client = OpenAI(
    api_key=os.getenv("UPSTAGE_AI_API_KEY"),
    base_url="https://api.upstage.ai/v2"
)