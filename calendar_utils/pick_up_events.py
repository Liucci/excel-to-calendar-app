from googleapiclient.discovery import Resource
from typing import List
from datetime import datetime, timezone
import calendar
def pick_up_events(service: Resource, calendar_id: str, year: int, month: int, tags: List[str] = None):
    """
    指定年月とタグで予定を抽出
    :param service: Google Calendar API サービス
    :param calendar_id: カレンダーID（通常 'primary'）
    :param year: 対象年
    :param month: 対象月
    :param tag: description に含まれるタグ（例: [勤務表=MAIN]）
    :return: 該当イベントのリスト
    """

# 月初
    start = datetime(year, month, 1, tzinfo=timezone.utc)
# 月末
    last_day = calendar.monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    print(f"events:\n{events}")
    #google calendar api から取得では、月を指定しても翌月１日イベントも含めて取得されることがあるため、年月で再フィルタリング
    same_month_events = []
    for e in events:
        start = e.get("start", {})

        if "dateTime" in start:  # 時間指定イベント
            start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
        elif "date" in start:  # 終日イベント
            start_dt = datetime.fromisoformat(start["date"] + "T00:00:00+00:00")
        else:
            continue

        # 年月が一致するかどうか
        if start_dt.year == year and start_dt.month == month:
            same_month_events.append(e)
    
    print("same_month_events:")
    for a in same_month_events:
        print(f"・{a}")            

 # --- タグでフィルタリング ---
    if tags:
        # 安全のためタグはすべて文字列化＆前後の空白削除
        normalized_tags = [t.strip() for t in tags if isinstance(t, str)]
        filtered_events = []
        for e in same_month_events:
            desc = e.get("description", "") or ""
            desc_norm = desc.replace("\u3000", " ").strip()  # 全角空白除去
            if any(tag in desc_norm for tag in normalized_tags):
                filtered_events.append(e)
    else:
        filtered_events = same_month_events    
    
    print(f"filterd_events:\n{filtered_events}")
    
    simplified_events = []
    for e in filtered_events:
        simplified_events.append({
            "start": e.get("start", {}),
            "end": e.get("end", {}),
            "summary": e.get("summary"),
            "description": e.get("description", ""),
            "id": e.get("id")
        })


    print(f"[DEBUG] pick_up_events() で抽出されたイベント数: {len(simplified_events)}")
    print(f"[DEBUG] pick_up_events()で抽出されたイベントの３例: {simplified_events[:3]}")  # 最初の3つのイベントを表示
    for i, ev in enumerate(simplified_events[:3]):
        print(f"[DEBUG] html_events[{i}] type: {type(ev)}")
        for key in [ 'start', 'end', 'summary', 'description']:
            print(f"    {key}: {ev.get(key)} (type: {type(ev.get(key))})")
        print(f"  {ev['start']}～{ev['end']}: {ev['summary']} | {ev['description']}")    
    
    return simplified_events
