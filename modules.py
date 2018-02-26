import random
import pprint
import string
import sys
import json
import re
import praw
import progressbar
from HTMLParser import HTMLParser
from bs4 import BeautifulSoup
from pymongo import MongoClient

userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"
client_id = "XfLj8EkdiapGIg"
client_secret = "Sn2OGpkkWG_IlPCpM9E3hX46K-k"

dbClient = MongoClient()
db = dbClient.snapbackComments


postedCommentsCache = {}
redditPrawDict = {}

regex = re.compile(r"(t[0-9]_)?(.+)")

# runs a script collecting posts and parses them to then post to another subreddit
# assumes bots are already created
# run as python modules.py parseSubs subreddit1 subreddit2 subreddit3
def getRandomString(N=16):
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

def parseThisShit(subreddits):
	for subreddit in subreddits:
		try:
			passkeys[subreddit + 'GC_bot']
		except:
			print 'Some passkeys do not exist'
			return
	for subreddit in subreddits:
		redditPrawDict[subreddit] = subredditMaster(subreddit)


	for subreddit in subreddits:
		#get content and parse it
		redditPrawDict[subreddit].getSubredditData()

# database
# sN = subredditName
# cId = commentId
def initCache():
	cursor = list(db.comments.find())

	for document in cursor:
		if document['sN'] not in postedCommentsCache:
			postedCommentsCache[document['sN']] = {}
		postedCommentsCache[document['sN']][document['cId']] = True

class subredditMaster:

    def __init__(self, subredditName):
    	self.name = subredditName
    	self.prawInit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=userAgent, username=subredditName + 'GC_bot', password=passkeys[subredditName + 'GC_bot'])
    	self.postsToParse = {}
    	self.commentsToPost = {}

    def addDbEntry(self, subredditName, commentId):
		db.comments.insert_one(
			{
				"sN" : subredditName,
				"cId" : commentId
    		}
		)
		if subredditName not in postedCommentsCache:
			postedCommentsCache[subredditName] = {}
		postedCommentsCache[subredditName][commentId] = True

    def postReddit(self, comment):

		soup = BeautifulSoup(comment.body_html, "html5lib")
		titlePost = soup.text.replace("\n\t", " ").replace("\n", " ").replace("\t", " ")
		urlPost = 'reddit.com' + comment.permalink + '?context=10000'

		self.subredditData.submit(titlePost, urlPost)
		self.addDbEntry(self.name, comment.id)

    def dbCacheEntry(self, subredditName, commentId):
		try:
			if (document[subredditName][commentId]):
				return True
		except:
			return False

    def postComments(self, commentsToPost):
		for commentId, commentData in commentsToPost.iteritems():
			if not self.dbCacheEntry(self.name, commentId):
				self.postReddit(commentData)

    def parseComments(self, commentsList, submissionId, submissionScore):
    	tempCommentsObj = {}
    	for comment in commentsList:
    		tempCommentsObj[comment.id] = comment

    	# post condition
    	for comment in commentsList:
    		parentId = regex.match(comment.parent_id).group(2)
    		try:
    			if comment.score > 10 and tempCommentsObj[parentId].score >= 0 and tempCommentsObj[parentId].score*2 < comment.score:
    				if comment.id not in self.commentsToPost:
    					self.commentsToPost[comment.id] = comment
    		except:
				if submissionId in parentId:
					if comment.score > 10 and submissionScore >= 0 and submissionScore*2 < comment.score:
						if comment.id not in self.commentsToPost:
							self.commentsToPost[comment.id] = comment

    def parsePosts(self, postsDict):
    	pBar = progressbar.ProgressBar(max_value=len(postsDict))
    	itera = 0
    	for key, val in postsDict.iteritems():
    		if not val:
    			submissionData = self.prawInit.submission(id=key)
    			submissionData.comment_sort = 'top'
    			submissionData.comments.replace_more(limit=0)
    			commentsList = submissionData.comments.list()
    			self.parseComments(commentsList, submissionData.id, submissionData.score)
    			itera += 1
    			pBar.update(itera)
    	self.postComments(self.commentsToPost)

    def getSubredditData(self):
    	self.subredditData = self.prawInit.subreddit(self.name)
    	for submission in self.subredditData.hot():
    		self.postsToParse[submission.id] = False
    	self.parsePosts(self.postsToParse)



args = sys.argv
if ('genPass' in args):
	print getRandomString()

#read passkeys
passkeys = json.load(open('./passkeys'))


subsToParse = []

if ('--parseSubs' in args):
	idx = args.index('--parseSubs')
	try:
		idx2 = args.index('>')
	except:
		idx2 = len(args)
	for i in range(idx+1, idx2):
		subsToParse.append(args[i])

initCache()

if len(subsToParse) > 0:
	parseThisShit(subsToParse)

