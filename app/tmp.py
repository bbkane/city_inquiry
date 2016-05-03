import collections
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

Tweet = collections.namedtuple('Tweet', 'text')


def get_tweet_generator(city, count=15):
    city = city.replace(' ', '-')
    city = city.lower()
    print('city: ', city)
    auth = tweepy.AppAuthHandler(KEY_TWIT_CON_KEY, KEY_TWIT_CON_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    if not api:
        return None
    new_tweets = api.search(q=city, count=count)
    for tweet in new_tweets:
        yield Tweet(tweet.text)
    # for count, tweet in enumerate(new_tweets):
    #     print(count)
    #     print(tweet.text)
        print('-'*15)

for tweet in get_tweet_generator('Little Rock'):
    print(tweet)
