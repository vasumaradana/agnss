import requests

def test_fetch():
    # Try fetching a known file from the past (e.g., Jan 1st 2024)
    # Year: 2024, DOY: 001
    # File: brdc0010.24n.gz
    
    url = "https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2024/001/brdc0010.24n.gz"
    print(f"Testing fetch from: {url}")
    
    try:
        resp = requests.get(url, stream=True, timeout=10)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS: Connection to IGS server works and file exists.")
            print(f"Content Length: {resp.headers.get('content-length')} bytes")
        else:
            print("FAILURE: Could not download file.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_fetch()
