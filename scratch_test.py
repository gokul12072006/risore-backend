import os, requests
from dotenv import load_dotenv
load_dotenv('.env')
key = os.getenv('GROQ_API_KEY')
models_to_test = ['llama-3.2-11b-vision-preview', 'llama-3.2-11b-vision', 'llama-3.2-90b-vision-preview', 'llama-3.2-90b-vision']
for m in models_to_test:
    res = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': m, 'messages': [{'role': 'user', 'content': 'hi'}]}
    )
    print(f'{m}: {res.status_code} - {res.json().get("error", {}).get("message", "SUCCESS")}')
