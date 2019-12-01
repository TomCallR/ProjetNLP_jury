import dataclasses
import json
import math
from datetime import date, datetime, timedelta
from typing import List

from flask import session


class Const:
    DBTRUE = "Y"
    DBFALSE = "N"
    DEFAULT_DAYS_UNCHANGED = 15
    MAX_DAYS_SHEET_UNCHANGED = "MAX_DAYS_SHEET_UNCHANGED"
    MAX_DAYS_TO_ENDDATE = "MAX_DAYS_TO_ENDDATE"
    DASHBOARD_COURSE_IDS = "DASHBOARD_COURSE_IDS"
    DASHBOARD_STUDENT_IDS = "DASHBOARD_STUDENT_IDS"
    DASHBOARD_STARTDATE = "DASHBOARD_STARTDATE"
    DASHBOARD_ENDDATE = "DASHBOARD_ENDDATE"


@dataclasses.dataclass
class Params:

    @classmethod
    def getmindate(cls):
        return date(year=2000, month=1, day=1)

    @classmethod
    def getmaxdate(cls):
        return date(year=2100, month=1, day=1)

    @classmethod
    def getsessionvar(cls, name: str, default: any = None):
        try:
            res = session[name]
        except KeyError:
            res = default
        return res


class DTime:

    @classmethod
    def min(cls) -> datetime:
        return datetime(year=2000, month=1, day=1)

    @classmethod
    def max(cls) -> datetime:
        return datetime(year=2100, month=1, day=1)

    @classmethod
    def timedelta2days(cls, delta: timedelta) -> int:
        res = 0
        if delta is not None:
            sec = delta.total_seconds() / 3600 / 24
            res = math.ceil(sec)
        return res

    @classmethod
    def datetimeencode(cls, daytime: datetime) -> List[int]:
        res = []
        if daytime is not None:
            res = [daytime.year, daytime.month, daytime.day, daytime.hour, daytime.minute, daytime.second]
        return res

    @classmethod
    def datetimedecode(cls, daytime: List[int]) -> datetime:
        res = None
        if daytime is not None:
            if len(daytime) >= 6:
                res = datetime(year=daytime[0], month=daytime[1], day=daytime[2],
                               hour=daytime[3], minute=daytime[4], second=daytime[5])
        return res


@dataclasses.dataclass
class NumAnswers:
    questiontext: str
    grades: List[int]
    count: int
    average: float
