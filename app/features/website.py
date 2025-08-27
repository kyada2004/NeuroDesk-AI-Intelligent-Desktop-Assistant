import webbrowser
import os
import re

def handle_open_website(query):
    match = re.search(r"open\s+([a-zA-Z0-9.\-]+)", query.lower())
    if match:
        domain = match.group(1)
        if '.' not in domain:
            # Handles cases like "open google"
            url = f"https://www.{domain}.com"
        else:
            # Handles cases like "open google.com"
            if not domain.startswith(('http://', 'https://')):
                url = f"https://{domain}"
            else:
                url = domain
        webbrowser.open(url)
        return f"Opening {url}"
    else:
        return "Please specify a website to open."

def handle_close_website(query):
    os.system("taskkill /f /im chrome.exe") 
    return "All browser windows closed."
