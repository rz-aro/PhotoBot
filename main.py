from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

# Replace with your bot token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = "C0937EQ82PN"  # Replace with your channel ID

client = WebClient(token=SLACK_BOT_TOKEN)
#join the channel

# client.conversations_join(channel=CHANNEL_ID)
headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
}

try:
    # Call the conversations.history method using the WebClient
    response = client.conversations_history(channel=CHANNEL_ID, limit=30)

    messages = response["messages"]
    caption_dict = []
    print(f"Fetched {len(messages)} messages from the channel:") 
    for msg in messages:
        print(json.dumps(msg, indent=2))
        user = msg.get("user", "Unknown")
        # username = client.users_info(user=user).get("user", {}).get("name", "Unknown")
        username = user
        print(f"User: {username}")
        text = msg.get("text", "")
        ts = msg.get("ts", "")
        files = msg.get("files", [])
        if files:
            image = files[0].get("url_private", "")
            print(f"Image URL: {image}")
            # download and save the image
            filename = files[0].get("name", "")
            response = requests.get(image, headers=headers)
            if response.status_code == 200:
                with open(f"Downloads/{filename}", "wb") as f:
                    f.write(response.content)
                caption_dict.append([filename, text, username])
                print(f"Image saved as {filename}")
            else:
                print(f"Failed to download image: {response.status_code}")
        
        print(f"[{ts}] {user}: {text}")
        with open("captions.pkl", "wb") as f:
            pickle.dump(caption_dict, f)
        print(f"Caption dictionary saved to captions.pkl")
        # load the captions from the pickle file
        
except SlackApiError as e:
    print(f"Error fetching messages: {e.response['error']}")
