import os
import json
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# بيانات تقويم وهمية للاختبار
MY_CALENDAR = [{"date": "2026-04-27", "event": "Project Presentation", "time": "10:00 AM"}]

def search_flights_live(origin, dest, date, stops=None):
    url = "https://serpapi.com/search.json" 
    params = {
        "engine": "google_flights",
        "departure_id": origin, "arrival_id": dest, "outbound_date": date,
        "type": "2", "currency": "AED", "stops": stops,
        "api_key": os.getenv("SERP_API_KEY")
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        flights = data.get("best_flights") or data.get("other_flights") or []
        if not flights: return "No flights found."
        return json.dumps([{"airline": f["flights"][0]["airline"], "price": f["price"], 
                            "duration": f["total_duration"], "id": f.get("type")} for f in flights[:5]])
    except Exception as e:
        return json.dumps({"error": str(e)})

def check_calendar(date):
    events = [e for e in MY_CALENDAR if e["date"] == date]
    return json.dumps({"status": "busy", "conflicts": events}) if events else json.dumps({"status": "free"})

def get_weather(city, date):
    return f"The weather in {city} on {date} is sunny, 25°C."

def add_to_watchlist(origin, dest, target_price):
    with sqlite3.connect('agent_v2.db') as conn:
        conn.execute("INSERT INTO watchlist (origin, dest, target_price) VALUES (?, ?, ?)", (origin, dest, target_price))
    return f"✅ Saved! I will monitor flight prices from {origin} to {dest} at {target_price} AED."

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_flights_live",
            "description": "البحث عن رحلات طيران حقيقية.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"}, "dest": {"type": "string"}, "date": {"type": "string"},
                    "stops": {"type": "integer"}
                },
                "required": ["origin", "dest", "date"]
            }
        }
    },
    # احذف الـ dictionary الخاص بـ check_calendar من هنا
    {"type": "function", "function": {"name": "get_weather", "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "date": {"type": "string"}}, "required": ["city", "date"]}}},
    {"type": "function", "function": {"name": "add_to_watchlist", "parameters": {"type": "object", "properties": {"origin": {"type": "string"}, "dest": {"type": "string"}, "target_price": {"type": "number"}}, "required": ["origin", "dest", "target_price"]}}}
]