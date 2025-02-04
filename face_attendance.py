import cv2
import face_recognition
import pickle
import base64
import numpy as np
from flask import jsonify
from datetime import datetime
from db import get_db_connection

def process_attendance(image_base64):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Decode base64 menjadi gambar
        img_data = base64.b64decode(image_base64)
        np_img = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Load data wajah dari database
        cursor.execute("SELECT id, name, NIS, face_encoding FROM users")
        users = cursor.fetchall()

        known_encodings = []
        known_names = []

        for user in users:
            user_id, name, nis, encoding = user
            known_encodings.append(pickle.loads(encoding))
            known_names.append((user_id, name, nis))

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                user_id, name, nis = known_names[best_match_index]
                hari_inggris = datetime.now().strftime("%A")
                hari_indonesia = konversi_hari_ke_indonesia(hari_inggris)
                waktu_absensi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                

                # Periksa apakah absensi dalam rentang waktu yang diperbolehkan
                if cek_jadwal_absensi():
                    cursor.execute("INSERT INTO attendance (user_id, hari, waktu_absensi) VALUES (%s, %s, %s)", 
                                   (user_id, hari_indonesia, waktu_absensi))
                    conn.commit()
                    return {"message": f"{name} berhasil absen pada {hari_indonesia}, {waktu_absensi}"}
                else:
                    return {"error": "Absensi di luar jam yang diperbolehkan"}
                
        return {"error": "Wajah tidak dikenali"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

def konversi_hari_ke_indonesia(hari_inggris):
    hari_indonesia = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }
    return hari_indonesia.get(hari_inggris, hari_inggris)

def cek_jadwal_absensi():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hari_sekarang = konversi_hari_ke_indonesia(datetime.now().strftime("%A"))
    waktu_sekarang = datetime.now().time()
    
    query = "SELECT jam_mulai, jam_selesai FROM jadwal_absensi WHERE hari = %s AND aktif = TRUE"
    cursor.execute(query, (hari_sekarang,))
    jadwal = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if jadwal:
        jam_mulai, jam_selesai = jadwal
        jam_mulai = datetime.strptime(str(jam_mulai), "%H:%M:%S").time()
        jam_selesai = datetime.strptime(str(jam_selesai), "%H:%M:%S").time()
        
        return jam_mulai <= waktu_sekarang <= jam_selesai
    
    return False