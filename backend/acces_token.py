import requests

url = "https://services.leadconnectorhq.com/oauth/token"

data = {
    "client_id": "68ed64854dc0537c00502b1f-mgpu22ve",
    "client_secret": "0da26c21-4b10-478b-99b3-e13f374be2e8",
    "grant_type": "authorization_code",
    "redirect_uri": "http://localhost:8000/oauth/callback/",
    "code": "3937e1a9696470e5beedcdbc5b70c6ba107345de"
}

response = requests.post(url, data=data)
print(response.json())