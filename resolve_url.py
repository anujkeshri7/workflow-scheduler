import sys
import requests

def resolve(url):
    if not url.startswith("http"):
        return url
    try:
        # Try HEAD request first for speed
        r = requests.head(url, allow_redirects=True, timeout=10)
        return r.url
    except Exception:
        try:
            # Fallback to GET
            r = requests.get(url, allow_redirects=True, timeout=10)
            return r.url
        except Exception as e:
            print(f"Error resolving {url}: {e}", file=sys.stderr)
            return url

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(resolve(sys.argv[1]))
