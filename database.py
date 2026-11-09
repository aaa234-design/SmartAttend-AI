import sqlite3
from pathlib import Path
from datetime import date
DB=Path("data/attendance.db")
DB.parent.mkdir(parents=True,exist_ok=True)
def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, name TEXT NOT NULL, roll_number TEXT UNIQUE NOT NULL, class_name TEXT NOT NULL, section TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS periods(id INTEGER PRIMARY KEY, class_name TEXT NOT NULL, period_name TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, class_name TEXT NOT NULL, period_id INTEGER NOT NULL, attendance_date TEXT NOT NULL, status TEXT NOT NULL, marked_at TEXT NOT NULL, UNIQUE(student_id,attendance_date,period_id));
        """)
def add_student(name,roll,class_name,section):
    with connect() as c:
        cur=c.execute("INSERT INTO students(name,roll_number,class_name,section) VALUES(?,?,?,?)",(name,roll,class_name,section)); return cur.lastrowid
def get_students():
    with connect() as c: return [dict(x) for x in c.execute("SELECT * FROM students ORDER BY roll_number")]
def add_period(class_name,name,start,end,active=True):
    with connect() as c: c.execute("INSERT INTO periods(class_name,period_name,start_time,end_time,active) VALUES(?,?,?,?,?)",(class_name,name,start,end,int(active)))
def get_periods(active_only=False):
    q="SELECT * FROM periods"+(" WHERE active=1" if active_only else "")+" ORDER BY class_name,start_time"
    with connect() as c: return [dict(x) for x in c.execute(q)]
def get_active_period(class_name,now):
    with connect() as c:
        r=c.execute("SELECT * FROM periods WHERE class_name=? AND active=1 AND start_time<=? AND end_time>? ORDER BY start_time LIMIT 1",(class_name,now,now)).fetchone()
        return dict(r) if r else None
def mark_attendance(student_id,class_name,period_id,marked_at):
    d=marked_at[:10]
    with connect() as c:
        try: c.execute("INSERT INTO attendance(student_id,class_name,period_id,attendance_date,status,marked_at) VALUES(?,?,?,?,?,?)",(student_id,class_name,period_id,d,"Present",marked_at)); return True,"Present marked."
        except sqlite3.IntegrityError: return False,"Attendance already recorded for this student and period."
def finalize_period(class_name,period_id,day):
    with connect() as c:
        grade,sep,section=class_name.partition("-")
        sql="SELECT id FROM students WHERE class_name=?"+(" AND section=?" if sep else "")
        args=(grade,section) if sep else (class_name,)
        students=c.execute(sql,args).fetchall(); n=0
        for s in students:
            cur=c.execute("INSERT OR IGNORE INTO attendance(student_id,class_name,period_id,attendance_date,status,marked_at) VALUES(?,?,?,?,?,?)",(s["id"],class_name,period_id,day,"Absent",day+" 23:59:59")); n+=cur.rowcount
        return n
def get_attendance(attendance_date=None,student_id=None):
    q="""SELECT a.id,s.name,s.roll_number,s.class_name AS student_class,a.class_name,p.period_name,a.attendance_date,a.status,a.marked_at FROM attendance a JOIN students s ON s.id=a.student_id JOIN periods p ON p.id=a.period_id WHERE 1=1"""
    args=[]
    if attendance_date: q+=" AND a.attendance_date=?"; args.append(str(attendance_date))
    if student_id: q+=" AND a.student_id=?"; args.append(student_id)
    q+=" ORDER BY a.marked_at DESC"
    with connect() as c: return [dict(x) for x in c.execute(q,args)]
def get_student_attendance_summary(student_id=None):
    q="""SELECT s.roll_number,s.name,a.class_name,COUNT(*) total_periods,SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present_periods,SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) absent_periods FROM attendance a JOIN students s ON s.id=a.student_id"""
    args=[]
    if student_id: q+=" WHERE s.id=?"; args.append(student_id)
    q+=" GROUP BY s.id,a.class_name ORDER BY s.roll_number"
    with connect() as c: return [dict(x) for x in c.execute(q,args)]
