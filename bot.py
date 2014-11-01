################
# Author: Pad
# License: GPLv3
################

import praw
from selenium import webdriver
import sys
from imgurpython import ImgurClient
import sqlite3 as lite
from time import sleep 
from secrets import (
                    IMGUR_CID,
                    IMGUR_KEY,
                    USERNAME,
                    PASSWORD,
                    )

USERAGENT ="ToI Bot v1 /u/ToIBot"
COMMENT =\
"""
[Mirror]({imgur})\n
For issues/removal: [send my creator a message](http://www.reddit.com/message/compose/?to=padmanabh)
"""

#Database connection + cursor initialization
conn = lite.connect("bot.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS botlog(id INTEGER PRIMARY KEY, reddit_id TEXT unique, toi_url TEXT,
                       imgur_url TEXT)
''')


#api connections
red = praw.Reddit(USERAGENT)
red.login(username=USERNAME, password=PASSWORD)
client = ImgurClient(IMGUR_CID, IMGUR_KEY)

def screengrab(url):
    print "Grabbing screenshot..."
    br.get(url)
    br.save_screenshot("ToIBot.png")

def imgur_up():
    print "Uploading..."
    try:
        res = client.upload_from_path("ToIBot.png")
        return res['link']
    except:
        print "Error:", sys.exc_info()[0]
        return None

def add_record(reddit_id, toi_url, imgur_url):
    try:
        cursor.execute("INSERT INTO botlog (reddit_id,toi_url,imgur_url) VALUES (?,?,?)", (reddit_id,toi_url,imgur_url));
        conn.commit()
    except lite.IntegrityError:
        print "Reddit id {} already exists".format(reddit_id)

def check_record(reddit_id):
    cursor.execute("SELECT reddit_id from botlog where reddit_id=?",(reddit_id,))
    return cursor.fetchone()

if __name__ == '__main__':
    subs = red.get_subreddit("india")
    posts = subs.get_new(limit=100)
    for p in posts:
        if 'timesofindia' not in p.domain:
            continue
        if 'epaper' in p.domain:
            continue
        if check_record(p.id):
            continue
        #print p.id, p.title
        screengrab(p.url)
        link = imgur_up()
        if link is None:
            continue
        while True:
            try:
                p.add_comment( COMMENT.format(**{'imgur':link}))
                add_record(p.id,p.url,link)
            except praw.errors.RateLimitExceeded:
                print "Rate limit exceeded, sleeping 8 mins"
                sleep(8*60)
