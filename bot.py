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
*[Report a Problem](http://www.reddit.com/message/compose/?to=padmanabh) | \
[Code](https://github.com/lekhakpadmanabh/ToIBot)*
"""
#Database connection + cursor initialization
conn = lite.connect("bot.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS botlog(id INTEGER PRIMARY KEY, 
                  reddit_id TEXT unique, toi_url TEXT,
                  imgur_url TEXT)
               ''')
#reddit api
red = praw.Reddit(USERAGENT)
red.login(username=USERNAME, password=PASSWORD)
#imgur api
client = ImgurClient(IMGUR_CID, IMGUR_KEY)
#Goose
g = Goose()

def screengrab_firefox(url):
    """Firefox with adblock"""

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
    """PhantomJS webdriver"""

    br = webdriver.PhantomJS()
    br.get(url)
    br.save_screenshot('ToIBot.png')
    br.quit()


def imgur_up():
    """Upload to imgur"""

    while True
        try:
            res = client.upload_from_path("ToIBot.png")
            break
        except:
            print "Error:", sys.exc_info()[0]
    return res['link']


def add_record(reddit_id, toi_url, imgur_url):
    """Insert id's and url into db"""

    try:
        cursor.execute("INSERT INTO botlog (reddit_id,toi_url,imgur_url) \
                        VALUES (?,?,?)", (reddit_id,toi_url,imgur_url));
        conn.commit()
    except lite.IntegrityError:
        print "Reddit id {} already exists".format(reddit_id)

def check_record(reddit_id):
    """check if given id has been processed previously"""

    cursor.execute("SELECT reddit_id from botlog where reddit_id=?",
                   (reddit_id,))
    return cursor.fetchone()

def text_summary(url):
    """Return summary and text of article"""

    article = g.extract(url=url)
    return article.meta_description, article.cleaned_text

if __name__ == '__main__':

    subs = red.get_subreddit("india")
    posts = subs.get_new(limit=100)
    for p in posts:

        if check_record(p.id):
            """skip if record has been processed"""

            continue

        if 'timesofindia' not in p.domain:
            """usually timesofindia.indiatimes.com, sometimes
            m.timesofindiatimes.com, etc."""

            continue

        if 'epaper' in p.domain:
            """don't process epaper links"""

            continue

        if '[video]' in p.title.lower():
            """skip stories whose main attraction
            is a video, usually with a [video] in
            title"""

            continue

        screengrab_firefox(p.url)
        link = imgur_up()
        summ,full = text_summary(p.url)
        nopost = True

        while nopost:
            try:
                print p.title
                p.add_comment( COMMENT.format(**{'imgur':link, 'summary':summ, 
                                                 'fulltext':full}) )
                add_record(p.id, p.url, link)
                nopost = False
            except praw.errors.RateLimitExceeded:
                print "Rate limit exceeded, sleeping 8 mins"
                sleep(8*60)
