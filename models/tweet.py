#! /usr/bin/env python
# -*- coding:utf-8 -*-
# 12/02/25 3:24
u"""
開発手順
まず、APIで取得できる情報をすべて保存するクラスを作る
次に、それをアップデート（set型やリスト型、辞書型にも対応できるように）する方法を考える

TODO
there is more efficient implementation for DEBRef
http://hujimi.seesaa.net/article/227616428.html
"""
__author__ = 'endorno'
import pymongo
from pymongo.son_manipulator import AutoReference,NamespaceInjector, SONManipulator
import settings

con=pymongo.Connection()
db=con[settings.DB_NAME]
tweets_col=db.tweets
users_col=db.users


#WARNING:creating link to User from Tweet maybe slow when searching user property.#not experiment
class User(object):
    @classmethod
    def from_DB(cls,from_DB):
        return cls(**from_DB)
    def to_DB(self):
        return vars(self)
    @classmethod
    def from_tweepy(cls,user):
        ret=cls()
        for key,value in vars(user).items():
            if key=="status":
                #TODO find reason of tweepy source code
                #WARNING ignore status info
                print "ignore user's status"
            elif key=="following":
                if value is True:
                    setattr(ret,key,True)
                else:
                    setattr(ret,key,False)
            else:
                setattr(ret,key,value)
        return ret
    def __init__(self,**kwargs):
        self._type="user"
        for k,v in kwargs.items():
            setattr(self,k,v)
    def save(self):
       users_col.save(vars(self))

class Tweet(object):
    @classmethod
    def from_DB(cls,from_DB):
        return cls(**from_DB)
    def to_DB(self):
        return vars(self)
    @classmethod
    def from_tweepy(cls,status):
        u"""
        :Args:
        status Tweepy.models.Status
        """
        tweet=cls()
        for key,value in vars(status).items():

            if key=="user":
                user=User.from_tweepy(value)

                user.save()
                setattr(tweet,key,user)
            elif key=="retweeted_status":
                pass
            elif key=="_api":
                #unsave tweepy's api
                pass
            else:
                setattr(tweet,key,value)
        return tweet
    def __init__(self,**kwargs):
        self._type="tweet"
        for k,v in kwargs.items():
            setattr(self,k,v)

    def save(self):
        tweets_col.save(vars(self))

#########################
# set handler for using original class
#########################
db.add_son_manipulator(NamespaceInjector())
db.add_son_manipulator(AutoReference(db))


class UserTransform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, User):
                son[key] = value.to_DB()
            elif isinstance(value, dict): # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son
    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if "_type" in value and value["_type"] == "user":
                    son[key] = User.from_DB(value)
                else: # Again, make sure to recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son
class TweetTransform(SONManipulator):
    def transform_incoming(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, Tweet):
                son[key] = value.to_DB()
            elif isinstance(value, dict): # Make sure we recurse into sub-docs
                son[key] = self.transform_incoming(value, collection)
        return son
    def transform_outgoing(self, son, collection):
        for (key, value) in son.items():
            if isinstance(value, dict):
                if "_type" in value and value["_type"] == "tweet":
                    son[key] = Tweet.from_DB(value)
                else: # Again, make sure to recurse into sub-docs
                    son[key] = self.transform_outgoing(value, collection)
        return son
db.add_son_manipulator(TweetTransform())
db.add_son_manipulator(UserTransform())


###########################################
# test code
###########################################
import datetime
class DummyTweet(object):
    def __init__(self,text,created_at):
        self.text=text
        self.created_at=created_at
def main():
    db.drop_collection("tweets")
    db.drop_collection("users")

    dummy_tweet=Tweet()
    dummy_tweet.text=u"hoge"
    dummy_tweet.created_at=datetime.datetime.now()

    dummy_user=User()
    dummy_user.name=u"tmp"

    dummy_tweet.user=dummy_user

    tw=Tweet.from_tweepy(dummy_tweet)
    tw.save()
    print list(db.tweets.find())

if __name__ == "__main__":
    main()


  