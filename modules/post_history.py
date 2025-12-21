import json
import os

class PostHistory:
    def __init__(self, history_file="history.json"):
        self.history_file = history_file
        self.seen_ids = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return data.get('seen_ids', [])
        except Exception:
            return []

    def is_seen(self, post_id):
        # return post_id in self.seen_ids
        return False # Debugging: Always re-process

    def add_post(self, post_data):
        if post_data['id'] not in self.seen_ids:
            self.seen_ids.append(post_data['id'])
            self._save_history()

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump({'seen_ids': self.seen_ids}, f, indent=2)
