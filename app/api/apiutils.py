import os
from typing import List

import gspread
from flask import flash
from oauth2client.service_account import ServiceAccountCredentials

from app import app


class ApiAccess:
    API_SCOPE = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
    CREDENTIALS_FILE = "private/api_credentials.json"  # TODO put in a conf w/ complete path : dangerous on windows
    TIMESTAMP_HEADER = "Horodateur"
    EMAIL_HEADER = "Adresse e-mail"

    def __init__(self):
        self.client = None

    @classmethod
    def getwsheetdata(cls, wsheet: gspread.models.Worksheet) -> List[dict]:
        res = []
        if wsheet is not None:
            try:
                res = wsheet.get_all_records()
            except IndexError:
                flash(f"Erreur : Onglet {wsheet.title} du fichier {wsheet.spreadsheet.title} vide")
                pass
        return res

    @classmethod
    def getmetadata(cls, spreadsheet: gspread.models.Spreadsheet):
        metadata = None
        try:
            metadata = spreadsheet.fetch_sheet_metadata()
        except PermissionError:
            flash("Erreur : Accès refusé (avez-vous partagé le fichier avec le mail du credential ?)")
        return metadata

    def initclient(self):
        projectpath, appdir = os.path.split(app.root_path)
        credfile = os.path.join(projectpath, self.CREDENTIALS_FILE)
        creds = None
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                filename=credfile, scopes=self.API_SCOPE)
        except ValueError:
            flash("Erreur : Type de credentials différent de `SERVICE_ACCOUNT`")
        except KeyError:
            flash("Erreur : Erreur d'index lors de l'obtention de l'accès à l'API Google")
        self.client = gspread.authorize(creds)

    def getfile(self, fileid: str) -> (bool, gspread.models.Spreadsheet):
        spreadsheet = None
        if self.client is None:
            self.initclient()
        try:
            spreadsheet = self.client.open_by_key(key=fileid)
        except gspread.exceptions.SpreadsheetNotFound:
            flash(f"Erreur : Fichier id {fileid} non trouvé")
        return spreadsheet
