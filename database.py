import sqlite3

def init_db():
    conn = sqlite3.connect('backups.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_jobs (
            id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            size_gb REAL NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    mock_data = [
        ("JOB-101", "Bausch-Health-Prod", "Commvault", 450.5, "Success", "2026-07-04 02:00:00"),
        ("JOB-102", "Bausch-Health-QA", "Azure-VM", 120.0, "Failed", "2026-07-04 03:15:00"),
        ("JOB-103", "Finance-DB-Cluster", "Cohesity", 1200.0, "Success", "2026-07-04 04:30:00"),
        ("JOB-104", "Mail-Server-Arch", "Veeam", 85.2, "Success", "2026-07-04 05:00:00"),
        ("JOB-105", "Bausch-Health-DR", "Commvault", 310.0, "Failed", "2026-07-04 06:12:00")
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO backup_jobs VALUES (?, ?, ?, ?, ?, ?)', mock_data)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with mock data.")