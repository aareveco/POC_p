import subprocess
import os
import json
from typing import Dict, List, Optional

class AppManager:
    def __init__(self):
        self.apps: Dict[str, dict] = {}
        self.load_apps()
    
    def load_apps(self):
        """Load saved apps from configuration file"""
        try:
            with open('apps_config.json', 'r') as f:
                self.apps = json.load(f)
        except FileNotFoundError:
            self.apps = {}
    
    def save_apps(self):
        """Save apps configuration to file"""
        with open('apps_config.json', 'w') as f:
            json.dump(self.apps, f, indent=4)
    
    def add_app(self, app_name: str, app_type: str, config: dict) -> bool:
        """Add a new app to the manager"""
        if app_name in self.apps:
            return False
        
        self.apps[app_name] = {
            'type': app_type,
            'config': config,
            'status': 'inactive'
        }
        self.save_apps()
        return True
    
    def remove_app(self, app_name: str) -> bool:
        """Remove an app from the manager"""
        if app_name not in self.apps:
            return False
        
        del self.apps[app_name]
        self.save_apps()
        return True
    
    def launch_teamviewer(self, connection_id: str) -> bool:
        """Launch TeamViewer with specific connection ID"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(['teamviewer.exe', '-i', connection_id])
            else:  # Linux/MacOS
                subprocess.Popen(['teamviewer', '-i', connection_id])
            return True
        except Exception as e:
            print(f"Error launching TeamViewer: {e}")
            return False
    
    def launch_obs(self, stream_key: str) -> bool:
        """Launch OBS Studio with streaming configuration"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(['obs64.exe', '--stream', stream_key])
            else:  # Linux/MacOS
                subprocess.Popen(['obs', '--stream', stream_key])
            return True
        except Exception as e:
            print(f"Error launching OBS: {e}")
            return False
    
    def get_app_list(self) -> List[str]:
        """Get list of all managed apps"""
        return list(self.apps.keys())
    
    def get_app_status(self, app_name: str) -> Optional[str]:
        """Get status of a specific app"""
        return self.apps.get(app_name, {}).get('status') 