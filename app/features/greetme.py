import datetime
from app.core.utils import say


def greetMe():
    """Greets the user based on the current time."""
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        greeting = "Good Morning, sir"
    elif 12 <= hour < 18:
        greeting = "Good Afternoon, sir"
    else:
        greeting = "Good Evening, sir"

    say(f"{greeting}. Please tell me, how can I help you?")
    return f"{greeting}. Please tell me, how can I help you?"
