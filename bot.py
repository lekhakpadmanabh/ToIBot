#######################
## Author: Padmanabh
## License: GPLv3
#######################

from imgurpython import ImgurClient
from management import dnd_users
import praw
from selenium import webdriver
import sys
import sqlite3 as lite
from time import sleep 
from xvfbwrapper import Xvfb

try:
    import configparser as cfg
except ImportError:
    import ConfigParser as cfg
#getting secrets
conf = cfg.ConfigParser()
conf.read("config.ini")
USERNAME = conf.get('REDDIT','USERNAME')
PASSWORD = conf.get('REDDIT','PASSWORD')
IMGUR_CID = conf.get('IMGUR','CLIENT_ID')
IMGUR_KEY = conf.get('IMGUR','API_KEY')
USERAGENT = conf.get('GENERAL','USERAGENT')
SUBREDDIT = "padbots" #test

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

def screengrab_firefox(url):
    """get screenshot: firefox with adblock
    and virtual display"""

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
    """get screenshot: headless phantomJS"""

    br = webdriver.PhantomJS()
    br.get(url)
    br.save_screenshot('ToIBot.png')
    br.quit()


def imgur_up():
    """Upload to imgur"""

    while True:
        try:
            res = client.upload_from_path("ToIBot.png")
            return res['link']
        except:
            print "Retrying upload:", sys.exc_info()[0]



def add_record(reddit_id, toi_url, imgur_url):
    """Insert id and urls into db"""

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

#submission format 
COMMENT =\
u"""

**Summary**: {summary}\n
**Key Points**\n ---
{keypoints}\n --- 
[^Full ^Mirror]({imgur})\n
^I'm ^a ^bot [^Message ^Creator](http://www.reddit.com/message/compose/?to=padmanabh) | \
[^Code](https://github.com/lekhakpadmanabh/ToIBot)
"""

#custom summarizer not yet open
from summarizer import summarizer


def format_keypoints(key_points):
    assert len(key_points) == 4
    return ">* {0}\n>* {1}\n>* {2}\n>* {3}\n".format(*[p[2] for p in key_points])

def text_summary(url):
    hsumm, kp = summarizer(url)
    kpf = format_keypoints(kp)
    return hsumm, kpf

if __name__ == '__main__':

    subs = red.get_subreddit(SUBREDDIT)
    posts = subs.get_new(limit=100)
    for p in posts:

        if p.author in dnd_users():
            """filter out submissions by
            users who've requested donotdisturb"""
            continue

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
        summ,kpts = text_summary(p.url)
        nopost = True

        while nopost:
            try:
                print p.title
                p.add_comment( COMMENT.format(**{'imgur':link, 'summary':summ, 
                                                 'keypoints':kpts}) )
                add_record(p.id, p.url, link)
                nopost = False
            except praw.errors.RateLimitExceeded:
                print "Rate limit exceeded, sleeping 8 mins"
                sleep(8*60)

