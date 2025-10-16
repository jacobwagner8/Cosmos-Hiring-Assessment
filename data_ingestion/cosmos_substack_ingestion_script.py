from substack_api import Newsletter
from substack_api import Post

# Initialize a newsletter by its URL
newsletter = Newsletter("https://example.substack.com")

# Get recent posts (returns Post objects)
recent_posts = newsletter.get_posts(limit=5)

# Get posts sorted by popularity
top_posts = newsletter.get_posts(sorting="top", limit=10)

# Search for posts
search_results = newsletter.search_posts("machine learning", limit=3)

# Get podcast episodes
podcasts = newsletter.get_podcasts(limit=5)

# Get recommended newsletters
recommendations = newsletter.get_recommendations()

# Get newsletter authors
authors = newsletter.get_authors()

# Initialize a post by its URL
post = Post("https://example.substack.com/p/post-slug")

# Get post metadata
metadata = post.get_metadata()

# Get the post's HTML content
content = post.get_content()