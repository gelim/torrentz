#!/usr/bin/python
#
# Automagic torrent url download
# powered by www.torrentz.com and some urllib/feedparser magic
#
# -- (c) 2010 mathieu.geli@gmail.com
#

import urllib,feedparser,BeautifulSoup
import sys,os,getopt,re

DEBUG=0
string_max = 50

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    RED  = '\033[31m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1;1m'

    def disable(self):
        self.HEADER = ''
        self.BLUE = ''
        self.GREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''
	slef.BOLD = ''

def usage():
	print "usage: %s [-v|--verbose] [-h|--help] [-n|--no-verified] [-d|--destdir] [-t|--team] search_query" % sys.argv[0]
	print " * verbose      : debug mode prints some internals"
	print " * help         : this useful usage message"
	print " * no-verified  : do not restrict search to verified torrent only"
	print " * destdir      : the directory where we save the downloaded .torrent file"
	print " * team         : torrent team or none for all, e.g: eztv"
	print " * search_query : double-quoted strings separated with spaces, e.g \"linux iso\""
	print ""
	print "Example:"
	print "$ python torrentz.py -d /path/to/rtorrent/autodl \"linux iso\""
	print "0:	Linux Mint 8 Helena iso                            		 (688 Mb) S: 637  P: 50"
	print "1:	Ubuntu v9 04 desktop amd64 CD iso FINAL            		 (696 Mb) S: 216  P: 4"
	print "2:	ubuntu 8 10 desktop i386 iso                       		 (698 Mb) S: 132  P: 2"
	print "3:	Linux Mint 8 Universal \\\Helena\\\ iso            		 (1070 Mb) S: 105  P: 16"
	print "4:	CrunchBang Linux 9 04 01 32bit crunchbang 9 04 01  		 (620 Mb) S: 60  P: 18"
	print "5:	kubuntu 8 10 desktop amd64 iso                     		 (695 Mb) S: 7  P: 1"
	print "Which torrent to retrieve ? (or q to quit) : _"
	print ""

def torrentget(torrent, filename):
	try:
		if DEBUG: print torrent
		t = urllib.urlopen(torrent)
		FILE = open(filename, "w")
		FILE.write(t.read())
		FILE.close()
		return 0
	except Exception as e:
		print e
		return -1

def gethref(matcher, page):
	if DEBUG: print "gethref(%s, %s)" % (matcher, page)
	soup = BeautifulSoup.BeautifulStoneSoup(page)
	urls=soup('a')
	for link in urls:
		try:
			match = re.findall(matcher, link['href'])
			if DEBUG: print "match: %s pour link: %s" % (match, link['href'])
			if match:
				return link['href']
		except KeyError:	
			pass
	return False

def grasp(trackers, destdir, title, trackername, baseurl, linkmatcher, urlappend):
        os.write(sys.stdout.fileno(), "Trying %s... " % trackername)
        trackeridx = gethref(baseurl, trackers)
        if trackeridx:
                trackerpage = urllib.urlopen(trackeridx)
                torrent = gethref(linkmatcher, trackerpage)
		if urlappend != "":
			torrent=urlappend+torrent
                if DEBUG: print "gethref ->", torrent
                if torrent:
                        ret = torrentget(torrent, destdir+"/"+title+".torrent")
                        if ret == 0: print "OK."; sys.exit(0)

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvnd:t:", ["help", "debug", "destdir", "no-verified", "team"])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)	
	# default args here
	site = "http://www.torrentz.com/feed_verifiedP"
	search = "linux iso"
	team = "none"
	destdir="/home/mathieu/ftp/dl/torrents"
	global DEBUG
	for o,a in opts:
		if o in ("-h", "--help"): usage(); sys.exit(0)
		if o in ("-v", "--verbose"): DEBUG = 1
		if o in ("-d", "--destdir"): destdir = a
		if o in ("-t", "--team")   : team = a
		if o in ("-n", "--no-verified") : site = "http://www.torrentz.com/feedP"
	if len(args) != 1: usage(); sys.exit(0)
	search = args[0]
	params = urllib.urlencode({'q' : search})
	f = urllib.urlopen(site + "?%s" % params)
	feed = feedparser.parse(f.read())
	item_num = feed["items"].__len__()
	if item_num == 0: print "Sorry, no torrents found."; sys.exit(0)

	for i in range(item_num):
		item = feed["items"][i]
		title = item['title'][:string_max]
		# on veut des titres de longueurs egaux et strippes a une longueure max, donc on padde la fin avec ' '
		if item['title'].__len__() < string_max:
			title+=(string_max-item['title'].__len__())*' '
		v = item['summary_detail']['value']
		# pattern matching de size, seeds & peers a la va-vite
		size = v['Size: '.__len__(): v.find("Seed")].strip()
		seeds = v[v.find("Seeds")+'Seeds: '.__len__(): v.find("Peer")]
		peers = v[v.find("Peers")+'Peers: '.__len__(): v.find("Hash")]
		if title.lower().find(team) >= 0 or team == "none":
			printstr = "%d:\t%s \t\t (%s) S: "+bcolors.BOLD+bcolors.RED + "%s" + bcolors.ENDC + " P: "+bcolors.BOLD+bcolors.GREEN+"%s"+bcolors.ENDC
			print printstr % (i, title, size, seeds, peers)

	sys.stdout.write("Which torrent to retrieve ? (or q to quit) : ")
	torrent = sys.stdin.readline()
	if torrent.strip() == "q": print "Bye."; sys.exit(0)
	trackerindex = feed['items'][int(torrent)]['link']
	title = feed['items'][int(torrent)]['title'].replace(' ', '_').replace('/', '_') # formatting for saved torrent filename

	if DEBUG: print "GET %s" % trackerindex
	trackers = urllib.urlopen(trackerindex).read()
	
	grasp(trackers, destdir, title, "btchat", "http://www.bt-chat.com", "download.php", "http://www.bt-chat.com/")
	grasp(trackers, destdir, title, "btjunkie", "http://btjunkie.org", "http://dl.btjunkie.org/torrent/.*?\.torrent", "")
	grasp(trackers, destdir, title, "btmon", "http://www.btmon.com", "\.torrent$", "http://btmon.com/")
	grasp(trackers, destdir, title, "tpb", "http://thepiratebay.org", "http://torrents.thepiratebay.org", "")
	grasp(trackers, destdir, title, "h33t", "http://www.h33t.com", "download.php.*?\.torrent", "http://www.h33t.com/")
	grasp(trackers, destdir, title, "monova", "http://www.monova.org", "monova.org/download.*\.torrent", "http://")
	grasp(trackers, destdir, title, "vertor", "http://www.vertor.com", "http://www.vertor.com/.*?mod=download.*?id=", "")

if __name__ == "__main__":
	if BeautifulSoup.__version__ > '3.0.8':
		sys.stderr.write("WARNING: BeautfiulSoup greather than 3.0.8 is known to crash on malformed script tags.\n")
	main()

