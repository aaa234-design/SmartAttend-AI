# SmartAttend-AI

Class 12 attendance management project using OpenCV LBPH face recognition, Streamlit, and SQLite.

## Features
- Teacher login (demo password: `admin123`; set `TEACHER_PASSWORD` before real use)
- Student registration with roll number, class, and section
- Webcam photo capture for face samples
- Train an LBPH face recognition model
- Configurable class periods and automatic/manual period selection
- Period-wise attendance with duplicate prevention
- Finalize a period to mark remaining students absent
- Attendance history and CSV export

## Run on Windows
1. Install Python 3.11 (64-bit recommended).
2. Run `setup.bat` and wait for installation.
3. Run `run.bat`.
4. Open the local Streamlit address shown in the terminal (usually `http://localhost:8501`).

## Important
This starter uses camera snapshots, not continuous CCTV streaming. Face recognition is not liveness detection. Face samples, database, and trained model are stored locally and excluded from Git.
