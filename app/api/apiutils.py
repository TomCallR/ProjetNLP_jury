import gspread

import app
from oauth2client.service_account import ServiceAccountCredentials


class ApiFile:

    def __init__(self):
        self.client = None

    def initclient(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            filename=app.config.CREDENTIALS_FILE, scopes=app.config.API_SCOPE)
        self.client = gspread.authorize(creds)

    def getfile(self, name: str) -> (bool, str, gspread.models.Spreadsheet):
        success = False
        message = ""
        if self.client is None:
            self.initclient()
        try:
            spreadsheet = self.client.open(title=name)
            success = True
        except gspread.exceptions.SpreadsheetNotFound:
            message = f"Erreur : Impossible de trouver le fichier {name}"
        return success, message, spreadsheet


