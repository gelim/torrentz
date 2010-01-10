#!/usr/bin/python env
#
# Automagic torrent url download
# powered by www.torrentz.com and some urllib/feedparser magic
# FIXME: nice getopts instead of this crap
# FIXME: regexp for string matching
#
# -- (c) 2010 mathieu.geli@gmail.com
#

import urllib,feedparser,sys,os,getopt,re

DEBUG=0

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
	print "usage: %s [-v|--verbose] [-h|--help] [-d|--destdir] [-t|--team] [-T|--tracker] search_query" % sys.argv[0]
	print " * verbose      : debug mode prints some internals"
	print " * help         : this useful usage message"
	print " * destdir      : the directory where we save the downloaded .torrent file"
	print " * team         : torrent team or none for all, e.g: eztv"
	print " * tracker      : torrent site, e.g: bt-chat, thepiratebay, btmon ..."
	print " * search_query : double-quoted strings separated with spaces, e.g \"linux iso\""
	print ""
	print "Example:"
	print "$ python torrentz.py -d /path/to/rtorrent/autodl -T tpb \"linux iso\""
	print "0:	Linux Mint 8 Helena iso                            		 (688 Mb) S: 637  P: 50"
	print "1:	Ubuntu v9 04 desktop amd64 CD iso FINAL            		 (696 Mb) S: 216  P: 4"
	print "2:	ubuntu 8 10 desktop i386 iso                       		 (698 Mb) S: 132  P: 2"
	print "3:	Linux Mint 8 Universal \\\Helena\\\ iso            		 (1070 Mb) S: 105  P: 16"
	print "4:	CrunchBang Linux 9 04 01 32bit crunchbang 9 04 01  		 (620 Mb) S: 60  P: 18"
	print "5:	kubuntu 8 10 desktop amd64 iso                     		 (695 Mb) S: 7  P: 1"
	print "Which torrent to retrieve ? (or q to quit) : _"
	print ""

def trackerfindurl(tracker, page):
	global DEBUG
	if DEBUG: print "trackerfindurl(%s, page)" % tracker
	begin = page.find(tracker)
	if DEBUG: print "begin:", begin
	ofs = page[begin:].find(">")
	if DEBUG: print "ofs:", ofs
	if begin == -1 or ofs == -1:
		print "Sorry, no tracker link found :-("
		return ''
	else:
		return page[begin:begin+ofs].split()[0]


def trackerextracturl(regexp, page):
	global DEBUG
	if DEBUG: print "trackerextracturl(%s, page)" % (regexp)
	url = re.findall(regexp, page)
	if DEBUG: print url
	if url == []:
		print "Problem during url extraction :"
		print bcolors.FAIL+page.split('\n')[0]+bcolors.ENDC
		return ''
	else:
		return url[0]

def trackerget(match_url, regexp, page):
	global DEBUG
	if DEBUG: print "trackerget(%s, %s, page)" % (match_url, regexp)
	url = trackerfindurl(match_url, page)
	url = url.replace('"', '')
	if DEBUG: print "GET %s" % url
	if url:
		page = urllib.urlopen(url)
		torrent = trackerextracturl(regexp, page.read())
		return torrent
	else:
		print "Sorry no tracker found in torrentz index :-("
	return ''

def torrentget(torrent, filename):
	t = urllib.urlopen(torrent)
	FILE = open(filename, "w")
	FILE.write(t.read())
	FILE.close()

# feed_verifiedP means give us RSS with only verified torrents and sorted by descending peers numbers
# any other filter can be constructed via this simple syntax (i.e: verifiedS, gives only verified in HTML sorted by size)

site = "http://www.torrentz.com/feed_verifiedP"
string_max = 50

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvd:t:T:", ["help", "debug", "team", "tracker"])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)	
	# default args here
	search = "linux iso"
	team = "none"
	webtracker = "bt-chat"
	destdir="/home/mathieu/ftp/dl/torrents"
	global DEBUG
	for o,a in opts:
		if o in ("-h", "--help"): usage(); sys.exit(0)
		if o in ("-v", "--verbose"): DEBUG = 1
		if o in ("-d", "--destdir"): destdir = a
		if o in ("-t", "--team")   : team = a
		if o in ("-T", "--tracker"): webtracker = a
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

	os.write(sys.stdout.fileno(), "Which torrent to retrieve ? (or q to quit) : ")
	torrent = sys.stdin.readline()
	if torrent.strip() == "q": print "Bye."; sys.exit(0)
	trackerindex = feed['items'][int(torrent)]['link']
	title = feed['items'][int(torrent)]['title'].replace(' ', '_')

	if DEBUG: print "GET %s" % trackerindex
	trackers = urllib.urlopen(trackerindex)

	# on doit choisir sur quel referenceur de tracker on veut aller
	# bt-chat ? thepiratebay ? ...

	page = trackers.read()
	
	if webtracker == "bt-chat":
		torrent = trackerget("http://www.bt-chat.com", "a href=\"(download\.php.*?)>", page)
		torrent = torrent.replace('"', '')
		if torrent != '': torrent = "http://www.bt-chat.com/"+torrent
	if webtracker == "tpb":
		torrent = trackerget("http://thepiratebay.org", "(http://torrents\.thepiratebay\.org/.*?\.torrent)", page)
	if webtracker == "btmon":
		torrent = trackerget("http://www.btmon.com", "a href=\"(.*?\.torrent)", page)
		if torrent != '': torrent = "http://www.btmon.com/"+torrent
	if DEBUG: print torrent

	if torrent != '': torrentget(torrent, destdir+"/"+title+".torrent")
	
if __name__ == "__main__":
	main()
	
#trackerfindurl("http://btjunkie.org", page)
#trackerfindurl("http://www.vertor.com", page)

