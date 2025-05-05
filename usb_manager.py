import usb.core
import usb.util
import threading
import time
from typing import Dict, List, Optional

class USBManager:
    def __init__(self):
        self.devices: Dict[int, usb.core.Device] = {}
        self.streaming_threads: Dict[int, threading.Thread] = {}
        self.running = False
    
    def find_devices(self) -> List[Dict]:
        """Find all available USB devices"""
        devices = []
        for device in usb.core.find(find_all=True):
            try:
                device_info = {
                    'id': device.idVendor,
                    'manufacturer': usb.util.get_string(device, device.iManufacturer),
                    'product': usb.util.get_string(device, device.iProduct),
                    'device': device
                }
                devices.append(device_info)
            except:
                continue
        return devices
    
    def start_streaming(self, device_id: int, callback) -> bool:
        """Start streaming data from a USB device"""
        if device_id in self.streaming_threads:
            return False
        
        device = self.devices.get(device_id)
        if not device:
            return False
        
        self.running = True
        thread = threading.Thread(
            target=self._stream_data,
            args=(device, callback)
        )
        self.streaming_threads[device_id] = thread
        thread.start()
        return True
    
    def stop_streaming(self, device_id: int) -> bool:
        """Stop streaming from a USB device"""
        if device_id not in self.streaming_threads:
            return False
        
        self.running = False
        self.streaming_threads[device_id].join()
        del self.streaming_threads[device_id]
        return True
    
    def _stream_data(self, device: usb.core.Device, callback):
        """Internal method to stream data from USB device"""
        try:
            # Configure device
            device.set_configuration()
            endpoint = device[0][(0,0)][0]
            
            while self.running:
                try:
                    data = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
                    callback(data)
                except usb.core.USBError as e:
                    if e.args == ('Operation timed out',):
                        continue
                    break
                time.sleep(0.001)  # Small delay to prevent CPU overuse
                
        except Exception as e:
            print(f"Error streaming USB data: {e}")
        finally:
            self.running = False
    
    def get_device_info(self, device_id: int) -> Optional[Dict]:
        """Get information about a specific USB device"""
        device = self.devices.get(device_id)
        if not device:
            return None
        
        return {
            'id': device.idVendor,
            'manufacturer': usb.util.get_string(device, device.iManufacturer),
            'product': usb.util.get_string(device, device.iProduct),
            'is_streaming': device_id in self.streaming_threads
        } 