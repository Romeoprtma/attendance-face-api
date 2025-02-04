from flask import Flask, request, jsonify
from face_registration import register_face
from face_attendance import process_attendance
from jadwal import cek_jadwal_absensi, update_jadwal, add_jadwal
import os
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"success": "berhasil terhubung ke API"}), 200

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    nis = data.get("nis")
    mapel = data.get("mapel")
    image_base64 = data.get("image")  # Base64 dari Flutter

    if not all([name, nis, mapel, image_base64]):
        return jsonify({"error": "Data tidak lengkap"}), 400

    result = register_face(name, nis, mapel, image_base64)
    return jsonify(result)

@app.route("/absensi", methods=["POST"])
def absensi():
    data = request.json
    image = data.get("image")  # Base64 dari Flutter

    if not image:
        return jsonify({"error": "Gambar tidak dikirim"}), 400

    result = process_attendance(image)
    return jsonify(result)

@app.route("/jadwal", methods=["GET"])
def jadwal():
    jadwal = cek_jadwal_absensi()
    return jadwal

@app.route("/jadwal/<int:id>", methods=["PUT"])
def update_jadwal_route(id):
    response = update_jadwal(id)
    return response

@app.route("/jadwal", methods=["POST"])
def add_jadwal_route():
    response = add_jadwal()
    return response

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Gunakan PORT dari environment variable
    app.run(host='127.0.0.1', port=port, debug=True)

