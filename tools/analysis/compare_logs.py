import sys

def compare_logs(file1, file2):
    print(f"Comparing {file1} and {file2}...")
    try:
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            
            min_len = min(len(lines1), len(lines2))
            print(f"comparing first {min_len} lines...")
            
            diffs = 0
            for i in range(min_len):
                l1 = lines1[i]
                l2 = lines2[i]
                
                # Strip timestamp (first 11 chars: "HH:MM:SS [")
                content1 = l1[11:].strip()
                content2 = l2[11:].strip()
                
                if content1 != content2:
                    print(f"DIFF at line {i+1}:")
                    print(f"< {l1.strip()}")
                    print(f"> {l2.strip()}")
                    diffs += 1
                    if diffs >= 5:
                        print("Stopping after 5 differences.")
                        break
            
            if diffs == 0:
                print(f"SUCCESS: Logs are identical up to line {min_len}")
            else:
                print(f"FAILURE: Found {diffs} differences.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        compare_logs(sys.argv[1], sys.argv[2])
    else:
        compare_logs("reports/logs/campaign_run6.log", "reports/logs/campaign.log")
