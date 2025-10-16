import praw

reddit = praw.Reddit(
    client_id="<your_client_id>",
    client_secret="<your_client_secret>",
    password="<your_password>",
    username="<your_username>",
    user_agent="<your_user_agent>",
)

# https://praw.readthedocs.io/en/stable/code_overview/models/comment.html

# Stream comments from multiple subreddits
subreddit = reddit.subreddit("wallstreetbets+stocks+investing")
for comment in subreddit.stream.comments():
    print(comment.body)
    # comment.submission.title : Title of the submission the comment belongs to