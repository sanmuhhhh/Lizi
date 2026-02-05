#!/usr/bin/env python3
"""栗子的手表 - 看时间用的"""

from datetime import datetime

weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

now = datetime.now()
weekday = weekdays[now.weekday()]

print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} {weekday}")
