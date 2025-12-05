import rinex_parser
import os

def test_local():
    file_path = "debug_file.rnx.gz"
    if not os.path.exists(file_path):
        print("Debug file not found. Run debug_parser.py first.")
        return

    print(f"Testing parser on {file_path}...")
    data = rinex_parser.parse_rinex_nav(file_path)
    print(f"Parsed {len(data)} records.")
    if data:
        print("First record:", data[0])

if __name__ == "__main__":
    test_local()
