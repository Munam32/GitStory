import requests
import json
import re
import os
from dotenv import load_dotenv
# for testing and running code review API.
load_dotenv()

url = "http://localhost:8002/api/review"
# Use a token from environment or a dummy one
#github_token = os.environ.get("GITHUB_TOKEN", "<github_token>") # token to validate ownership

payload = {
    "repo_url": "https://github.com/MSabihkhan/GitStory", #this repo must be public for testing without a valid token
    "commit_count": 3,
    "github_token": github_token
}

print(f"Sending request to AI Reviewer for {payload['repo_url']}...")
try:
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Analyzed {data['files_analyzed']} files.")
        
        health_score = data.get('health_score')
        print(f"📊 Codebase Health Score: {health_score}")
        
        # Validation
        if health_score is not None and 0 <= health_score <= 100:
            print("✅ Health Score is valid (0-100).")
        else:
            print("❌ Invalid Health Score!")

        review_text = data.get('review', "")
        
        # Check for severity tags
        has_severity = any(tag in review_text for tag in ["[Critical]", "[Warning]", "[Info]"])
        if has_severity:
            print("✅ Found severity tags ([Critical], [Warning], [Info]).")
        else:
            print("⚠️ No severity tags found in review.")

        # Check for Location (File/Line)
        has_location = re.search(r"File:.*Line:", review_text)
        if has_location:
            print("✅ Found file/line references.")
        else:
            print("⚠️ No file/line references found.")

        # Check for Suggestion
        if "Suggestion:" in review_text:
            print("✅ Found actionable suggestions.")
        else:
            print("⚠️ No suggestions found.")

        print("\n--- AI Review Snippet ---")
        print(review_text[:1000] + "...") 
    elif response.status_code == 403:
        print(f"🔒 Ownership verification failed as expected: {response.json()['detail']}")
    elif response.status_code == 401:
        print(f"🔑 Authentication failed: {response.json()['detail']}")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Connection failed: {e}. Make sure the server is running.")