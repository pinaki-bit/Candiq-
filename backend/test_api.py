import requests

url = 'http://localhost:8000/api/v1/resumes/candidate-analyze'

# Need a valid token, but maybe we can just expect 401 instead of 404/500 to know it's alive
response = requests.post(url, files={'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')})

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
