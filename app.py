import os
import random
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, abort, request

app = Flask(__name__)

# 1. Your Mock Database Array containing the cross-platform backup jobs
JOBS_DATABASE = [
    {
        "job_id": "JOB-110",
        "client_target": "Cloud-Archive",
        "backup_engine": "Rubrik",
        "data_handled_gb": 248.2,
        "sla_status": "Failed",
        "execution_time_utc": "2026-07-04 06:48:00",
        "error_code": "STORAGE-QUOTA-EXCEEDED",
        "error_message": "Destination storage quota exceeded while writing incremental segments."
    },
    {
        "job_id": "JOB-109",
        "client_target": "DevOps-Pipeline",
        "backup_engine": "Veeam",
        "data_handled_gb": 60.3,
        "sla_status": "Success",
        "execution_time_utc": "2026-07-04 06:00:00"
    },
    {
        "job_id": "JOB-108",
        "client_target": "Finance-Warehouse",
        "backup_engine": "Veritas",
        "data_handled_gb": 900.0,
        "sla_status": "Failed",
        "execution_time_utc": "2026-07-04 05:25:00",
        "error_code": "PERMISSION-DENIED",
        "error_message": "Backup agent could not access target files due to missing permissions."
    },
    {
        "job_id": "JOB-107",
        "client_target": "Marketing-Analytics",
        "backup_engine": "NetBackup",
        "data_handled_gb": 135.7,
        "sla_status": "Success",
        "execution_time_utc": "2026-07-04 05:00:00"
    },
    {
        "job_id": "JOB-106",
        "client_target": "Backup-Test-Lab",
        "backup_engine": "Azure-VM",
        "data_handled_gb": 18.5,
        "sla_status": "Failed",
        "execution_time_utc": "2026-07-04 04:10:00",
        "error_code": "AUTH-401",
        "error_message": "Credentials expired for the target backup client."
    },
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
        "execution_time_utc": "2026-07-04 03:15:00",
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

ERROR_GUIDANCE = {
    "0x2000001a": {
        "cause": "Network timeout during the data transfer pipeline initialization.",
        "resolution": "Validate MediaAgent network connectivity, firewall settings, and host reachability. Restart the backup service and rerun the job after restoring connectivity."
    },
    "vmextensionprovisioningerror": {
        "cause": "Azure VM backup extension failed to provision on the target virtual machine.",
        "resolution": "Check the Azure VM agent health, snapshot extension status, and VM resource availability. Reinstall or upgrade the extension if necessary, then retry the job."
    },
    "auth-401": {
        "cause": "Target credentials are expired or rejected by the backup service.",
        "resolution": "Rotate the service account credentials, verify their validity in the backup policy, and update the target configuration before retrying."
    },
    "storage-quota-exceeded": {
        "cause": "The backup target repository has exceeded available storage capacity.",
        "resolution": "Delete stale backups, expand the target repository quota, or move backups to an alternate storage location and rerun the job."
    },
    "permission-denied": {
        "cause": "The backup agent lacks the required file system permissions to read source data.",
        "resolution": "Grant the backup service account read access to the source directories and verify access using the same credentials before rerunning the backup."
    },
    "network-timeout": {
        "cause": "Network latency or packet loss is interrupting backup traffic.",
        "resolution": "Inspect NIC statistics, switch and router logs, and any WAN accelerator paths. Stabilize network throughput, then re-run the backup."
    },
    "snapshot-failure": {
        "cause": "The storage snapshot or VSS provider did not complete successfully.",
        "resolution": "Verify the snapshot provider, check disk IO pressure, and ensure no conflicting snapshot jobs are running. Restart the provider service and retry."
    },
    "disk-full": {
        "cause": "The backup target disk is full or near capacity.",
        "resolution": "Free up space on the repository, archive old snapshots, or extend the backup volume before restarting the failed job."
    },
    "dns-failure": {
        "cause": "The backup agent cannot resolve the target host name.",
        "resolution": "Check DNS records, host file entries, and name resolution from the backup server. Use the IP address temporarily if DNS is incorrect."
    }
}

GENERIC_FAILURE_KB = {
    "network": "Network issues are among the most common backup causes. Validate firewall rules, latency, packet loss, and routing between source and target systems. Use dedicated backup VLANs or QoS if possible.",
    "storage": "Insufficient storage space often causes backup failures. Review repository usage, delete outdated snapshots, and consider storage tiering or expanding the target volume.",
    "permission": "Permissions are critical. Ensure the backup service account has read access to the source files and write access to the target repository. Check for NTFS, ACL, or UNIX permission mismatches.",
    "credentials": "Expired or invalid credentials will stop backups immediately. Rotate backup credentials regularly, and verify the account has the required privileges before retrying.",
    "snapshot": "Snapshot failures usually indicate problems with the snapshot provider, VM agent, or disk I/O. Check the provider logs, ensure the VM is healthy, and retry the snapshot job separately.",
    "agent": "Agent health is important. Confirm the backup agent service is running, up to date, and can communicate with the central server. Restart or reinstall the agent if it reports errors.",
    "timeout": "Timeouts often point to overloaded infrastructure or network congestion. Reduce the backup window, run smaller incremental jobs, or move heavy jobs to a less busy timeframe.",
    "quota": "Repository quota issues are solved by reclaiming space, extending the storage pool, or redirecting backups to a secondary target. Monitor storage growth and prune old backups proactively.",
    "ssl": "SSL or certificate issues can block connections. Verify the certificate chain, trust store configuration, and expiration dates on both ends of the backup path.",
    "policy": "Backup policies must match the data and recovery objectives. Review retention, schedules, and target selection, then align them with your SLA requirements."
}

FAQ_REFERENCE = {
    "failure": "Backup failures are usually caused by network interruptions, target storage issues, expired credentials, or permission problems. Ask a specific job ID for exact diagnostics.",
    "resolution": "The most reliable fix is to identify the root cause from the error code, validate connectivity and credentials, then rerun the failed job after correcting the problem.",
    "job": "A failed job includes an error code and message. Ask about the specific job ID and the backup bot will provide the most likely cause and remediation steps.",
    "real world": "I can provide real backup best practices based on industry knowledge. For live internet-sourced articles, you would connect this app to a search or knowledge API."
}

@app.route('/api/chat', methods=['POST'])
def chat_bot():
    request_data = request.get_json(silent=True) or {}
    question = request_data.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please ask a question about backup failures, causes, or resolution."})
    answer = answer_backup_question(question)
    return jsonify({"answer": answer})


def answer_backup_question(question):
    text = question.lower()

    if any(term in text for term in ["internet", "online", "web", "google", "search", "article", "live", "vendor", "knowledge base"]):
        internet_answer = internet_search_snippet(question)
        if internet_answer:
            return internet_answer
        return ("I currently draw on a built-in backup knowledge base with real-world troubleshooting guidance. "
                "For live vendor KB pages, connect this app to a search or AI knowledge API.")

    for job in JOBS_DATABASE:
        if job["job_id"].lower() in text:
            if job["sla_status"] == "Failed":
                code = job.get("error_code", "UNKNOWN")
                guidance = ERROR_GUIDANCE.get(code.lower())
                if guidance:
                    engine_note = ''
                    if job.get("backup_engine"):
                        engine_note = f" This failure is on {job['backup_engine']}, so validate the agent and repository settings for that platform."
                    return (f"{job['job_id']} failed with error code {code}. Cause: {guidance['cause']} "
                            f"Resolution: {guidance['resolution']}{engine_note}")
                return (f"{job['job_id']} failed with error code {code}. "
                        f"Message: {job.get('error_message', 'No additional details available.')}. "
                        "Check the agent logs, network connectivity, and storage target health.")
            return (f"{job['job_id']} completed successfully. No active failure is currently recorded for this job. "
                    "If you need help with past failures, ask for the error code or backup details.")

    for keyword, guidance in GENERIC_FAILURE_KB.items():
        if keyword in text:
            return guidance

    if any(term in text for term in ["cause", "why", "reason", "failed", "failure"]):
        for key, answer in FAQ_REFERENCE.items():
            if key in text:
                return answer
        return FAQ_REFERENCE["failure"]

    if any(term in text for term in ["resolve", "fix", "solution", "repair", "recover"]):
        return FAQ_REFERENCE["resolution"]

    if any(term in text for term in ["sla", "success rate"]):
        payload = build_dashboard_payload()
        return f"Current SLA success rate is {payload['sla_value']}% with {payload['unresolved_failures']} unresolved failures."

    if any(term in text for term in ["backup best", "best practice", "recommendation", "advice"]):
        return ("For real-world backup reliability, use strong retention policies, monitor target capacity, keep agents up to date, "
                "validate credentials before windows, and avoid storing backups on the same physical infrastructure as the source.")

    return ("I can help with backup failures, root causes, resolutions, and job-specific error details. "
            "Ask about a job ID, an error code, or a specific failure symptom like network, quota, or permissions.")


def internet_search_snippet(question):
    try:
        query = urllib.parse.quote(question)
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&skip_disambig=1"
        with urllib.request.urlopen(url, timeout=8) as response:
            body = response.read().decode('utf-8')
        data = json.loads(body)
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            return f"Internet summary: {abstract}"
        related = data.get("RelatedTopics", [])
        if isinstance(related, list):
            for item in related:
                if isinstance(item, dict):
                    text = item.get("Text", "").strip()
                    if text:
                        return f"Internet summary: {text}"
        return None
    except Exception:
        return None


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
        },
        {
            "error_code": "STORAGE-QUOTA-EXCEEDED",
            "error_message": "Target repository storage quota was exceeded while writing backup increments."
        },
        {
            "error_code": "PERMISSION-DENIED",
            "error_message": "Backup agent was denied access to source data due to permissions."
        }
    ]

    jobs_to_update = random.sample(JOBS_DATABASE, k=max(1, min(3, len(JOBS_DATABASE))))
    for job in jobs_to_update:
        if job["sla_status"] == "Success":
            job["sla_status"] = "Failed"
            failure = random.choice(failure_reasons)
            job["error_code"] = failure["error_code"]
            job["error_message"] = failure["error_message"]
        else:
            job["sla_status"] = "Success"
            job.pop("error_code", None)
            job.pop("error_message", None)
        job["execution_time_utc"] = (datetime.utcnow() - timedelta(minutes=random.randint(1, 120))).strftime("%Y-%m-%d %H:%M:%S")

    for job in JOBS_DATABASE:
        if job not in jobs_to_update and random.random() < 0.35:
            job["execution_time_utc"] = (datetime.utcnow() - timedelta(minutes=random.randint(5, 90))).strftime("%Y-%m-%d %H:%M:%S")

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