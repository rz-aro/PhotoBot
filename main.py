from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json
import pickle
import os
from dotenv import load_dotenv
import time
load_dotenv()

# Replace with your bot token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = "C0937EQ82PN"  # Replace with your channel ID

client = WebClient(token=SLACK_BOT_TOKEN)
# join the channel

# client.conversations_join(channel=CHANNEL_ID)
headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
}

next_cursor = None
caption_dict = []
try:
    while True:
        # Call the conversations.history method using the WebClient
        try:
            response = client.conversations_history(channel=CHANNEL_ID, limit=1000, cursor=next_cursor)
        except SlackApiError as e:
            time.sleep(15)  # To avoid hitting rate limits
            response = client.conversations_history(channel=CHANNEL_ID, limit=1000, cursor=next_cursor)

        time.sleep(15)  # To avoid hitting rate limits
        messages = response["messages"]
        # print(f"Messages: {json.dumps(messages, indent=2)}")
        # print(f"Fetched {len(messages)} messages from the channel: {CHANNEL_ID}")
        # print(f"response_metadata : {json.dumps(response.get('response_metadata', {}), indent=2)}   ")

        next_cursor = response.get("response_metadata", {}).get("next_cursor", None)
        if not next_cursor:
            break
            
        print(f"Fetched {len(messages)} messages from the channel:") 
        for msg in messages:
            files = msg.get("files", [])
            if files:
                user = msg.get("user", "Unknown")
                try: 
                    userdata = client.users_info(user=user)
                    try:
                        username = userdata.get("user", {}).get("profile", {}).get("real_name", "Unknown")
                    except SlackApiError as e:
                        time.sleep(15)  # To avoid hitting rate limits
                        username = userdata.get("user", {}).get("profile", {}).get("real_name", "Unknown")
                    print(f"Username: {username}")
                except SlackApiError as e:
                    print(f"Error fetching user info: {e.response['error']}")
                    username = user
                # username = user
                print(f"User: {username}")
                text = msg.get("text", "")
                ts = msg.get("ts", "")
                image = files[0].get("url_private", "")
                print(f"Image URL: {image}")
                # download and save the image
                filename = files[0].get("name", "")
                caption_dict.append([filename, text, username])
                # response = requests.get(image, headers=headers)
                # if response.status_code == 200:
                    # with open(f"Downloads/{filename}", "wb") as f:
                    #     f.write(response.content)
                #     caption_dict.append([filename, text, username])
                #     print(f"Image saved as {filename}")
                # else:
                #     print(f"Failed to download image: {response.status_code}")
            
            print(f"[{ts}] {user}: {text}")
except SlackApiError as e:
    print(f"Error fetching messages: {e.response['error']}")
with open("captions.pkl", "wb") as f:
    pickle.dump(caption_dict, f)
print(f"Caption dictionary saved to captions.pkl")
        
# except SlackApiError as e:
#     print(f"Error fetching messages: {e.response['error']}")
