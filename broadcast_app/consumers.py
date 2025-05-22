import time, base64, asyncio, json, threading
import cv2, numpy as np, torch
from ultralytics import YOLO
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from concurrent.futures import ThreadPoolExecutor
from django.apps import apps
from django.utils import timezone


Broadcast = apps.get_model('broadcast_app', 'Broadcast')

# Load YOLO once
model = YOLO('yolov8s.pt')
if torch.cuda.is_available():
    model.to('cuda').fuse()

executor = ThreadPoolExecutor(max_workers=2)

class FrameBroadcastConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['roomId']
        
        qs = self.scope.get('query_string', b'').decode()  
        params = dict(pair.split('=') for pair in qs.split('&') if '=' in pair)
        self.role = params.get('role', 'viewer')           # default to viewer

        # join group
        self.group = f"broadcast_{self.room_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        self.counter = 0
        
        self._stop_event = threading.Event()

    @database_sync_to_async
    def _mark_broadcast_stopped(self):
        try:
            b = Broadcast.objects.get(id=self.room_id)
            b.is_live    = False
            b.save(update_fields=['is_live'])
        except Broadcast.DoesNotExist:
            pass
        
    async def disconnect(self, code):
        # print('get disconnected .............')
        self._stop_event.set()
        
        if self.role == 'broadcaster':
            await self._mark_broadcast_stopped()

        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        self.counter += 1
        if self.counter % 1 != 0:
            return

        raw = bytes_data
        sep = raw.find(b'\x00')
        header = json.loads(raw[:sep].decode())
        ts_send = header.get("ts_send")
        img_bytes = raw[sep+1:]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, self.process_frame, img_bytes)
        if not result:
            return
        frame_b64, empty, persons = result

        await self.channel_layer.group_send(
            self.group,
            {
                "type": "broadcast_frame",
                "frame": frame_b64,
                "empty": empty,
                "persons": persons,
                "ts_send": ts_send,
            }
        )

    async def broadcast_frame(self, event):
        ts_server = time.time() * 1000
        await self.send(text_data=json.dumps({
            "frame": event["frame"],
            "empty": event["empty"],
            "persons": event["persons"],
            "ts_send": event["ts_send"],
            "ts_server": ts_server,
        }))

    def process_frame(self, img_bytes):
        if getattr(self, "_stop_event", None) and self._stop_event.is_set():
            return None
    
        t0 = time.time()
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        t1 = time.time()

        small = cv2.resize(img, (320, 320))
        t2 = time.time()

        results = model(small, conf=0.5, device='cuda' if torch.cuda.is_available() else 'cpu')
        t3 = time.time()

        persons, chairs = [], []
        for r in results:
            for b in r.boxes:
                cls = int(b.cls[0])
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                (chairs if cls == 56 else persons).append((x1, y1, x2, y2))

        empty = 0
        for c in chairs:
            occ = any(self.iou(c, p) >= 0.2 for p in persons)
            empty += not occ
            color = (0, 255, 0) if not occ else (0, 0, 255)
            cv2.rectangle(img, (c[0], c[1]), (c[2], c[3]), color, 2)
        for p in persons:
            cv2.rectangle(img, (p[0], p[1]), (p[2], p[3]), (255, 0, 255), 2)

        cv2.putText(img, f"E:{empty}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img, f"P:{len(persons)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        t4 = time.time()

        _, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        frame_b64 = base64.b64encode(buf).decode('utf-8')
        t5 = time.time()

        print(f"[Frame timing] total={(t5-t0)*1000:.1f}ms | "
              f"decode={(t1-t0)*1000:.1f} | resize={(t2-t1)*1000:.1f} | "
              f"infer={(t3-t2)*1000:.1f} | post={(t4-t3)*1000:.1f} | encode={(t5-t4)*1000:.1f}")
        return f"data:image/jpeg;base64,{frame_b64}", empty, len(persons)

    @staticmethod
    def iou(a, b):
        xA1, yA1, xA2, yA2 = a
        xB1, yB1, xB2, yB2 = b
        xi1, yi1 = max(xA1, xB1), max(yA1, yB1)
        xi2, yi2 = min(xA2, xB2), min(yA2, yB2)
        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        union = ((xA2 - xA1) * (yA2 - yA1) +
                 (xB2 - xB1) * (yB2 - yB1) - inter)
        return inter / union if union else 0.0
