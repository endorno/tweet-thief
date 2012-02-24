#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 12/02/25 6:32
from models.tweet import Tweet
import pymongo

__author__ = 'endorno'
from settings import *
import tweepy


def save_test():

    db=pymongo.Connection()[DB_NAME]
    db.drop_collection("tweets")
    db.drop_collection("users")

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(AUTH_TOKEN_KEY, AUTH_TOKEN_SECRET)
    api = tweepy.API(auth)
    cur = tweepy.Cursor(api.friends_timeline,include_entities=True).items(5)

    for s in cur:
        tw=Tweet.from_tweepy(s)
        tw.save(False)
    for s in db.tweets.find():
        for k,v in s.items():
            print k,v


def main():
    save_test()

if __name__ == "__main__":
    main()


  