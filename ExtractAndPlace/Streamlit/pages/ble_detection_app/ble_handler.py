"""BLE communication handler for Arduino communication."""

import asyncio
from bleak import BleakClient, BleakScanner
from config import SERVICE_UUID, CHAR_UUID, ARDUINO_MAC, CLASS_ID


class BLEHandler:
    def __init__(self):
        self.arduino_mac = ARDUINO_MAC
        self.char_uuid = CHAR_UUID
        self.class_id = CLASS_ID

    async def send_data(self, payload):
        """Send detection data to Arduino via BLE."""
        device = await BleakScanner.find_device_by_address(self.arduino_mac, timeout=10.0)
        if not device:
            print("❌ Arduino BLE not found.")
            return False

        try:
            async with BleakClient(device) as client:
                print(f"✔ Connected to {device.address}")
                
                # Send crop shape
                await self._send_crop_shape(client, payload)
                
                # Send highest-confidence detection
                await self._send_detection(client, payload)
                
                return True
        except Exception as e:
            print(f"❌ BLE Error: {e}")
            return False

    async def _send_crop_shape(self, client, payload):
        """Send crop shape information."""
        w, h = payload['crop_shape']
        s_msg = f"S {w} {h}"
        await client.write_gatt_char(self.char_uuid, s_msg.encode())
        print(f"▶ Sent BLE: {s_msg}")

    async def _send_detection(self, client, payload):
        """Send detection information."""
        dets = payload.get('detections', [])
        if dets:
            best = max(dets, key=lambda d: d['confidence'])
            cx, cy = map(int, best['center_px'])
            obj_id = self.class_id.get(best['class'], 1)
            t_msg = f"T {cx} {cy} {obj_id}"
            await client.write_gatt_char(self.char_uuid, t_msg.encode())
            print(f"▶ Sent BLE: {t_msg}")
        else:
            print("⚠ No detections to send.")


