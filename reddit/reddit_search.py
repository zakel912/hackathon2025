import praw

reddit = praw.Reddit(
    client_id="<your_client_id>",
    client_secret="<your_client_secret>",
    password="<your_password>",
    username="<your_username>",
    user_agent="<your_user_agent>",
)

# https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html

# .new() for the newest posts
# .top() for the most popular posts
# .hot() for the most active posts

for submission in reddit.subreddit("wallstreetbets+stocks+investing").hot(limit=5):
    print(f"--------------")
    print(f"title: {submission.title}")
    print(f"content: {submission.selftext}") # can be empty
    print("comments:")
    for comment in submission.comments:
        print("> ", comment.body)
    print()