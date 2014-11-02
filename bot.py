################
# Author: Pad
# License: GPLv3
################

from goose import Goose
from imgurpython import ImgurClient
import praw
from selenium import webdriver
import sys
import sqlite3 as lite
from time import sleep 
from secrets import (
                    IMGUR_CID,
                    IMGUR_KEY,
                    USERNAME,
                    PASSWORD,
                    )
from xvfbwrapper import Xvfb

USERAGENT ="ToI Bot v1 /u/ToIBot"
COMMENT =\
u"""
[Full Mirror]({imgur})\n
**Summary**: {summary}\n
**Full Text**\n
{fulltext}\n
*[Report a Problem](http://www.reddit.com/message/compose/?to=padmanabh) | [Code](https://github.com/lekhakpadmanabh/ToIBot)*
"""

#Database connection + cursor initialization
conn = lite.connect("bot.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS botlog(id INTEGER PRIMARY KEY, reddit_id TEXT unique, toi_url TEXT,
                       imgur_url TEXT)
''')

red = praw.Reddit(USERAGENT)
red.login(username=USERNAME, password=PASSWORD)
client = ImgurClient(IMGUR_CID, IMGUR_KEY)
g = Goose()

def screengrab_firefox(url):
    vdisplay = Xvfb()
    vdisplay.start()
    fp = webdriver.FirefoxProfile()
    fp.add_extension('adblockplusfirefox.xpi')
    fp.set_preference("extensions.adblockplus.currentVersion", "2.4")
    fox = webdriver.Firefox(fp)
    fox.get(url)
    fox.save_screenshot('ToIBot.png')
    fox.quit()
    vdisplay.stop()

def screengrab_phantom(url):
    br = webdriver.PhantomJS()
    br.get(url)
    br.save_screenshot('ToIBot.png')
    br.quit()


def imgur_up():
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

def text_summary(url):
    article = g.extract(url=url)
    return article.meta_description, article.cleaned_text

if __name__ == '__main__':
    subs = red.get_subreddit("india")
    posts = subs.get_new(limit=100)
    for p in posts:
        if 'timesofindia' not in p.domain:
            continue
        if 'epaper' in p.domain:
            continue
        if '[video]' in p.title.lower():
            continue
        if check_record(p.id):
            continue
        screengrab_firefox(p.url)
        link = imgur_up()
        if link is None:
            continue
        summ,full= text_summary(p.url)
        nopost=True
        while nopost:
            try:
                print p.title #,'\n', link, '\n', summ, '\n', full
                p.add_comment( COMMENT.format(**{'imgur':link, 'summary':summ, 'fulltext':full}))
                add_record(p.id,p.url,link)
                nopost = False
            except praw.errors.RateLimitExceeded:
                print "Rate limit exceeded, sleeping 8 mins"
                sleep(8*60)
