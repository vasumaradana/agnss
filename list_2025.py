import requests
from html.parser import HTMLParser

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.links.append(attr[1])

def list_2025_files():
    # Try to list files in the first day of 2025 to see if *any* data exists
    url = "https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2025/001/"
    print(f"Checking listing for: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            parser = SimpleHTMLParser()
            parser.feed(resp.text)
            files = [l for l in parser.links if l.endswith('.gz')]
            print(f"Found {len(files)} .gz files.")
            if files:
                print(f"Example: {files[0]}")
        else:
            print("Could not list directory.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_2025_files()
