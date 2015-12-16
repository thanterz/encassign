import sys
try:
	from jinja2 import Environment, FileSystemLoader
except:
	print "please install Jinja2"
	sys.exit()
import datetime
import requests,json
import time
import string
import os
import argparse

################### override default usage message ######################
def msg(name=None):
	return '''assignment.py
		[-i, start date in format dd/mm/yyyy]
		[-e, start date in format dd/mm/yyyy]
		[-f, filename where the generated html table will be written]

		E.g. python assignment.py -i 10/10/2014 -e 17/12/2015 -f export.html
		'''

################### parse arguments #####################################
def get_arguments():
	parser = argparse.ArgumentParser(usage=msg())
	parser.add_argument('-i', help='start date in dd/mm/yyyy format',required=True)
	parser.add_argument('-e', help='end date in dd/mm/yyyy format',required=True)
	parser.add_argument('-f', help='export file',required=True)

	return parser.parse_args()

class StackApi(object):
	"""docstring for StackApi"""

	def __init__(self, startdate, enddate , exportfile):
		self.check_date(startdate)
		self.check_date(enddate)
		self.startdate = startdate
		self.enddate = enddate
		self.exportfile = exportfile
		self.exlist = []
		self.cnt = 0
		self.data = ''
		self.d = {}
		self.mylist = []
		self.THIS_DIR = os.path.dirname(os.path.abspath(__file__))
		self.TEMPLATE_DIR = "%s/templates" % self.THIS_DIR

	def dir_creation(self):
		############## create template export dir #########################
		if not os.path.exists("export"):
			os.makedirs("export")

	################## check if date format is valid ######################
	def check_date(self,ardate):
		try:
			valid_date = time.strptime(ardate, '%d/%m/%Y')
		except:
			print "Wrong date format"
			print "Correct date format is dd/mm/yyyy"
			sys.exit()

	def answers(self):
		count = 0
		score = 0
		final_score = 0

		itimestamp = time.mktime(datetime.datetime.strptime(self.startdate, "%d/%m/%Y").timetuple())
		etimestamp = time.mktime(datetime.datetime.strptime(self.enddate, "%d/%m/%Y").timetuple())

		if etimestamp < itimestamp:
			print "start date must be before end date"
			sys.exit()
		############# get data from stackapi for the time range given as command line argument#################
		getreq = requests.get('https://api.stackexchange.com/2.2/answers?page=1&pagesize=30&fromdate=%s&todate=%s&order=desc&sort=activity&site=stackoverflow' %(str(int(itimestamp)),str(int(etimestamp))))
		data = json.loads(getreq.text)
		self.data = data

		############# find number of accepted answers ########################
		for accepted_answers in data['items']:
			if str(accepted_answers['is_accepted']) == "True":
				count = count + 1
				score = int(accepted_answers['score'])
				final_score = final_score + score

		########### find average score of the accepted answers ###############
		if count > 0 :
			avg_score = float(final_score)/count
		else:
			avg_score = 0

		self.d["avg_score"] = avg_score
		self.d["c"] = count

	def avg_answer_count(self):
		############## count number of retrieved data ########################
		json_length = len(self.data["items"])
		############## set of unique question ids ############################
		qids = set(i['question_id'] for i in self.data["items"])
		############## count number of unique ids ############################
		count_q_id = len(set(qids))
		############## calculate average answer count per question ###########
		avgpq = float(json_length)/float(count_q_id)
		self.d["avg_answer_count_pq"] = avgpq

	def comment_count(self):
		################## sort retrieved data by scroe #####################
		sorted_data = sorted(self.data['items'], key=lambda k: int(k['score']), reverse=True)
		################### for the top 10 answers... #######################
		first10pairs = [x.get('answer_id') for x in sorted_data[:10]]
		for answid in first10pairs:
			##################### ... get comments ##########################
			getreq = requests.get('https://api.stackexchange.com/2.2/answers/%s/comments?order=desc&sort=creation&site=stackoverflow' % answid);
			jsondata = json.loads(getreq.text)
			##################### count comments ############################
			comments_count = len(jsondata['items'])
			##################### create a list of dictionaries #############
			comment_item = {'answerid' :answid, "sum" : comments_count}
			self.mylist.append(comment_item)
			self.cnt = self.cnt + 1
		self.d["comments"] = self.mylist
		self.exlist.append(self.d)
		
	def template_statistics(self):
		exportpath = "export/%s" % self.exportfile
		########### open export file #################
		fo = open(exportpath, "w")
		####################### render template with data ####################
		env = Environment(loader=FileSystemLoader(self.TEMPLATE_DIR),trim_blocks=True)
		mytemplate = env.get_template('template.html').render( myexportlist=self.exlist)
		###################### write rendered template to file ##############
		fo.write(mytemplate)
		fo.close
	
if __name__ == "__main__":
	args = get_arguments()
	stackapi = StackApi(args.i,args.e,args.f)
	stackapi.dir_creation()
	stackapi.answers()
	stackapi.avg_answer_count()
	stackapi.comment_count()
	stackapi.template_statistics()