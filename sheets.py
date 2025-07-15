import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_ID = "1v7lqkE3n3A43z58D7WctuwFybTdzHOG0lL3Q9Z1vx2s"
WORKSHEET_NAME = "Sheet1"

def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(WORKSHEET_NAME)

def append_result_row(source, query, query_category, max_similarity, time_start, time_end, accuracy, notes):
    sheet = init_sheet()
    row = [source, query, query_category, max_similarity, time_start, time_end, accuracy, notes]
    sheet.append_row(row)
