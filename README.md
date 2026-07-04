# BackupInsight Console

## Project Overview
BackupInsight Console is a Flask-based monitoring dashboard for backup jobs. It provides a responsive, modern UI with simulated real-time updates, SLA tracking, unresolved failure metrics, and interactive diagnostics.

## Purpose
The application is designed to help operators monitor backup activity, quickly identify failed jobs, and review estimated root causes with a conversational diagnostics assistant.

## Technologies Used
- Python 3
- Flask
- Jinja2 templates
- HTML / CSS / JavaScript
- python-docx

## Main Modules / Features
- `app.py` - backend application logic, route handling, job data simulation, refresh API, and chatbot diagnostic responses
- `templates/dashboard.html` - dashboard UI, live job table, responsive layout, interactive failure modal, and chat assistant
- `static/style.css` - modern glassmorphism styling, 3D-inspired cards, mobile responsiveness, and table layout
- `generate_report.py` - generates a Word document report summarizing project details

## Dataset / Source
The project uses a mock in-memory dataset of backup jobs. Job status, runtime, throughput, and stage values are simulated and refreshed programmatically to mimic a live monitoring dashboard.

## Implementation Flow
1. Load mock job definitions from the Flask backend.
2. Hydrate each job with runtime, throughput, and SLA values.
3. Render the dashboard with metric cards and a detailed job table.
4. Poll the backend for refreshed job data at intervals.
5. Display failure diagnostics and chat guidance for jobs that require attention.
6. Generate a Word project report using `generate_report.py` when needed.

## Running the Project
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python app.py
   ```
3. Open the dashboard in your browser at:
   ```
   http://127.0.0.1:5000
   ```

## Notes
- The job data is simulated, so this project is best used as a dashboard prototype.
- For production, replace the mock dataset with a real backup data source and persistent storage.

## Report Generation
Run `python generate_report.py` to create `BackupInsight_Project_Report.docx` containing a project summary and architecture details.
