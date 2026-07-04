from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('backups.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM backup_jobs ORDER BY timestamp DESC')
    jobs = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM backup_jobs')
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM backup_jobs WHERE status="Success"')
    success_jobs = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(size_gb) FROM backup_jobs')
    total_data_gb = cursor.fetchone()[0] or 0
    
    conn.close()
    
    failed_jobs = total_jobs - success_jobs
    success_rate = (success_jobs / total_jobs) * 100 if total_jobs > 0 else 0
    total_data_tb = total_data_gb / 1024
    
    return render_template('dashboard.html', 
                           jobs=jobs, 
                           total=total_jobs, 
                           success_rate=round(success_rate, 1),
                           failed=failed_jobs,
                           total_data=round(total_data_tb, 2))

if __name__ == '__main__':
    app.run(debug=True)