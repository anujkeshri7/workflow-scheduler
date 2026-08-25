import sys
from playwright.sync_api import sync_playwright

def capture_screenshot(url, output_path, selector=None):
    print(f"Opening browser to screenshot: {url}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to URL
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if selector:
                # Wait for the specific element (e.g. an image tag) and capture it
                element = page.wait_for_selector(selector, timeout=15000)
                element.screenshot(path=output_path)
                print(f"Element screenshot ({selector}) successfully saved to {output_path}")
            else:
                # Take screenshot of the loaded page viewport
                page.screenshot(path=output_path)
                print(f"Screenshot successfully saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python screenshot_downloader.py <URL> <output_path> [css_selector]")
        sys.exit(1)
    
    target_url = sys.argv[1]
    out_file = sys.argv[2]
    sel = sys.argv[3] if len(sys.argv) > 3 else None
    capture_screenshot(target_url, out_file, sel)
