import requests

# Tokens received from your previous request
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI4MDM4NjE2LCJpYXQiOjE3Mjc5NTIyMTYsImp0aSI6ImY3MTc3ODg1YzE4NzRiMGNhNDIxNzNjOGE0YmRiMTk4IiwidXNlcl9pZCI6MTV9.19Fl0xiyTQZ7NxuM35I03Niyfmp0y73GWtH7vEWwvMs"

# URL for the API endpoint where you want to send the POST request
url = "http://127.0.0.1:8000/aut/logout"  # Replace with your actual URL

# Prepare the JSON payload to be sent in the POST request
payload = {
    "key1": "value1",
    "key2": "value2",
    # Add more key-value pairs as needed
}

# Set up the headers for the request
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Check the response status code and content
print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.text}")

# Attempt to parse JSON response
try:
    response_data = response.json()  # Attempt to parse JSON
    print("Data received:", response_data)
except requests.exceptions.JSONDecodeError:
    print("Response is not in JSON format or is empty.")
