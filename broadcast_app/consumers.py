import cv2
import numpy as np
import base64
import json
import torch
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
import asyncio

# Load YOLO model with hardware acceleration
model = YOLO('yolov8s.pt')  # Smaller model for faster inference
if torch.cuda.is_available():
    model.to('cuda')

class FrameBroadcastConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['roomId']
        self.group_name = f"broadcast_{self.room_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()  
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            frame_data = data.get("frame")
            
            if frame_data:
                # Frame skipping logic (process 1 of every 2 frames)
                if not hasattr(self, 'frame_counter'):
                    self.frame_counter = 0
                self.frame_counter += 1
                if self.frame_counter % 2 != 0:
                    return

                # Process frame in thread pool
                loop = asyncio.get_event_loop()
                processed = await loop.run_in_executor(
                    None, 
                    self.process_frame, 
                    frame_data
                )
                
                if processed:
                    annotated_frame, empty, persons = processed
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "broadcast_frame",
                            "frame": annotated_frame,
                            "empty": empty,
                            "persons": persons
                        }
                    )
        except Exception as e:
            print("WebSocket receive error:", e)

    async def broadcast_frame(self, event):
        await self.send(text_data=json.dumps({
            "frame": event["frame"],
            "empty": event["empty"],
            "persons": event["persons"]
        }))

    def calculate_iou(boxA, boxB):
        xA1, yA1, xA2, yA2 = boxA
        xB1, yB1, xB2, yB2 = boxB

        xI1 = max(xA1, xB1)
        yI1 = max(yA1, yB1)
        xI2 = min(xA2, xB2)
        yI2 = min(yA2, yB2)

        inter_width = max(0, xI2 - xI1)
        inter_height = max(0, yI2 - yI1)

        inter_area = inter_width * inter_height

        boxA_area = max(0, xA2 - xA1) * max(0, yA2 - yA1)
        boxB_area = max(0, xB2 - xB1) * max(0, yB2 - yB1)

        union_area = boxA_area + boxB_area - inter_area
        if union_area == 0:
            return 0.0

        iou = inter_area / union_area
        return iou
    
    def process_frame(self, frame_data):
        try:
            # Decode base64 image
            header, data = frame_data.split(",", 1)
            image_bytes = base64.b64decode(data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Optimized YOLO inference
            results = model(
                frame, 
                imgsz=320, 
                conf=0.5, 
                half=torch.cuda.is_available(),  # FP16 if CUDA available
                device='cuda' if torch.cuda.is_available() else 'cpu'
            )

            # Process detections
            person_boxes = []
            chair_boxes = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    if cls_id == 0:  # Person
                        person_boxes.append((x1, y1, x2, y2))
                    elif cls_id == 56:  # Chair
                        chair_boxes.append((x1, y1, x2, y2))

            # Calculate occupancy
            empty_count = 0
            for (x1, y1, x2, y2) in chair_boxes:
                occupied = any(
                    self.calculate_iou((x1, y1, x2, y2), person) >= 0.2
                    for person in person_boxes
                )
                if not occupied:
                    empty_count += 1
                color = (0, 255, 0) if not occupied else (0, 0, 255)
                thickness = 6 if not occupied else 13
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(frame, "Empty" if not occupied else "Occupied", 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

            # Draw person boxes
            for (x1, y1, x2, y2) in person_boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255,0,255), 2)

            # Add statistics
            cv2.putText(frame, f"Empty: {empty_count}", (25, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
            cv2.putText(frame, f"People: {len(person_boxes)}", (25, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)

            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            jpg_b64 = base64.b64encode(buffer).decode('utf-8')
            
            return (
                f"data:image/jpeg;base64,{jpg_b64}",
                empty_count,
                len(person_boxes)
            )
        except Exception as e:
            print("Frame processing error:", e)
            return None