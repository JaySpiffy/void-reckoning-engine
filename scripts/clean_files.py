import os

def clean_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'rb') as f:
        content = f.read()
    
    # Remove null bytes
    cleaned = content.replace(b'\x00', b'')
    
    with open(path, 'wb') as f:
        f.write(cleaned)
    print(f"Cleaned {path}")

clean_file('src/reporting/dashboard/services/dashboard_service.py')
clean_file('src/reporting/static/dashboard.js')
