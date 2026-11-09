import os
from datetime import date, datetime, time
import pandas as pd
import streamlit as st
from database import (init_db,add_student,get_students,add_period,get_periods,get_active_period,
                      mark_attendance,finalize_period,get_attendance,get_student_attendance_summary)
from face_recognition import train_model,recognize_image,save_student_face

st.set_page_config(page_title="SmartAttend AI",page_icon="📚",layout="wide")
init_db()
def login():
    if st.session_state.get("authenticated"): return True
    st.title("🔐 Teacher Login")
    st.caption("Demo password: admin123 — set TEACHER_PASSWORD environment variable before real use.")
    pwd=st.text_input("Teacher password",type="password")
    if st.button("Login",type="primary"):
        if pwd==os.getenv("TEACHER_PASSWORD","admin123"):
            st.session_state.authenticated=True; st.rerun()
        else: st.error("Incorrect password.")
    return False
if not login(): st.stop()
with st.sidebar:
    st.title("📚 SmartAttend AI")
    page=st.radio("Navigation",["Dashboard","Register Student","Train Face Model","Manage Timetable","Mark Attendance","Attendance Records"])
    if st.button("Logout"): st.session_state.authenticated=False; st.rerun()
st.title(page)

if page=="Dashboard":
    students=get_students(); records=get_attendance(date.today())
    present=sum(r["status"]=="Present" for r in records)
    a,b,c=st.columns(3); a.metric("Registered students",len(students)); b.metric("Present today",present); c.metric("Not yet marked",max(0,len(students)-present))
    st.subheader("Today's attendance")
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True) if records else st.info("No attendance recorded today.")
elif page=="Register Student":
    with st.form("student"):
        a,b=st.columns(2); name=a.text_input("Student full name"); roll=b.text_input("Roll number")
        c,d=st.columns(2); cls=c.text_input("Class / grade", "12"); section=d.text_input("Section","A")
        save=st.form_submit_button("Save student",type="primary")
    if save:
        try: st.success(f"Student saved. ID: {add_student(name.strip(),roll.strip(),cls.strip(),section.strip())}") if name.strip() and roll.strip() else st.error("Name and roll number required.")
        except Exception as e: st.error(str(e))
    students=get_students()
    if students:
        st.subheader("Capture face samples")
        labels={f'{s["roll_number"]} — {s["name"]}':s["id"] for s in students}
        chosen=st.selectbox("Select student",list(labels))
        photo=st.camera_input("Take a clear front-facing photo")
        if photo and st.button("Save face sample",type="primary"):
            ok,msg=save_student_face(labels[chosen],photo.getvalue()); (st.success if ok else st.error)(msg)
        st.caption("Capture 5–10 clear photos per student with slightly different angles and lighting. Images remain local.")
elif page=="Train Face Model":
    st.write("Train the OpenCV LBPH recognizer using locally saved face samples.")
    if st.button("Train / Update model",type="primary"):
        with st.spinner("Training..."): ok,msg=train_model()
        (st.success if ok else st.error)(msg)
elif page=="Manage Timetable":
    with st.form("period"):
        a,b,c=st.columns(3); cls=a.text_input("Class / section","12-A"); name=b.text_input("Period name","Period 1")
        start=c.time_input("Start time",time(8,0)); end=a.time_input("End time",time(8,45)); active=b.checkbox("Active",True)
        submit=st.form_submit_button("Add period",type="primary")
    if submit:
        if end<=start: st.error("End time must be later than start time.")
        else: add_period(cls.strip(),name.strip(),start.strftime("%H:%M"),end.strftime("%H:%M"),active); st.success("Period added.")
    st.subheader("Configured periods"); periods=get_periods()
    st.dataframe(pd.DataFrame(periods),use_container_width=True,hide_index=True) if periods else st.info("No periods configured.")
elif page=="Mark Attendance":
    periods=get_periods(active_only=True)
    if not periods: st.warning("Add at least one active period first."); st.stop()
    classes=sorted({p["class_name"] for p in periods}); cls=st.selectbox("Class / section",classes)
    class_periods=[p for p in periods if p["class_name"]==cls]
    active=get_active_period(cls,datetime.now().strftime("%H:%M"))
    mode=st.radio("Period selection",["Automatic suggestion","Manual selection"],horizontal=True)
    if mode=="Automatic suggestion" and active:
        chosen=active; st.success(f'Current period: {active["period_name"]} ({active["start_time"]}–{active["end_time"]})')
    else:
        if mode=="Automatic suggestion": st.info("No period matches current time; choose manually.")
        chosen=st.selectbox("Choose period",class_periods,format_func=lambda p:f'{p["period_name"]} ({p["start_time"]}–{p["end_time"]})')
    photo=st.camera_input("Capture attendance photo")
    if photo and st.button("Recognize and mark attendance",type="primary"):
        result=recognize_image(photo.getvalue())
        if result is None: st.error("Train the face model first.")
        elif result.get("student_id") is None: st.warning("Face not recognized.")
        else:
            ok,msg=mark_attendance(result["student_id"],cls,chosen["id"],datetime.now().isoformat(timespec="seconds"))
            (st.success if ok else st.warning)(f'{result["name"]} ({result["roll_number"]}) — {msg}')
    if st.button("Finalize this period (mark remaining students absent)",type="secondary"):
        n=finalize_period(cls,chosen["id"],date.today().isoformat()); st.success(f"Period finalized. {n} absent record(s) added.")
    st.caption("This starter uses camera snapshots, not continuous CCTV streaming.")
elif page=="Attendance Records":
    a,b=st.columns(2); day=a.date_input("Attendance date",date.today())
    students=get_students(); options={"All students":None}; options.update({f'{s["roll_number"]} — {s["name"]}':s["id"] for s in students})
    selected=b.selectbox("Student filter",list(options))
    records=get_attendance(day,options[selected])
    if records:
        df=pd.DataFrame(records); st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Download CSV report",df.to_csv(index=False).encode("utf-8"),f"attendance-{day}.csv","text/csv")
    else: st.info("No matching attendance records.")
    st.subheader("Student attendance summary")
    summary=get_student_attendance_summary(options[selected])
    if summary: st.dataframe(pd.DataFrame(summary),use_container_width=True,hide_index=True)
