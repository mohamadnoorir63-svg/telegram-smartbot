import requests
from bs4 import BeautifulSoup

BASE_URL = "https://gergahn.com/search?q="  # فرضی، باید لینک واقعی جایگزین شود

def search_music(query):
    url = BASE_URL + query.replace(" ", "+")
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    for item in soup.select(".song-item"):  # کلاس فرضی، با HTML واقعی جایگزین شود
        title = item.select_one(".song-title").text
        link = item.select_one("a.download-link")["href"]
        results.append({"title": title, "link": link})
    return results
