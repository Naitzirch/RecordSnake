import random
import pandas as pd
import hashlib

def to_millis(time_str):
    """Convert mm:ss:ttt or ss:ttt string to milliseconds. Raises ValueError if format is invalid."""
    parts = time_str.split(":")
    if len(parts) == 3:
        minutes, seconds, millis = parts
    elif len(parts) == 2:
        minutes = 0
        seconds, millis = parts
    else:
        raise ValueError("Invalid time format. Expected mm:ss:ttt or ss:ttt.")
    return int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(millis)

def from_millis(millis):
    """Convert milliseconds to mm:ss:ttt string."""
    minutes = millis // (60 * 1000)
    millis %= (60 * 1000)
    seconds = millis // 1000
    millis %= 1000
    return f"{minutes:02}:{seconds:02}:{millis:03}"

def make_path(*parts):
    return ".".join(str(p) for p in parts)

def get_subkeys(data, path):
    keys = path.split(".") # Turn string into list
    for key in keys:
        data = data.get(key, {})
    return list(data.keys())

def get_data_from_path(d, path):
    path = path.split(".")
    for k in path:
        d = d.get(k, {})
    return d

# Generate a random number so long we find the random number in the submissions
def generate_random_id(queue):
    unique = False
    while(not unique):
        unique = True
        s_id = str(random.randint(1000, 9999))
        for subs in queue["submissions"]:
            if s_id == subs["id"]:
                unique = False
    return s_id

def get_user_info(Uid, users):
    return users.get(Uid)

def get_user_info_by_ign(platform, ign, users):
    for user in users:
        if user[platform].lower().strip() == ign.lower():
            return user
    return None

# Get platform emoji
def platform_emoji(platform):
    Emoji = "🤔"
    match platform:
        case "Java":
            Emoji = "☕"
        case "Bedrock":
            Emoji = "<:bedrock:1016464470412886067>"
    return Emoji

# Return a string that is a link to the user's forums profile if it exists
def forums_link(user, IGN=""):
    forums = "This person has not linked their forums account."
    if user['forums']:
        forums = f"[Forums profile]({user['forums']})".replace("_", "\_")
    return forums


# Try to access the google sheets document
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1yGtbKkYQSf4KGBZd_uHJ5m52hVLIgdI59o3vqmN0F2Q/edit?usp=sharing"
SAMPLE_SPREADSHEET_ID = "1yGtbKkYQSf4KGBZd_uHJ5m52hVLIgdI59o3vqmN0F2Q"
SAMPLE_RANGE_NAME = "Records!B5:J400"

def get_ext_player_data():
    """Get player data from the google sheet leaderboard

    Returns:
        Pandas DataFrame: empty if data couldn't be fetched for some reason. Filled with all columns if the data could be fetched
    """
    df = pd.DataFrame()
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("database/login/token.json"):
        creds = Credentials.from_authorized_user_file("database/login/token.json", SCOPES)
    # If there are no (valid) credentials available, tell the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Administrator must log in")
            return df

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return df
        df = pd.DataFrame( values )

    except HttpError as err:
        print(err)

    # Clean the df
    df = df.drop([7], axis=1)
    df = df.rename(columns={0: "Position", 1: "Player", 2: "Records", 3: "Platform", 4: "OCR", 5: "LCR", 6: "RC", 8: "discord_id"})

    return df
    
