import cv2
import face_recognition
import pickle
import base64
import numpy as np
import mysql.connector
from db import get_db_connection

def is_face_registered(new_face_encoding):
    """Cek apakah wajah sudah ada di database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, nis, face_encoding FROM users")
    users = cursor.fetchall()

    for user in users:
        name, nis, stored_face_blob = user
        stored_face_encoding = pickle.loads(stored_face_blob)

        # Bandingkan dengan wajah yang baru diambil
        matches = face_recognition.compare_faces([stored_face_encoding], new_face_encoding)
        if True in matches:
            return name  # Wajah ditemukan
    
    return None  # Wajah belum terdaftar

def register_face(name, nis, mapel, image_base64):
    """Registrasi wajah dengan gambar dari Base64"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Decode base64 menjadi gambar OpenCV
        img_data = base64.b64decode(image_base64)
        np_img = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Gambar tidak valid"}

        # Deteksi wajah di gambar
        face_locations = face_recognition.face_locations(frame)
        if not face_locations:
            return {"error": "Wajah tidak terdeteksi"}

        # Ambil encoding wajah
        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

        # Cek apakah wajah sudah terdaftar
        existing_user = is_face_registered(face_encoding)
        if existing_user:
            return {"error": f"Wajah sudah terdaftar sebagai {existing_user}."}

        # Simpan encoding ke database
        encoded_face = pickle.dumps(face_encoding)
        cursor.execute(
            "INSERT INTO users (name, NIS, mapel, face_encoding) VALUES (%s, %s, %s, %s)", 
            (name, nis, mapel, mysql.connector.Binary(encoded_face))
        )
        conn.commit()
        return {"message": f"Wajah {name} berhasil diregistrasi!"}

    except Exception as e:
        return {"error": f"Terjadi kesalahan: {str(e)}"}
    
    finally:
        cursor.close()
        conn.close()
