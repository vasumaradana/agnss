import requests

def check_year_dir(year):
    url = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/{year}/"
    print(f"Checking: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"SUCCESS: Directory for {year} exists.")
        else:
            print(f"FAILURE: Directory for {year} does not exist (Status {resp.status_code}).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_year_dir(2024)
    check_year_dir(2025)
