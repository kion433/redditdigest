import requests
import random
import html

class RedditClient:
    def __init__(self, subreddits=None):
        self.subreddits = subreddits or ["confession", "AmItheAsshole", "tifu", "AskReddit"]
        self.default_subreddit = "confession" # Default fallback
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def get_top_posts(self, subreddit=None, time_filter="day", limit=25, sort="best"):
        """
        Fetches a list of posts, sorted by 'best', 'hot', 'top', or 'controversial'.
        """
        if not subreddit:
            subreddit = random.choice(self.subreddits)
        
        # Determine the endpoint based on sort strategy
        if sort == "best":
            # 'best' is usually for home feed, for subreddits 'hot' is default 'best' equivalent or 'top'
            # Reddit API structure: /r/{sub}/{sort}.json
            endpoint = "hot" 
        elif sort == "controversial":
            endpoint = "controversial"
            time_filter = "day" # Controversial typically needs a timeframe
        else:
            endpoint = "top" # Default to top

        url = f"https://www.reddit.com/r/{subreddit}/{endpoint}.json?t={time_filter}&limit={limit}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error fetching from Reddit ({subreddit}): {response.status_code}")
                return []
                
            data = response.json()
            posts = []
            
            # Subreddit might return empty children if invalid, but usually status 200
            children = data.get('data', {}).get('children', [])
            
            for child in children:
                p_data = child['data']
                
                # Basic Filtering
                if p_data.get('over_18'): continue
                if p_data.get('is_video'): continue # Skip videos, we want text
                if p_data.get('stickied'): continue
                
                # Text length filter
                # Combine title and body for the script source
                full_text = p_data.get('title', '') + "\n" + p_data.get('selftext', '')
                
                # Filter out likely empty/media-only posts
                if not p_data.get('selftext') and not p_data.get('title'): 
                    # print(f"Skipped {p_data['id']}: Empty")
                    continue
                
                # Relaxed length check (20 chars min, 10000 max)
                if len(full_text) < 20 or len(full_text) > 10000:
                    # print(f"Skipped {p_data['id']}: Length {len(full_text)}")
                    continue
                
                posts.append({
                    'subreddit': subreddit,
                    'id': p_data['id'],
                    'title': html.unescape(p_data['title']),
                    'text': html.unescape(p_data.get('selftext', '')), # Keep original separation
                    'url': p_data['url'],
                    'author': p_data['author']
                })

                
            return posts
            
        except Exception as e:
            print(f"Reddit Client Error: {e}")
            return []

    def get_top_post(self, subreddit=None, time_filter="day"):
        """
        Legacy method for backward compatibility if needed, 
        returns just the first valid post.
        """
        posts = self.get_top_posts(subreddit, time_filter, limit=10)
        return posts[0] if posts else None
