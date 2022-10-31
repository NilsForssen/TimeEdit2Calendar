#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import datetime
from dataclasses import dataclass
import re
import googleCalendar

""" Install before running file:

pip install requests
pip install beautifulsoup4
pip install lxml
"""


@dataclass
class event:
    summary: str
    description: str
    start: datetime.datetime
    end: datetime.datetime
    t_offset: str = "+01:00"

    def get_gc_event(self):
        event = {
            "summary": self.summary,
            "description": self.description,
            "start": {
                "dateTime": "{0}T{1}{2}".format(
                    self.start.date(), self.start.time(), self.t_offset
                )
            },
            "end": {
                "dateTime": "{0}T{1}{2}".format(
                    self.end.date(), self.end.time(), self.t_offset
                )
            },
            "reminders": {
                "useDefault": False,
                "overrides": [],  # Reminders would drive me crazy
            },
            "colorId": googleCalendar.EVENT_COLORIDS["blue"],
        }

        return event


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
}
schedule_URL = "https://cloud.timeedit.net/liu/web/schema/ri167XQQ617Z50Qm07060gZ6y6Y7606Q6Y95Y2.html"

with requests.Session() as session:
    data = session.get(
        schedule_URL,
        headers=headers,
        verify=False,
    )

soup = BeautifulSoup(data.content, features="lxml")
table = soup.find("table", attrs={"class": "restable"})
rows = table.find_all("tr")

schedule = []
active_day = ""
for row in rows[2:]:
    date = row.find("td", attrs={"class": "headline t"})
    if date is not None:
        match = re.search(r"\d{4}-\d{2}-\d{2}", date.text.strip())
        active_day = match.group()
    else:
        try:
            time = row.find("td", attrs={"class": "time tt c-1"})
            if time is not None:
                info = [
                    col.text.strip()
                    for col in row.find_all("td")
                    if "columnLine" in col["class"]
                ]
                summary = f"{info[0]} - {info[1]}, {info[2]}"
                description = f"{info[0]}, {info[1]}, {info[2]}, {info[3]}, {info[5]}, {info[5]}\nautogen_nils\nCreated: {datetime.datetime.now()}"
                active_time = time.text.strip()
                start = datetime.datetime.strptime(
                    active_day + active_time[:5], "%Y-%m-%d%H:%M"
                )
                end = datetime.datetime.strptime(
                    active_day + active_time[8:], "%Y-%m-%d%H:%M"
                )
                schedule.append(event(summary, description, start, end))
        except Exception as e:
            print(e)
        else:
            print(f"strange row: {row.content}")

for c_event in googleCalendar.listEvents(
    **{
        "timeMin": "{0}T{1}{2}".format(
            schedule[0].start.date(), schedule[0].start.time(), schedule[0].t_offset
        )
    }
):
    try:
        if "\nautogen_nils" in c_event["description"]:
            googleCalendar.deleteEvent(c_event["id"])
    except KeyError:
        pass

for n_event in schedule:
    googleCalendar.createEvent(n_event.get_gc_event())
    print(f"Created: {n_event}\n")
