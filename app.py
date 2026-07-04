import os
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, abort

app = Flask(__name__)

# 1. Your Mock Database Array containing the cross-platform backup jobs
JOBS_DATABASE = [
    {
        "job_id": "JOB-105",
        "client_target": "Bausch-Health-DR",
        "backup_engine": "Commvault",
        "data_handled_gb": 310.0,
        "sla_status": "Failed",
        "execution_time_utc": "2026-07-04 06:12:00",
        "error_code": "0x2000001a",
        "error_message": "MediaAgent side network connection timeout during data transfer pipeline initialization."
    },
    {
        "job_id": "JOB-104",
        "client_target": "Mail-Server-Arch",
        "backup_engine": "Veeam",
        "data_handled_gb": 85.2,
        "sla_status": "Success",
        "execution_time_utc": "2026-07-04 05:00:00"
    },
    {
        "job_id": "JOB-103",
        "client_target": "Finance-DB-Cluster",
        "backup_engine": "Cohesity",
        "data_handled_gb": 1200.0,
        "sla_status": "Success",
        "execution_time_utc": "2026-07-04 04:30:00"
    },
    {
        "job_id": "JOB-102",
        "client_target": "Bausch-Health-QA",
        "backup_engine": "Azure-VM",
        "data_handled_gb": 120.0,
        "sla_status": "Failed",
        "error_code": "VMExtensionProvisioningError",
        "error_message": "Microsoft.Azure.RecoveryServices.VMSnapshot extension failed to provision. Ensure the VM agent is responsive."
    },
    {
        "job_id": "JOB-101",
        "client_target": "Bausch-Health-Prod",
        "backup_engine": "Commvault",
        "data_handled_gb": 450.5,
        "sla_status": "Success",
        "execution_time_utc": "2026-07-04 02:00:00"
    }
]

# 2. Home Page Dashboard Route
@app.route('/')
def dashboard_home():
    total_jobs = len(JOBS_DATABASE)
    successful_jobs = sum(1 for j in JOBS_DATABASE if j["sla_status"] == "Success")
    unresolved_failures = sum(1 for j in JOBS_DATABASE if j["sla_status"] == "Failed")
    
    # Calculate live SLA Success Rate Percentage
    sla_value = round((successful_jobs / total_jobs) * 100, 1) if total_jobs > 0 else 100.0
    total_tb = round(sum(j["data_handled_gb"] for j in JOBS_DATABASE) / 1024, 2)

    return render_template('dashboard.html', 
                           jobs=JOBS_DATABASE, 
                           sla_value=sla_value, 
                           unresolved_failures=unresolved_failures,
                           total_tb=total_tb)

# 3. API Route to fetch the current dashboard state
@app.route('/api/jobs')
def get_jobs():
    return jsonify(build_dashboard_payload())

# 4. API Route to refresh the current job statuses dynamically
@app.route('/api/jobs/refresh')
def refresh_jobs():
    simulate_job_updates()
    payload = build_dashboard_payload()
    payload['refreshed_at'] = datetime.utcnow().isoformat() + 'Z'
    return jsonify(payload)

# 5. API Route to Fetch a single job's error details
@app.route('/api/job/<job_id>')
def get_job_details(job_id):
    job = next((j for j in JOBS_DATABASE if j["job_id"] == job_id), None)
    if job:
        return jsonify(job)
    return jsonify({"error": "Job not found"}), 404

def build_dashboard_payload():
    total_jobs = len(JOBS_DATABASE)
    successful_jobs = sum(1 for j in JOBS_DATABASE if j["sla_status"] == "Success")
    unresolved_failures = sum(1 for j in JOBS_DATABASE if j["sla_status"] == "Failed")
    sla_value = round((successful_jobs / total_jobs) * 100, 1) if total_jobs > 0 else 100.0
    total_tb = round(sum(j["data_handled_gb"] for j in JOBS_DATABASE) / 1024, 2)

    return {
        "jobs": JOBS_DATABASE,
        "sla_value": sla_value,
        "unresolved_failures": unresolved_failures,
        "total_tb": total_tb,
        "total_jobs": total_jobs
    }

def simulate_job_updates():
    failure_reasons = [
        {
            "error_code": "0x2000001a",
            "error_message": "Network packet timeout prevented the backup stream from establishing."
        },
        {
            "error_code": "VMExtensionProvisioningError",
            "error_message": "VM agent extension failed during snapshot preparation."
        },
        {
            "error_code": "AUTH-401",
            "error_message": "Credentials expired for the target backup client."
        }
    ]

    for job in JOBS_DATABASE:
        if random.random() < 0.22:
            if job["sla_status"] == "Success":
                job["sla_status"] = "Failed"
                failure = random.choice(failure_reasons)
                job["error_code"] = failure["error_code"]
                job["error_message"] = failure["error_message"]
            else:
                job["sla_status"] = "Success"
                job.pop("error_code", None)
                job.pop("error_message", None)
        if random.random() < 0.15:
            job["execution_time_utc"] = (datetime.utcnow() - timedelta(minutes=random.randint(1, 120))).strftime("%Y-%m-%d %H:%M:%S")

# 4. API Route to process the "Retry Backup" trigger action
@app.route('/api/job/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    job = next((j for j in JOBS_DATABASE if j["job_id"] == job_id), None)
    if job:
        job["sla_status"] = "Success"
        if "error_code" in job: del job["error_code"]
        if "error_message" in job: del job["error_message"]
        return jsonify({"status": "success", "message": f"Retry command processed for {job_id}!"})
    return jsonify({"error": "Job not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)