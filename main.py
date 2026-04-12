import os
import json
from openai import OpenAI
from tools import search_flights_live, check_calendar, add_to_watchlist, get_weather, tools_schema

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
available_actions = {
    "search_flights_live": search_flights_live, "check_calendar": check_calendar,
    "add_to_watchlist": add_to_watchlist, "get_weather": get_weather
}

def run_agent(user_query):
    messages = [
        {"role": "system", "content": """
        You are a proactive Travel Assistant.
        1. Convert city names to IATA codes (e.g. Dubai -> DXB).
        2. Check 'Stop Preference' in Context: If 0, set stops=0 in search.
        3. ALWAYS check the weather for the destination before finalizing the response.
        4. If the flight price is higher than the user's budget, suggest 'add_to_watchlist'.
        5. DO NOT check or mention the user's calendar or schedule.
        6. Always respond in English.
        Current Date: 2026-04-12.
        """},
        {"role": "user", "content": user_query}
    ]
    
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools_schema)
    msg = response.choices[0].message
    
    if msg.tool_calls:
        messages.append(msg)
        for tool in msg.tool_calls:
            args = json.loads(tool.function.arguments)
            result = available_actions[tool.function.name](**args)
            messages.append({"tool_call_id": tool.id, "role": "tool", "name": tool.function.name, "content": result})
        
        final = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return final.choices[0].message.content
    return msg.content