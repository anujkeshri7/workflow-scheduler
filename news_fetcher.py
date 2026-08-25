import urllib.request
import json
import xml.etree.ElementTree as ET
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_rss(url, source_name, limit=3):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"\n=== {source_name} ===")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Atom or RSS check
            items = root.findall('.//item')
            if not items:
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
            count = 0
            for item in items:
                if count >= limit: break
                title = item.find('title')
                if title is None:
                    title = item.find('{http://www.w3.org/2005/Atom}title')
                
                title_text = title.text.strip() if title is not None and title.text else "No Title"
                print(f"- {title_text}")
                count += 1
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")

def fetch_reddit(subreddit, limit=3):
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={limit}&t=day"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"\n=== Reddit (r/{subreddit}) ===")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read())
            for child in data['data']['children']:
                title = child['data']['title']
                print(f"- {title}")
    except Exception as e:
        print(f"Error fetching reddit: {e}")

print("Fetching latest news...\n")

# PIB India
fetch_rss("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=15&Regid=24", "PIB India")

# Reuters
fetch_rss("https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&hl=en-US&gl=US&ceid=US:en", "Reuters")

# Associated Press
fetch_rss("https://news.google.com/rss/search?q=when:24h+allinurl:apnews.com&hl=en-US&gl=US&ceid=US:en", "Associated Press")

# PTI & ANI News
fetch_rss("https://news.google.com/rss/search?q=when:24h+(allinurl:ptinews.com+OR+allinurl:aninews.in)&hl=en-IN&gl=IN&ceid=IN:en", "PTI & ANI News")

# ViralHog (YouTube RSS)
fetch_rss("https://www.youtube.com/feeds/videos.xml?channel_id=UCt7x5I8HMB39B_Y32A_zCvw", "ViralHog (YouTube)")

# Reddit
fetch_reddit("news", 3)
fetch_reddit("indepthstories", 3)

print("\nDone fetching.")
