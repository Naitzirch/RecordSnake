import random
import pandas as pd


EXCEL_URL_TXT = open("EXCEL_URL.txt", "r")
EXCEL_URL = EXCEL_URL_TXT.read()
EXCEL_URL_TXT.close()


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
    for user in users:
        if user["id"] == Uid:
            return user
    return None

def get_user_info_by_ign(ign, users):
    for user in users:
        if user["IGN"] == ign:
            return user
    return None

def get_ext_player_data():
    # Try to download and read the onedrive excel file into a df
    df = None
    try:
        df = pd.read_excel(EXCEL_URL, 'Test', engine='openpyxl')    # add sheetname here
        # Use engine='openpyxl' to handle .xlsx files
    except Exception as e:
        print("An error occurred while reading the Excel file:", e)
        return

    # Clean the df
    df = df.drop(['Unnamed: 0', 'Unnamed: 1'], axis=1)
    df = df.rename(columns={"Unnamed: 2": "Position", "Unnamed: 3": "Player", "Unnamed: 4": "Records"})[2:]

    return df
    
