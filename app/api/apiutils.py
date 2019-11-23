import os

import gspread

from app import app
from oauth2client.service_account import ServiceAccountCredentials


class ApiAccess:

    API_SCOPE = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
    CREDENTIALS_FILE = "private/api_secret.json"            # TODO put in a conf w/ complete path : dangerous on windows
    TIMESTAMP_HEADER = "Horodateur"
    EMAIL_HEADER = "Adresse e-mail"

    def __init__(self):
        self.client = None

    def initclient(self):
        projectpath = os.path.split(app.root_path)[0]
        credfile = os.path.join(projectpath, self.CREDENTIALS_FILE)
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            filename=credfile, scopes=self.API_SCOPE)
        self.client = gspread.authorize(creds)

    def getfile(self, name: str) -> (bool, str, gspread.models.Spreadsheet):
        success = False
        message = ""
        spreadsheet = None
        if self.client is None:
            self.initclient()
        try:
            spreadsheet = self.client.open(title=name)
            success = True
        except gspread.exceptions.SpreadsheetNotFound as ex:
            message = f"Erreur : Impossible de trouver le fichier {name}"
        return success, message, spreadsheet


