#!/usr/bin/env python3
"""
Webcam viewer with MediaPipe hand tracking and gesture recognition
Integrates with Ableton Live for gesture-based control
Press 'q' to quit
"""

import cv2
import sys
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math
import socket
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GestureControl")

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

def is_finger_extended(landmarks, finger_tip_idx, finger_pip_idx, wrist_idx):
    """Check if a finger is extended by comparing tip position to pip joint"""
    tip = landmarks[finger_tip_idx]
    pip = landmarks[finger_pip_idx]
    wrist = landmarks[wrist_idx]
    
    # Distance from wrist to tip vs wrist to pip
    tip_dist = calculate_distance(wrist, tip)
    pip_dist = calculate_distance(wrist, pip)
    
    return tip_dist > pip_dist * 1.1

def recognize_gesture(hand_landmarks):
    """Recognize common hand gestures based on landmark positions"""
    if not hand_landmarks:
        return "None"
    
    # Landmark indices
    WRIST = 0
    THUMB_TIP = 4
    THUMB_IP = 3
    INDEX_TIP = 8
    INDEX_PIP = 6
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    RING_TIP = 16
    RING_PIP = 14
    PINKY_TIP = 20
    PINKY_PIP = 18
    
    # Check which fingers are extended
    thumb_extended = hand_landmarks[THUMB_TIP].x < hand_landmarks[THUMB_IP].x - 0.05
    index_extended = is_finger_extended(hand_landmarks, INDEX_TIP, INDEX_PIP, WRIST)
    middle_extended = is_finger_extended(hand_landmarks, MIDDLE_TIP, MIDDLE_PIP, WRIST)
    ring_extended = is_finger_extended(hand_landmarks, RING_TIP, RING_PIP, WRIST)
    pinky_extended = is_finger_extended(hand_landmarks, PINKY_TIP, PINKY_PIP, WRIST)
    
    # Count extended fingers
    extended_count = sum([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended])
    
    # Gesture recognition logic
    if extended_count == 0:
        return "Fist"
    
    elif extended_count == 5:
        return "Open Hand"
    
    elif index_extended and middle_extended and not ring_extended and not pinky_extended and not thumb_extended:
        return "Peace Sign"
    
    elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
        return "Pointing"
    
    elif thumb_extended and not index_extended and not middle_extended and not ring_extended and not pinky_extended:
        return "Thumbs Up"
          
    elif index_extended and pinky_extended and not middle_extended and not ring_extended:
        return "Rock On"
    
    elif extended_count == 1:
        return f"One Finger ({extended_count})"
    
    elif extended_count == 2:
        return f"Two Fingers ({extended_count})"
    
    elif extended_count == 3:
        return f"Three Fingers ({extended_count})"
    
    elif extended_count == 4:
        return f"Four Fingers ({extended_count})"
    
    return "Unknown"

