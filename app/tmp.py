import tweepy
import os
import json

try:
    # Twitter thingies
    KEY_TWIT_CON_KEY = os.environ['KEY_TWIT_CON_KEY']
    KEY_TWIT_CON_SECRET = os.environ['KEY_TWIT_CON_SECRET']
    KEY_TWIT_ACC_TOK = os.environ['KEY_TWIT_ACC_TOK']
    KEY_TWIT_ACC_KEY = os.environ['KEY_TWIT_ACC_KEY']
except KeyError as e:
    raise SystemExit("Load API keys into shell variables: `source api_keys.sh`. Missing key: " + str(e))

auth = tweepy.AppAuthHandler(KEY_TWIT_CON_KEY, KEY_TWIT_CON_SECRET)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

if not api:
    raise SystemExit("Can't authenticate")


search_query = "littlerock"
count = 20
since_id = None

new_tweets = api.search(q=search_query, count=count)

for count, tweet in enumerate(new_tweets):
    print(count)
    print(tweet.text)
    print('-'*15)
