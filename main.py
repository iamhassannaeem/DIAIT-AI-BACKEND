
from ml.app import *
import os
from dotenv import load_dotenv
from urllib.parse import urlparse


env_path = os.path.join('./ml/.env')
print(f"Loading .env file from: {env_path}")
print(load_dotenv(env_path)) 


def save_value_to_env(key, value, path):
    print(f"Saving {key}={value} to {path}")
    
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    updated = False
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = f"{key}={value}\n"
            updated = True
            break

    if not updated:
        lines.append(f"\n{key}={value}")

    with open(path, 'w') as file:
        file.writelines(lines)
    print(f"{key} saved successfully to {path}")


if __name__ == "__main__":
    import uvicorn
    try:
        # listener = ngrok.connect(f"http://localhost:{PORT}")
        # print(f"Ngrok tunnel opened at {listener.public_url} for port {PORT}")
        # NGROK_URL = listener.public_url
        # parsed_url = urlparse(NGROK_URL)

        # save_value_to_env("HOST", parsed_url.hostname, env_path)

        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]

        client.incoming_phone_numbers(twilio_number_sid).update(
            account_sid,
            voice_url=f"https://{os.environ['HOST']}/{INCOMING_CALL_ROUTE}?a='1122'"
        )

        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
    finally:
        exit
