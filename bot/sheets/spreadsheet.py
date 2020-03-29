import pickle
import string
from typing import List

from django.utils import timezone
from googleapiclient.discovery import build

from bot import secrets
from models.models import DailyCheckin

bool_to_yes_no = {
    True: "Да",
    False: "Нет"
}


class Spreadsheet:
    def __init__(self, spreadsheet_id=None):
        if spreadsheet_id is None:
            spreadsheet_id = secrets.SPREADSHEET_ID
        service = build('sheets', 'v4', credentials=pickle.load(open("bot/sheets/secrets/token.pickle", "rb")))
        self.spreadsheet = service.spreadsheets()
        self.spreadsheet_id = spreadsheet_id

    def _daily_checkin_line(self, dc: DailyCheckin):
        return [timezone.localtime(dc.created).strftime('%d.%m.%Y %H:%M'),
                # работник
                dc.worker.full_name, dc.worker.position, dc.worker.boss,
                # дейлик
                bool_to_yes_no[dc.worked_today], dc.reason_not_worked, dc.tasks_done_today, dc.problems_today,
                bool_to_yes_no[dc.will_work_tomorrow], dc.tomorrow_tasks, dc.days_till_start_work]

    def _first_free_line(self, rows_taken_cell="Отчеты!Z1"):
        return int(
            self.spreadsheet.values().get(spreadsheetId=self.spreadsheet_id, range=rows_taken_cell).execute() \
                ["values"][0][0]
        ) + 1

    def _write_values(self, values: List[str]):
        free_row = self._first_free_line()
        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"Отчеты!{string.ascii_uppercase[0]}{free_row}:"
                             f"{string.ascii_uppercase[len(values) - 1]}{free_row}",
                    "majorDimension": "ROWS",
                    "values": [
                        values,
                    ]
                }
            ],
        }
        self.spreadsheet.values().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def write_daily_checkin(self, dc: DailyCheckin):
        self._write_values(self._daily_checkin_line(dc))
