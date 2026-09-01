import os
import yaml
import logging
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("SEEZY")

class BuyingSession(QObject):
    # Signals emitted during session progression
    session_started = pyqtSignal(list)
    navigating_to_item = pyqtSignal(int, str, dict)
    detection_requested = pyqtSignal(int, str)
    item_completed = pyqtSignal(int, str)
    navigating_to_checkout = pyqtSignal(dict)
    session_finished = pyqtSignal()
    queue_completed = pyqtSignal()

    def __init__(self, config_path=None):
        super().__init__()
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "locations.yaml"
        )
        self.locations_config = self._load_locations()
        
        self.queue = []            
        self.current_item = None
        self.is_active = False

    def _load_locations(self):
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                logger.info("[BuyingSession] Loaded location configuration successfully.")
                return config
        except Exception as e:
            logger.error(f"[BuyingSession] Failed to load locations.yaml: {e}")
            return {"locations": {}, "checkout": {"name": "checkout", "x": 0.0, "y": 0.0, "theta": 0.0}}

    def add_item(self, item_id: int):
        if item_id not in self.locations_config.get("locations", {}):
            logger.warning(f"[BuyingSession] Item ID {item_id} not found in map locations.")
            return False

        if item_id in self.queue:
            logger.warning(f"[BuyingSession] Item ID {item_id} is already in the queue.")
            return False

        self.queue.append(item_id)
        item_name = self.locations_config["locations"][item_id]["name"]
        logger.info(f"[BuyingSession] Added item {item_id} ({item_name}) to queue.")
        return True

    def start_session(self):
        if not self.queue:
            return False

        self.is_active = True
        self.session_started.emit(self.queue)
        self._process_current_item()
        return True

    def _process_current_item(self):
        # If there are items left in the queue, process the first one
        if self.queue:
            item_id = self.queue[0]
            item_data = self.locations_config["locations"][item_id]
            self.current_item = item_data
            
            logger.info(f"[BuyingSession] Navigating to {item_data['name']}...")
            self.navigating_to_item.emit(item_id, item_data["name"], item_data)
        else:
            # Queue is fully empty. Do NOT force checkout. Return to open-ended state.
            logger.info("[BuyingSession] Queue finished. Awaiting next command.")
            self.queue_completed.emit()

    def on_navigation_arrived(self):
        if not self.is_active or not self.queue:
            return

        item_id = self.queue[0]
        item_name = self.current_item["name"]
        self.detection_requested.emit(item_id, item_name)

    def on_item_detected(self, item_id: int, success: bool, confidence: float = 0.0):
        if not self.is_active:
            return

        item_name = self.locations_config["locations"].get(item_id, {}).get("name", "Unknown")
        if success:
            # Logs the exact percentage confidence received from the controller
            logger.info(f"[BuyingSession] Confirmed item {item_id} ({item_name}) detected with {confidence * 100:.1f}% confidence.")
            self.item_completed.emit(item_id, item_name)

    def advance_queue(self):
        """Pops the active item permanently and moves to the next."""
        if not self.is_active or not self.queue: 
            return
            
        # Unconditionally erase the item from the queue
        self.queue.pop(0)
        
        # Advance to the next item in the list
        self._process_current_item()

    def navigate_checkout(self):
        checkout_data = self.locations_config.get("checkout", {"name": "checkout", "x": 0.0, "y": 0.0, "theta": 0.0})
        logger.info("[BuyingSession] Routing to Checkout Counter...")
        self.navigating_to_checkout.emit(checkout_data)

    def complete_checkout(self):
        logger.info("[BuyingSession] Reached Checkout Counter. Session complete.")
        self.is_active = False
        self.queue.clear()
        self.current_item = None
        self.session_finished.emit()