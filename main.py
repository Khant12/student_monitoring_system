import datetime
import os
import cv2
import face_recognition
import numpy as np
import requests
import time
import pandas as pd
import serial
from flask import Flask, render_template, Response, jsonify, request, send_file

app = Flask(__name__)
ser = serial.Serial('COM9', 9600)  # change the serial port connect from your Arduino Uno


class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_current_frame = True
    image_folder = 'unknown_faces'
    students_data = pd.read_csv('user_info.csv', encoding='ISO-8859-1')

    currentRecognizedName = 'N/A'
    currentBatchName = 'N/A'
    currentTimetable = 'N/A'

    MATCH_THRESHOLD = 0.6

    def __init__(self):
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('faces'):
            face_image = face_recognition.load_image_file(f'faces/{image}')
            face_encoding = face_recognition.face_encodings(face_image)[0]

            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(os.path.splitext(image)[0])

    def get_student_info(self, name):
        student_info = self.students_data[self.students_data['Name'] == name]
        if not student_info.empty:
            return {
                'BatchName': student_info['BatchName'].values[0],
                'TimeTable': student_info['TimeTable'].values[0]
            }
        else:
            return {'BatchName': 'N/A', 'TimeTable': 'N/A'}

    def generate_frames(self):
        esp32_cam_url = 'http://192.168.22.8/cam-mid.jpg'

        frame_skip_counter = 0

        while True:
            try:
                response = requests.get(esp32_cam_url)
                frame = cv2.imdecode(np.array(bytearray(response.content), dtype=np.uint8), -1)
            except Exception as e:
                print(f"Error retrieving frame from ESP32-CAM: {e}")
                continue

            frame_skip_counter = (frame_skip_counter + 1) % 3
            if frame_skip_counter == 0:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

                self.face_names = []
                person_detected = False

                for (top, right, bottom, left), face_encoding in zip(self.face_locations, self.face_encodings):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.4)
                    name = 'Unknown'

                    if any(matches):
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index] and face_distances[best_match_index] < self.MATCH_THRESHOLD:
                            name = self.known_face_names[best_match_index]

                            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"{current_time}: {name}")

                            if name != 'Unknown':
                                student_info = self.get_student_info(name)
                                print(f"Batch Name: {student_info['BatchName']}, TimeTable: {student_info['TimeTable']}")

                                self.currentRecognizedName = name
                                self.currentBatchName = student_info['BatchName']
                                self.currentTimetable = student_info['TimeTable']

                                ser.write(b'0')
                                print("Sending signal '0' to turn on green LED.")

                                cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4), (0, 0, 128), 2)
                                cv2.rectangle(frame, (left * 4, bottom * 4 - 35), (right * 4, bottom * 4), (0, 0, 128),
                                              cv2.FILLED)
                                font = cv2.FONT_HERSHEY_DUPLEX
                                cv2.putText(frame, name, (left * 4 + 6, bottom * 4 - 6), font, 0.5, (255, 255, 255), 1)

                                person_detected = True
                                # Inside the generate_frames method
                                for (top, right, bottom, left), face_encoding in zip(self.face_locations,
                                                                                     self.face_encodings):
                                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding,
                                                                             tolerance=0.4)
                                    name = 'Unknown'

                                    if any(matches):
                                        face_distances = face_recognition.face_distance(self.known_face_encodings,
                                                                                        face_encoding)
                                        best_match_index = np.argmin(face_distances)

                                        if matches[best_match_index] and face_distances[
                                            best_match_index] < self.MATCH_THRESHOLD:
                                            name = self.known_face_names[best_match_index]

                                            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            print(f"{current_time}: {name}")

                                            if name != 'Unknown':
                                                student_info = self.get_student_info(name)
                                                print(
                                                    f"Batch Name: {student_info['BatchName']}, TimeTable: {student_info['TimeTable']}")

                                                # Set the values for the added attributes
                                                self.currentRecognizedName = name
                                                self.currentBatchName = student_info['BatchName']
                                                self.currentTimetable = student_info['TimeTable']

                                                # Draw a rectangle around the face with dark blue color
                                                cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4),
                                                              (0, 0, 128), 2)

                                                # Draw the label below the face
                                                cv2.rectangle(frame, (left * 4, bottom * 4 - 35),
                                                              (right * 4, bottom * 4), (0, 0, 128), cv2.FILLED)
                                                font = cv2.FONT_HERSHEY_DUPLEX
                                                cv2.putText(frame, name, (left * 4 + 6, bottom * 4 - 6), font, 0.5,
                                                            (255, 255, 255), 1)

                # If the name is 'Unknown', set the values for the added attributes
                    if name == 'Unknown':
                        self.currentRecognizedName = name
                        self.currentBatchName = 'no record'
                        self.currentTimetable = 'no record'

                        person_detected = True
                        print("Sending signal '1' to turn on red LED.")

                        ser.write(b'1')

                        cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4), (0, 0, 255), 2)
                        cv2.rectangle(frame, (left * 4, bottom * 4 - 35), (right * 4, bottom * 4), (0, 0, 255),
                                  cv2.FILLED)
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(frame, name, (left * 4 + 6, bottom * 4 - 6), font, 0.5, (255, 255, 255), 1)
                        self.save_unknown_person_image(frame)

                if not person_detected:
                    print("No person detected. Sending signal '2' to turn off LED.")
                    ser.write(b'2')

            ret, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    def save_unknown_person_image(self, frame):  # it will save the photo if there was an unknown person detected.
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        image_filename = f"{self.image_folder}/unknown_person_{timestamp}.jpg"
        cv2.imwrite(image_filename, frame)
        print(f"Unknown person image saved: {image_filename}")


fr = FaceRecognition()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(fr.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_user_image')
def get_user_image():
    user_name = request.args.get('name')

    if user_name == 'N/A':
        return jsonify({'error': 'User image not available.'}), 404

    image_path = f'faces/{user_name}.jpg'  # Assuming images are named after the user

    if not os.path.exists(image_path):
        return jsonify({'error': 'User image not found.'}), 404

    return send_file(image_path, mimetype='image/jpeg')


@app.route('/get_recognized_info')
def get_recognized_info():
    time.sleep(1)
    return jsonify({'name': fr.currentRecognizedName,
                    'info': {'batchName': fr.currentBatchName, 'timetable': fr.currentTimetable}})


@app.route('/capture_photo')
def capture_photo():
    try:
        # Retrieve a frame from the camera feed
        response = requests.get('http://192.168.22.8/cam-mid.jpg')
        frame = cv2.imdecode(np.array(bytearray(response.content), dtype=np.uint8), -1)

        # Save the captured frame to the 'captures' folder
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        capture_filename = f'captures/captured_photo_{timestamp}.jpg'
        cv2.imwrite(capture_filename, frame)

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error capturing photo: {e}")
        return jsonify({'success': False})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