class AbletonController:
    """Simple Ableton Live controller using socket connection"""
    
    def __init__(self, host="localhost", port=9877):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
    
    def connect(self):
        """Connect to Ableton Remote Script"""
        if self.connected:
            return True
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to Ableton: {e}")
            self.sock = None
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Ableton"""
        if self.sock:
            try:
                self.sock.close()
                logger.info("Disconnected from Ableton")
            except:
                pass
            finally:
                self.sock = None
                self.connected = False
    
    def send_command(self, command_type, params=None):
        """Send a command to Ableton"""
        if not self.connected:
            if not self.connect():
                return False
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            
            # Try to receive response (non-blocking)
            try:
                self.sock.settimeout(0.5)
                response_data = self.sock.recv(8192)
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get("status") == "error":
                    logger.error(f"Ableton error: {response.get('message')}")
                    return False
                
                return True
            except socket.timeout:
                # No response received, but command was sent
                return True
        except Exception as e:
            logger.error(f"Error sending command to Ableton: {e}")
            self.connected = False
            self.sock = None
            return False
    
    def start_playback(self):
        """Start Ableton playback"""
        logger.info("Starting Ableton playback")
        return self.send_command("start_playback")
    
    def stop_playback(self):
        """Stop Ableton playback"""
        logger.info("Stopping Ableton playback")
        return self.send_command("stop_playback")

def main():
    """Open webcam and display video feed with hand tracking"""
    print("=== Webcam Viewer with Hand Tracking & Gesture Recognition ===")
    print("=== Ableton Gesture Control ===")
    print("Pointing = Start Playback")
    print("Fist = Stop Playback")
    print("Press 'q' to quit\n")
    print("Opening webcam...")
    
    # Initialize Ableton controller
    ableton = AbletonController()
    print("Connecting to Ableton...")
    if ableton.connect():
        print("Connected to Ableton Live!")
    else:
        print("WARNING: Could not connect to Ableton. Make sure Ableton is running with the Remote Script.")
        print("Gesture detection will still work, but Ableton control will be disabled.\n")
    
    # Open the default camera (0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return 1
    
    print("Webcam opened successfully!")
    print("Press 'q' to quit")
    
    # Hand landmark connections for drawing
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        (5, 9), (9, 13), (13, 17)  # Palm
    ]
    
    # Get the path to the model file
    model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
    
    # Configure hand landmarker options
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        running_mode=vision.RunningMode.VIDEO
    )
    
    try:
        detector = vision.HandLandmarker.create_from_options(options)
        
        frame_count = 0
        last_gesture = None
        last_action = None  # Track last action to avoid repeated commands
        
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to grab frame")
                break
            
            # Flip the frame horizontally for a mirror view
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB and create MediaPipe Image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Process the frame with timestamp
            frame_count += 1
            results = detector.detect_for_video(mp_image, frame_count)
            
            # Draw hand landmarks and recognize gestures
            gestures = []
            if results.hand_landmarks:
                h, w, _ = frame.shape
                
                for idx, hand_landmarks in enumerate(results.hand_landmarks):
                    # Recognize gesture for this hand
                    gesture = recognize_gesture(hand_landmarks)
                    gestures.append(gesture)
                    
                    # Print gesture to console when it changes
                    if gesture != last_gesture:
                        hand_label = results.handedness[idx][0].category_name if results.handedness else "Hand"
                        print(f"{hand_label}: {gesture}")
                        
                        # Trigger Ableton actions based on gestures
                        if gesture == "Pointing" and last_action != "start":
                            if ableton.start_playback():
                                last_action = "start"
                                print("  -> Started Ableton playback")
                        
                        elif gesture == "Fist" and last_action != "stop":
                            if ableton.stop_playback():
                                last_action = "stop"
                                print("  -> Stopped Ableton playback")
                        
                        last_gesture = gesture
                    
                    # Draw landmarks as circles
                    for landmark in hand_landmarks:
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                    
                    # Draw connections
                    for connection in HAND_CONNECTIONS:
                        start_idx, end_idx = connection
                        start = hand_landmarks[start_idx]
                        end = hand_landmarks[end_idx]
                        
                        start_point = (int(start.x * w), int(start.y * h))
                        end_point = (int(end.x * w), int(end.y * h))
                        
                        cv2.line(frame, start_point, end_point, (255, 0, 0), 2)
                
                # Display number of hands and gestures detected
                num_hands = len(results.hand_landmarks)
                y_offset = 30
                cv2.putText(
                    frame,
                    f'Hands detected: {num_hands}',
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )
                
                # Display gestures on screen
                for idx, gesture in enumerate(gestures):
                    y_offset += 35
                    hand_label = results.handedness[idx][0].category_name if results.handedness else f"Hand {idx+1}"
                    
                    # Highlight active gestures
                    color = (255, 255, 0)  # Yellow default
                    if gesture == "Pointing":
                        color = (0, 255, 0)  # Green for start
                    elif gesture == "Fist":
                        color = (0, 0, 255)  # Red for stop
                    
                    cv2.putText(
                        frame,
                        f'{hand_label}: {gesture}',
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                        cv2.LINE_AA
                    )
                
                # Display Ableton status
                if ableton.connected:
                    status_text = "Ableton: Connected"
                    if last_action == "start":
                        status_text += " (Playing)"
                    elif last_action == "stop":
                        status_text += " (Stopped)"
                    
                    cv2.putText(
                        frame,
                        status_text,
                        (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                        cv2.LINE_AA
                    )
            else:
                last_gesture = None
            
            # Display the resulting frame
            cv2.imshow('Hand Tracking', frame)
            
            # Wait for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nQuitting...")
                break
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect from Ableton
        ableton.disconnect()
        
        # Release the camera and close windows
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam closed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
