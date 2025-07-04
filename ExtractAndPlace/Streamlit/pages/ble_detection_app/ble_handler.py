"""BLE Handler for communicating with Arduino device."""

import asyncio
import threading
from bleak import BleakClient, BleakScanner
import time

from config import SERVICE_UUID, CHAR_UUID, ARDUINO_MAC, CLASS_ID


class BLEHandler:
    def __init__(self):
        # BLE configuration
        self.service_uuid = SERVICE_UUID
        self.char_uuid_data = CHAR_UUID  # pentru date S/T
        self.char_uuid_status = "19B10002-E8F2-537E-4F6C-D104768A1214"  # pentru notificări 0/1
        self.arduino_mac = ARDUINO_MAC
        
        # Global BLE state
        self.ble_loop = asyncio.new_event_loop()
        self.ble_client = None
        self.last_payload = None  # ultimul request primit
        self.arm_idle = True  # True când brațul e liber
        self.lock = threading.Lock()  # protecție acces last_payload
        
        # Start BLE thread
        self.start_ble_thread()
        
    def notification_handler(self, sender, data):
        """Callback pentru notificările de stare BLE (0=ready, 1=busy)."""
        if not data:
            return
        
        state = data[0]
        print(f"🔔 Status notification: {state}")
        
        if state == 0:  # Arm is ready
            with self.lock:
                self.arm_idle = True
                if self.last_payload:
                    payload = self.last_payload
                    self.last_payload = None
                    self.arm_idle = False
                else:
                    return
            
            print("▶ Arm ready – trimit payload stocat.")
            self.send_ble_async(payload)
    
    def disconnected_handler(self, client):
        """Callback la deconectare BLE: reconectează automat."""
        print("⚠ Disconnected – încerc reconectarea...")
        asyncio.run_coroutine_threadsafe(self.reconnect(), self.ble_loop)
    
    async def reconnect(self):
        """Corutină care încearcă reconectarea periodic."""
        while True:
            if self.ble_client and not self.ble_client.is_connected:
                try:
                    await self.ble_client.connect()
                    print("✔ Reconnected to BLE device.")
                    await self.ble_client.start_notify(self.char_uuid_status, self.notification_handler)
                    return
                except Exception as e:
                    print(f"⚠ Reconnect failed ({e}), retry in 5s...")
            await asyncio.sleep(5)
    
    def ble_thread_fn(self):
        """Thread care inițializează și rulează BLE loop."""
        asyncio.set_event_loop(self.ble_loop)
        
        try:
            device = self.ble_loop.run_until_complete(
                BleakScanner.find_device_by_address(self.arduino_mac, timeout=10.0)
            )
            
            if not device:
                print("❌ BLE device not found.")
                return
            
            self.ble_client = BleakClient(device, disconnected_callback=self.disconnected_handler)
            
            self.ble_loop.run_until_complete(self.ble_client.connect())
            print(f"✔ Connected to {device.address}")
            
            self.ble_loop.run_until_complete(
                self.ble_client.start_notify(self.char_uuid_status, self.notification_handler)
            )
            print(f"✔ Notifications enabled on {self.char_uuid_status}")
            
        except Exception as e:
            print(f"❌ BLE init error: {e}")
            return
        
        self.ble_loop.run_forever()
    
    def start_ble_thread(self):
        """Pornește thread-ul BLE."""
        threading.Thread(target=self.ble_thread_fn, daemon=True).start()
        print("🚀 BLE thread started")
    
    def send_ble_async(self, payload):
        """Trimite comenzile S și T serializat pe BLE; reset idle dacă nu sunt detecții."""
        if not self.ble_client or not self.ble_client.is_connected:
            print("⚠ BLE client nu e conectat.")
            return
        
        dets = payload.get('detections', [])
        if not dets:
            # Nu trimitem S/T, dar resetăm arm_idle pentru detectare nouă
            print("⚠ Fără detecții: resetez starea și permit noi detectări.")
            with self.lock:
                self.arm_idle = True
                self.last_payload = None
            return
        
        # 1) trimite S
        w, h = payload['crop_shape']
        s_msg = f"S {w} {h}"
        print(f"🔄 Sending: {s_msg}")
        
        fut1 = asyncio.run_coroutine_threadsafe(
            self.ble_client.write_gatt_char(self.char_uuid_data, s_msg.encode()), 
            self.ble_loop
        )
        
        try:
            fut1.result(timeout=5)
            print(f"✔ Sent: {s_msg}")
        except Exception as e:
            print(f"⚠ Failed S: {e}")
            with self.lock:
                self.last_payload = payload
            return
        
        # 2) trimite T
        best = max(dets, key=lambda d: d['confidence'])
        cx, cy = map(int, best['center_px'])
        obj_id = CLASS_ID.get(best['class'], 1)
        t_msg = f"T {cx} {cy} {obj_id}"
        print(f"🔄 Sending: {t_msg}")
        
        fut2 = asyncio.run_coroutine_threadsafe(
            self.ble_client.write_gatt_char(self.char_uuid_data, t_msg.encode()), 
            self.ble_loop
        )
        
        try:
            fut2.result(timeout=5)
            print(f"✔ Sent: {t_msg}")
        except Exception as e:
            print(f"⚠ Failed T: {e}")
            with self.lock:
                self.last_payload = payload
    
    async def send_data(self, data):
        """Public method pentru a trimite date (compatibilitate cu codul existent)."""
        with self.lock:
            if self.arm_idle:
                self.arm_idle = False
                threading.Thread(target=self.send_ble_async, args=(data,), daemon=True).start()
                return 'sent_immediately'
            else:
                self.last_payload = data
                return 'queued'
    
    def is_ready(self):
        """Verifică dacă brațul este gata de următoarea comandă."""
        with self.lock:
            return self.arm_idle
    
    def get_status(self):
        """Returnează statusul BLE handler-ului."""
        return {
            'connected': self.ble_client.is_connected if self.ble_client else False,
            'arm_idle': self.arm_idle,
            'has_queued_payload': self.last_payload is not None
        }
