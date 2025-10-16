import praw

reddit = praw.Reddit(
    client_id="<your_client_id>",
    client_secret="<your_client_secret>",
    password="<your_password>",
    username="<your_username>",
    user_agent="<your_user_agent>",
)

# https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html

#Stream submissions from multiple subreddits
subreddit = reddit.subreddit("wallstreetbets+stocks+investing")
for submission in subreddit.stream.submissions():
    print(submission.title)