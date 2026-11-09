import io
from pathlib import Path
import cv2, numpy as np
from PIL import Image
from database import get_students
FACE_DIR=Path("data/students"); MODEL_DIR=Path("models")
MODEL=MODEL_DIR/"lbph_model.yml"
LABELS=MODEL_DIR/"labels.txt"
CASCADE=cv2.data.haarcascades+"haarcascade_frontalface_default.xml"
def detector():
    d=cv2.CascadeClassifier(CASCADE)
    if d.empty(): raise RuntimeError("OpenCV face detector could not load")
    return d
def save_student_face(student_id,image_bytes):
    try:
        img=Image.open(io.BytesIO(image_bytes)).convert("RGB")
        gray=cv2.cvtColor(np.array(img),cv2.COLOR_RGB2GRAY)
        faces=detector().detectMultiScale(gray,1.2,5,minSize=(80,80))
        if not len(faces): return False,"No face detected; try a brighter front-facing photo."
        x,y,w,h=max(faces,key=lambda f:f[2]*f[3]); crop=cv2.resize(gray[y:y+h,x:x+w],(200,200))
        folder=FACE_DIR/str(student_id); folder.mkdir(parents=True,exist_ok=True)
        idx=len(list(folder.glob("*.png")))+1; cv2.imwrite(str(folder/f"face_{idx:03}.png"),crop)
        return True,f"Face sample saved. Total samples: {idx}"
    except Exception as e: return False,str(e)
def train_model():
    if not hasattr(cv2,"face"): return False,"Install opencv-contrib-python (not opencv-python)."
    faces=[]; labels=[]; label_map={}
    for s in get_students():
        paths=list((FACE_DIR/str(s["id"])).glob("*.png"))
        if paths: label_map[str(s["id"])]=s["id"]
        for p in paths:
            img=cv2.imread(str(p),cv2.IMREAD_GRAYSCALE)
            if img is not None: faces.append(cv2.resize(img,(200,200))); labels.append(s["id"])
    if len(faces)<2: return False,"Capture at least two face samples first."
    rec=cv2.face.LBPHFaceRecognizer_create(); rec.train(faces,np.array(labels,dtype=np.int32))
    MODEL_DIR.mkdir(exist_ok=True); rec.write(str(MODEL)); LABELS.write_text("\n".join(label_map),encoding="utf-8")
    return True,f"Model trained with {len(faces)} samples."
def recognize_image(image_bytes,threshold=65.0):
    if not MODEL.exists() or not hasattr(cv2,"face"): return None
    img=Image.open(io.BytesIO(image_bytes)).convert("RGB")
    gray=cv2.cvtColor(np.array(img),cv2.COLOR_RGB2GRAY)
    faces=detector().detectMultiScale(gray,1.2,5,minSize=(80,80))
    if not len(faces): return {"student_id":None,"message":"No face detected"}
    x,y,w,h=max(faces,key=lambda f:f[2]*f[3]); crop=cv2.resize(gray[y:y+h,x:x+w],(200,200))
    rec=cv2.face.LBPHFaceRecognizer_create(); rec.read(str(MODEL)); label,dist=rec.predict(crop)
    if dist>threshold: return {"student_id":None,"confidence":float(dist)}
    student=next((s for s in get_students() if s["id"]==int(label)),None)
    if not student: return None
    return {"student_id":student["id"],"name":student["name"],"roll_number":student["roll_number"],"confidence":float(dist)}
