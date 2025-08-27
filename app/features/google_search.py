import webbrowser

def handle_google_search(query):
    search_query = query.lower().replace("google search", "").replace("search google for", "").replace("google", "").strip()
    if search_query:
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching Google for: {search_query}"
    else:
        return "What would you like to search on Google?"
