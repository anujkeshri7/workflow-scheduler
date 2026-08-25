import json
import os

history_file = ".sent_posts_history.json"
data_file = "daily_news_data.json"

# Remove history entries for current daily_news_data items if any exist
if os.path.exists(history_file):
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # Clear out prior keys that might block sending news1, news2, news3 of this batch
        keys_to_remove = []
        for k, v in history.items():
            if v.get("image") in ["news1_final.png", "news2_final.png", "news3_final.png"]:
                keys_to_remove.append(k)
        
        for k in keys_to_remove:
            del history[k]
            
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        print(f"Cleared {len(keys_to_remove)} history keys to ensure fresh delivery of requested posts.")
    except Exception as e:
        print(f"Warning: {e}")
