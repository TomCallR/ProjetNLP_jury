import dataclasses
import json
from datetime import date, datetime
from typing import List


class Const:
    DBTRUE = "Y"
    DBFALSE = "N"


@dataclasses.dataclass
class NumAnswers:
    questiontext: str
    grades: List[int]
    count: int
    average: float


#
# class DateTimeEncoder(json.JSONEncoder):
#     # See example in https://docs.python.org/3.7/library/json.html
#     def default(self, obj):
#         res = None
#         if isinstance(obj, datetime):
#             res = [obj.year, obj.month, obj.day, obj.hour, obj.min, obj.second]
#         # Let the base class default method raise the TypeError
#         else:
#             res = json.JSONEncoder.default(self, obj)
#         return res


class DateEncoder(json.JSONEncoder):
    # See example in https://docs.python.org/3.7/library/json.html
    def default(self, obj):
        if isinstance(obj, date):
            res = [obj.year, obj.month, obj.day]
        # Let the base class default method raise the TypeError
        else:
            res = json.JSONEncoder.default(self, obj)
        return res


class DateDecoder:
    @classmethod
    def decode(cls, obj) -> datetime.date:
        res = None
        if isinstance(obj, str):
            strdate = obj.replace(" ", "")
            res = datetime.strptime(strdate, "[%Y,%m,%d]")
        return res


@dataclasses.dataclass
class Params:

    @classmethod
    def getmindate(cls):
        return date(year=2000, month=1, day=1)

    @classmethod
    def getmaxdate(cls):
        return date(year=2100, month=1, day=1)
