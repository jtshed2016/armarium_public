import os, sys, json, re
from fastpbkdf2 import pbkdf2_hmac

relpath = os.path.dirname(__file__)
sys.path.append(relpath)

from flask import render_template, redirect, request, session, url_for
from flask.json import dumps, jsonify
from app import app, models, db
from .forms import ExtDocForm, LoginForm, ItemSelectForm, MsEditForm, VolEditForm, ContentEditForm, FeedbackForm
from .data_parse_and_load import load
from base64 import b64encode, b64decode 

from sqlalchemy import func, distinct

@app.route('/')
def homepage():
#set variables for map and charts
	lats = 0
	lons = 0
	count = 0

	placedict = {}
	langdict = {}
	centdict = {}
	formatdict = {}
	supportdict = {'paper': 0, 'parchment': 0, 'papyrus': 0}
	num_vols_dict = {}
	scriptdict = {}
	linedict = {}
	rulingdict = {}
	wmsdict = {}
	orgdict = {}

	
	allmss = models.manuscript.query.all()
	
	#retrieve from the database which charts to show, and accompanying data...this determines what information to retrieve/send
	chartrecords = models.chart.query.filter_by(display=True).order_by(models.chart.displayorder)
	chart_include = {chart.chartname for chart in chartrecords}
	
	for ms in allmss:
		count +=1
		for allPlace in ms.places:
			#count up the number of MSS from each geographic location
			if allPlace.place_type == 'country':
				
				if allPlace.place_name not in placedict:
					placedict[allPlace.place_name] = {'center': {'lat': allPlace.lat, 'lng': allPlace.lon}, 'count': 1, 'id': allPlace.id}
					lats = lats + allPlace.lat
					lons = lons + allPlace.lon
				else:
					placedict[allPlace.place_name]['count'] += 1


		if 'date' in chart_include:
		#count up manuscripts from each century
			cent = str(ms.date1/100 +1)[:2]

			if cent not in centdict:
				centdict[cent] = 1
			else:
				centdict[cent] += 1

		#count up manuscripts in each language, format
		if 'language' in chart_include:
			if ms.ms_language.name not in langdict:
				langdict[ms.ms_language.name] = {'id': ms.ms_language.id, 'count': 1}
			else:
				langdict[ms.ms_language.name]['count'] += 1

		if 'format' in chart_include:
			if ms.ms_format not in formatdict:
				formatname = ms.ms_format
				if ms.ms_format == None:
					formatname = 'Unspecified'
				formatdict[ms.ms_format] = {'id': formatname, 'count': 1}
			else:
				formatdict[ms.ms_format]['count'] += 1

		if 'support' in chart_include:
			for vol in ms.volumes:
				if vol.support == None:
					continue
				for support_type in supportdict:
					if support_type in vol.support:
						supportdict[support_type] +=1

		if 'script' in chart_include:
			ms_scripts = set()
			#use set to avoid duplicate script counts for multivolume MSS
			for vol in ms.volumes:
				for script in vol.scripts:
					ms_scripts.add(script)
			for ms_script in ms_scripts:
				if ms_script.name not in scriptdict:
					scriptdict[ms_script.name] = {'id': ms_script.id, 'count': 1}
				else:
					scriptdict[ms_script.name]['count'] += 1

		if 'lines' in chart_include:
			ms_lines = set()
			for vol in ms.volumes:
				for linesnumber in vol.lines:
					ms_lines.add(linesnumber.id)
			for ms_line in ms_lines:
				if ms_line not in linedict:
					linedict[ms_line] = 1
				else:
					linedict[ms_line] +=1

		if 'ruling' in chart_include:
			for vol in ms.volumes:
				ms_rulings = set()
				for rulingtype in vol.ruling:
					ms_rulings.add(rulingtype)
				for rulingmat in ms_rulings:
					if rulingmat.name not in rulingdict:
						rulingdict[rulingmat.name] = {'id': rulingmat.id, 'count': 1}
					else:
						rulingdict[rulingmat.name]['count'] +=1

		if 'num_volumes' in chart_include:
			if ms.num_volumes not in num_vols_dict:
				num_vols_dict[ms.num_volumes] = 1
			else:
				num_vols_dict[ms.num_volumes] += 1


	if 'people' in chart_include:
		allpeople = models.person.query.all()
		peoplecountdict = {}

		for eachperson in allpeople:
			#get set of MS IDs for each person and get its length -- this is the number of MSS they are related to
			mspersonrelcount = len(set([association.ms_id for association in eachperson.ms_relations.all()]))
			#print eachperson.name_display
			#print mspersonrelcount
			peoplecountdict[eachperson.name_display] = {'count': mspersonrelcount, 'id': eachperson.id}

		#"invert" dictionary so we can rank most frequent people: frequency maps to a list of people
		countdict_inv = {}
		for x in peoplecountdict:
			if peoplecountdict[x]['count'] not in countdict_inv:
				countdict_inv[peoplecountdict[x]['count']] = [{'name': x, 'id': peoplecountdict[x]['id']}]
			else:
				countdict_inv[peoplecountdict[x]['count']].append({'name': x, 'id': peoplecountdict[x]['id']})

		sorted_dict = [(key, countdict_inv[key]) for key in sorted(countdict_inv.keys(), reverse=True)]
		#format: [(frequency1: [name1, name2, ...]), (frequency2: [name1, name2, ...]), ...]


		freqpeople = []
		for personfreq in sorted_dict:
			#print personfreq[0]
			for ind_person in personfreq[1]:
				
				if len(freqpeople) < 15:
					freqpeople.append({'name': ind_person['name'], 'id': ind_person['id'], 'frequency': personfreq[0]})
					#print ind_person
				else:
					break


	if 'watermark' in chart_include:
		all_wms = models.watermark.query.all()
		for wm in all_wms:
			wmsdict[wm.id] = {'name': str(wm.id) + ' ' + wm.name, 'count': len(wm.mss.all())}

	if 'organization' in chart_include:
		all_orgs = models.organization.query.all()
		for org in all_orgs:
			ms_set = set()
			for ms_rel in org.ms_relations:
				ms_set.add(ms_rel.ms_id)
			orgdict[org.name] = {'id': org.id, 'count': len(ms_set)}

	#cent_data = {'visElement': 'langvis', 'visHolderDiv': 'langvisholder', 'toolTipDiv': 'langtooltip', 'x_axis_id': "xaxis-lang", 'x_axis_label': "Language",
	#'y_axis_label': 'Number of Manuscripts', 'urlpath': 'mss_by_century', 'title': 'Chronology', 'context': 'The majority of manuscripts held by the Robbins Collection are early modern, as well as some medieval and newer materials.', 'data': centobj}
	avlats = lats/len(placedict)
	avlons = lons/len(placedict)
	placeobj = dumps(placedict)
	#need to use regex to remove quotes in json string  
	subbedplace =re.sub(r'[\"\' ]', '', placeobj)


	charts = []

	for record in chartrecords:
		chart_data = {
		'visElement': record.qualifier + 'vis',
		 'visHolderDiv': record.qualifier + 'visholder',
		 'toolTipDiv': record.qualifier + 'tooltip',
		 'x_axis_id': 'xaxis-' + record.qualifier,
		 'x_axis_label': record.x_axis_label,
		 'y_axis_label': record.y_axis_label,
		 'urlpath': record.urlpath,
		 'title': record.title,
		 'context': record.displaytext,
		  }
		  #assign "data" based on table

		if record.chartname == 'date':
			centobj = dumps([{'name': str(key) + 'th', 'frequency': centdict[key], 'id': key} for key in sorted(centdict.keys())])
			chart_data['data']  = centobj

		elif record.chartname == 'format':
			formobj = dumps([{'name': formatdict[mstype]['id'], 'id': formatdict[mstype]['id'], 'frequency': formatdict[mstype]['count']} for mstype in formatdict])
			chart_data['data'] = formobj

		elif record.chartname == 'language':
			langobj = dumps(sorted([{'name': key, 'frequency': langdict[key]['count'], 'id': langdict[key]['id']} for key in langdict], key=lambda lang_info: lang_info['frequency'], reverse=True))
			chart_data['data'] = langobj

		elif record.chartname == 'people':
			peopleobj = json.dumps(freqpeople)

			chart_data['data'] = peopleobj

		elif record.chartname == 'support':
			suppobj = dumps([{'name': supporttype, 'id': supporttype, 'frequency': supportdict[supporttype]} for supporttype in supportdict if supportdict[supporttype] > 0])
			chart_data['data'] = suppobj

		elif record.chartname == 'num_volumes':
			volobj = dumps([{'name': str(volnum), 'id': volnum, 'frequency': num_vols_dict[volnum]} for volnum in num_vols_dict])
			chart_data['data'] = volobj

		elif record.chartname == 'script':
			scriptobj = dumps(sorted([{'name': msscript, 'id': scriptdict[msscript]['id'], 'frequency': scriptdict[msscript]['count']} for msscript in scriptdict], key=lambda scriptinstance: scriptinstance['frequency'], reverse=True))
			chart_data['data'] = scriptobj

		elif record.chartname == 'lines':
			lineobj = dumps(sorted([{'name': str(lineno), 'id': lineno, 'frequency': linedict[lineno]} for lineno in linedict], key=lambda linesno: linesno['frequency'], reverse=True))
			chart_data['data'] = lineobj

		elif record.chartname == 'ruling':
			ruleobj = dumps(sorted([{'name': ruling, 'id': rulingdict[ruling]['id'], 'frequency': rulingdict[ruling]['count']} for ruling in rulingdict], key=lambda rulingtype: rulingtype['frequency'], reverse=True))
			chart_data['data'] = ruleobj

		elif record.chartname == 'watermark':
			wmobj = dumps(sorted([{'name': wmsdict[wm]['name'], 'id': wm, 'frequency': wmsdict[wm]['count']} for wm in wmsdict], key=lambda thiswm: thiswm['frequency'], reverse=True))
			chart_data['data'] = wmobj

		elif record.chartname == 'organization':
			orgobj = dumps(sorted([{'name': focusorg, 'id': orgdict[focusorg]['id'], 'frequency': orgdict[focusorg]['count']} for focusorg in orgdict], key=lambda orgrecord: orgrecord['frequency'], reverse=True))
			chart_data['data'] = orgobj

		elif record.chartname == 'place':
			#use existing place dictionary
			placechartobj = dumps(sorted([{'name': placename, 'id': placedict[placename]['id'], 'frequency': placedict[placename]['count']} for placename in placedict], key=lambda placeinstance: placeinstance['frequency'], reverse=True))
			chart_data['data'] = placechartobj
		charts.append(chart_data)

	#Count up people in collection
	allpeople = models.person.query.all()
	peoplecountdict = {}

	for eachperson in allpeople:
		#get set of MS IDs for each person and get its length -- this is the number of MSS they are related to
		mspersonrelcount = len(set([association.ms_id for association in eachperson.ms_relations.all()]))
		#print eachperson.name_display
		#print mspersonrelcount
		peoplecountdict[eachperson.name_display] = {'count': mspersonrelcount, 'id': eachperson.id}

	#"invert" dictionary so we can rank most frequent people: frequency maps to a list of people
	countdict_inv = {}
	for x in peoplecountdict:
		if peoplecountdict[x]['count'] not in countdict_inv:
			countdict_inv[peoplecountdict[x]['count']] = [{'name': x, 'id': peoplecountdict[x]['id']}]
		else:
			countdict_inv[peoplecountdict[x]['count']].append({'name': x, 'id': peoplecountdict[x]['id']})

	sorted_dict = [(key, countdict_inv[key]) for key in sorted(countdict_inv.keys(), reverse=True)]
	#format: [(frequency1: [name1, name2, ...]), (frequency2: [name1, name2, ...]), ...]


	freqpeople = []
	for personfreq in sorted_dict:
		#print personfreq[0]
		for ind_person in personfreq[1]:
			
			if len(freqpeople) < 15:
				freqpeople.append({'name': ind_person['name'], 'id': ind_person['id'], 'frequency': personfreq[0]})
				#print ind_person
			else:
				break
				
	peopleobj = json.dumps(freqpeople)

	peopledata = {'visElement': 'peoplevis', 'visHolderDiv': 'peoplevisholder', 'toolTipDiv': 'peopletooltip', 'x_axis_id': "xaxis-lang", 'x_axis_label': "Person",
	'y_axis_label': 'Appearances in Manuscript Records', 'urlpath': 'person', 'title': 'People', 'context': 'Many well-known figures share a history with the Robbins Collection\'s holdings, whether as subjects, authors, or owners of manuscripts.  Here are some of those that appear most frequently in the records.', 'data': peopleobj}

	return render_template('home.html', avgLat = avlats, avgLon = avlons, places = subbedplace, #centuries = subbedcent,
	 people = peopleobj, pagetitle = 'Manuscripts of the Robbins Collection', charts = charts)

@app.route('/add_ms', methods = ['GET', 'POST'])
def add_ms():
	#to be implemented later
	pass

@app.route('/list_mss', methods = ['GET'])
def list_mss():
	allmss = models.manuscript.query.all()
	return render_template('msresults.html', recs = allmss, headline = 'All Manuscripts')

@app.route('/mss_by_century<cent>', methods=['GET'])
def ms_by_century(cent):
	allmss = models.manuscript.query.all()
	centmss = [ms for ms in allmss if str(ms.date1/100+1)[:2] == cent]
	headline = cent + 'th-century Manuscripts'

	return render_template('msresults.html', recs = centmss, headline = headline)

@app.route('/mss_by_script<idno>', methods=['GET'])
def ms_by_script(idno):
	focus_script = models.script.query.get(idno)
	scriptvols = focus_script.mss.order_by(models.volume.ms_id)
	scriptmss = [models.manuscript.query.get(vol.ms_id) for vol in scriptvols]
	headline = 'Manuscripts with ' + focus_script.name + ' script'

	return render_template('msresults.html', recs = scriptmss, headline = headline)

@app.route('/mss_by_ruling<idno>', methods = ['GET'])
def ms_by_ruling(idno):
	focus_ruling = models.ruling.query.get(idno)
	rulevols = focus_ruling.volumes.order_by(models.volume.ms_id)
	rulemss = [models.manuscript.query.get(vol.ms_id) for vol in rulevols]
	headline = 'Manuscripts ruled in ' + focus_ruling.name

	return render_template('msresults.html', recs = rulemss, headline = headline)

@app.route('/mss_by_language<focus_lang_id>', methods = ['GET'])
def ms_by_language(focus_lang_id):
	focuslanguage = models.language.query.get(focus_lang_id)
	langmss = models.manuscript.query.filter_by(ms_language = focuslanguage)
	headline = 'Manuscripts written in ' + focuslanguage.name

	return render_template('msresults.html', recs = langmss, headline = headline)

@app.route('/mss_by_format_<focusformat>', methods=['GET'])
def ms_by_format(focusformat):
	format_mss = models.manuscript.query.filter_by(ms_format=focusformat)
	headline = 'Manuscripts in ' + focusformat + ' form'

	return render_template('msresults.html', recs=format_mss, headline=headline)

@app.route('/mss_by_support_<focussupport>', methods=['GET'])
def ms_by_support(focussupport):
	support_vols = models.volume.query.filter(models.volume.support.like('%' + focussupport + '%')).order_by(models.volume.ms_id)
	support_mss = [models.manuscript.query.get(vol.ms_id) for vol in support_vols]
	headline = focussupport.title() + ' Manuscripts'

	return render_template('msresults.html', recs=support_mss, headline=headline)

@app.route('/mss_by_vols<numvols>', methods=['GET'])
def ms_by_vols(numvols):
	selectvols = models.manuscript.query.filter_by(num_volumes=numvols).order_by(models.manuscript.id)
	if numvols == 1:
		headline = 'Manuscripts with 1 Volume'
	else:
		headline = 'Manuscripts with ' + str(numvols) + ' Volumes'

	return render_template('msresults.html', recs=selectvols, headline=headline)

@app.route('/mss_by_lines<lineno>', methods=['GET'])
def ms_by_lines(lineno):
	linevols = models.lines.query.get(lineno).volumes
	linemss = [models.manuscript.query.get(linevol.ms_id) for linevol in linevols]

	headline = 'Manuscripts written in ' + str(lineno) + ' lines'

	return render_template('msresults.html', recs=linemss, headline=headline)


@app.route('/ms<idno>', methods = ['GET'])
def ms_view(idno):
	"""Page view for individual MS"""
	
	pagems = models.manuscript.query.get(idno)
	
	#in order to avoid treating multiple relationships as relationships with multiple people,
	#this retrieves all people in this layer and sends the view a dict of {person_id: {'name': '', 'role': ''}}
	#this is for the table of people, not the graph
	relat_people = {}
	for person_assoc in pagems.assoc_people:
		if person_assoc.person_id not in relat_people:
			relat_people[person_assoc.person_id] = {}
			relat_people[person_assoc.person_id]['roles'] = person_assoc.assoc_type
			relat_people[person_assoc.person_id]['name'] = person_assoc.person.name_display
		else:
			relat_people[person_assoc.person_id]['roles'] = relat_people[person_assoc.person_id]['roles'] + ', ' + person_assoc.assoc_type

	#get node/link relationship data for graph	
	graph_data = get_info_from_db(pagems.id, 'manuscript')
	graphobj = json.dumps(graph_data)
	#Hardcoded support types - move later to DB?
	support_types = ['paper', 'parchment', 'papyrus']
	
	return render_template('msview.html', pagetitle = pagems.shelfmark, ms=pagems, people = relat_people, supports = support_types, graphsend=graphobj)

@app.route('/places', methods = ['GET'])
def list_places():
	place_list = models.place.query.all()

	return render_template('placelist.html', recs=place_list, pagetitle='Places of the Robbins Manuscripts')


@app.route('/place<placeid>', methods = ['GET'])
def view_place(placeid):
	#show info about a place in conjunction with their relationships with MSS
	focusplace = models.place.query.get(placeid)

	graph_data = get_info_from_db(placeid, 'place')
	graphobj = json.dumps(graph_data)


	return render_template ('placeview.html', graph = graphobj, location=focusplace, pagetitle=focusplace.place_name + ' in the Robbins Manuscripts')

@app.route('/person<personid>', methods = ['GET'])
def view_person(personid):
	#show info about a person in conjunction with their relationships with MSS
	focusperson = models.person.query.get(personid)

	graph_data = get_info_from_db(personid, 'person')
	graphobj = json.dumps(graph_data)
	
	#in order to avoid treating multiple relationships as relationships with multiple MSS,
	#this retrieves all MSS in this layer and sends the view a dict of {ms_id: {'title': '', 'role': ''}}
	mss = {}
	for ms_rel in focusperson.ms_relations:
		if ms_rel.ms_id not in mss:
			mss[ms_rel.ms_id] = {}
			mss[ms_rel.ms_id]['roles'] = ms_rel.assoc_type
			mss[ms_rel.ms_id]['title'] = ms_rel.ms.titles.filter_by(title_type='main').first()
		else:
			mss[ms_rel.ms_id]['roles'] = mss[ms_rel.ms_id]['roles'] + ', ' + ms_rel.assoc_type

	return render_template('personview.html', person = focusperson, ms_rels = mss, graph = graphobj, pagetitle = focusperson.name_display + ' in the Robbins Manuscripts')

@app.route('/people', methods = ['GET'])
def list_people():
	allpeople = models.person.query.order_by(models.person.name_main).all()

	return render_template('personlist.html', pagetitle='People in the Robbins Manuscripts', people=allpeople)

@app.route('/watermark<wmid>', methods = ['GET', 'POST'])
def view_wm(wmid):
	#show info about a watermark, link to Briquet page, graph of use in MSS
	page_wm = models.watermark.query.get(wmid)

	graph_data = get_info_from_db(wmid, 'watermark')
	graphobj = json.dumps(graph_data)	
	
	return render_template('wmview.html', mainwm = page_wm, graph = graphobj, pagetitle = page_wm.name + ', ' + str(page_wm.id))

@app.route('/watermarks', methods = ['GET'])
def list_watermarks():
	returnlist = []
	wmtypes = models.watermark.query.group_by(models.watermark.name).all()
	for x in wmtypes:
		holder = []
		for y in models.watermark.query.filter_by(name=x.name).all():
			holder.append(y)
		returnlist.append((x, holder))

	return render_template('wmlist.html', pagetitle='Watermarks', recs = returnlist)

@app.route('/orgs', methods = ['GET'])
def list_orgs():
	main_orgs = models.organization.query.order_by(models.organization.name).all()


	return render_template('orglist.html', orgs=main_orgs, pagetitle='Organizations')

@app.route('/org<orgid>', methods=['GET'])
def org_view(orgid):
	focusorg = models.organization.query.get(orgid)
	suborgs = {}
	otherMSrel = {}
	for rel in focusorg.ms_relations:
		if rel.subord_org == True:
			if rel.relationship in suborgs:
				suborgs[rel.relationship].append(rel.ms_id)
			else:
				suborgs[rel.relationship] = [rel.ms_id]
		else:
			if rel.ms_id in otherMSrel:
				otherMSrel[rel.ms_id].append(rel.relationship)
			else:
				otherMSrel[rel.ms_id] = [rel.relationship]

	graph_data = get_info_from_db(orgid, 'org')
	graphobj = json.dumps(graph_data)


	return render_template('orgview.html', pagetitle=focusorg.name, org=focusorg, suborgs=suborgs, graph = graphobj,
	 otherMSrel=otherMSrel)

@app.route('/exworks', methods = ['GET'])
def list_ex_works():
	allworks = models.external_work.query.all()

	return render_template('externalworks.html', pagetitle='Citing Works', works = allworks)

@app.route('/exwork<exworkid>', methods=['GET'])
def ex_work_view(exworkid):

	focuswork = models.external_work.query.get(exworkid)

	graph_data = get_info_from_db(exworkid, 'exwork')
	graphobj = json.dumps(graph_data)

	return render_template('exworkview.html', work = focuswork, graph = graphobj)

@app.route('/exdoc<doc_id>', methods=['GET'])
def ex_doc_view(doc_id):
	focusdoc = models.external_doc.query.get(doc_id)

	graph_data = get_info_from_db(doc_id, 'exdoc')
	graphobj = json.dumps(graph_data)

	return render_template('exdocview.html', doc = focusdoc, graph = graphobj)

@app.route('/about', methods=['GET'])
def about():
	pagetitle = 'About the Project'
	return render_template('about.html', pagetitle = pagetitle)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
	#need to deal with SMTP server here, otherwise this won't work
	#put into database instead?
	pagetitle = 'Feedback'
	feedback_form = FeedbackForm()

	if request.method == 'GET':
		sent = False
		return render_template('feedback.html', form=feedback_form, sent=sent, pagetitle=pagetitle)
	
	if request.method == 'POST':
		#replace this with load to database
		sent = True
		feedName = feedback_form.feedback_name.data
		feedEmail = feedback_form.feedback_email.data
		feedText = feedback_form.feedback_comment.data

		feedMessage = MIMEText(feedText)
		feedMessage['Subject'] = 'Comment submitted through Manuscript Exploration Portal'
		feedMessage['From'] = feedEmail
		feedMessage['To'] = 'jshedlock@ischool.berkeley.edu'

		s = smtplib.SMTP('localhost')
		s.sendmail(feedEmail, ['jshedlock@ischool.berkeley.edu'], feedMessage.as_string())
		s.quit()


		return render_template('feedback.html', sent=sent, pagetitle='Feedback Sent')




@app.route('/sendjson', methods = ['GET'])
def send_json():
	#Accepts HTTP request with ID and table of a node from a graph vis; passes to get_info_from_db,
	#returns JSON response
	table = request.args.get('entity')
	ent_id = request.args.get('id')
	result_dict = get_info_from_db(ent_id, table)

	return jsonify(result_dict)
	


def get_info_from_db(ent_id, table):
	#takes primary key and table name as arguments, returns dictionary of links and nodes to
	#populate or expand graph visualization

	valuemap = {'manuscript': models.manuscript, 'person': models.person, 'watermark': models.watermark,
	 'place': models.place, 'org': models.organization, 'exdoc': models.external_doc, 'exwork': models.external_work}


	result = valuemap[table].query.get(ent_id)

	returndict = {'nodes': [], 'links': []}


	if table == 'manuscript':
		
		resultid = '0_' + str(result.id)

		msdict = return_ms_data(result.id)
		returndict['nodes'].append(msdict)

		person_holder = {}
		for person_rel in result.assoc_people:
			personid = '1_' + str(person_rel.person.id)
			if personid not in person_holder:
				if ((person_rel.person.year_1 == None) and (person_rel.person.year_2 == None)):
					persondates = ''
				elif ((person_rel.person.year_1 != None) and (person_rel.person.year_2 == None)):
					persondates = str(person_rel.person.year_1) + '-'
				elif ((person_rel.person.year_1 == None) and (person_rel.person.year_2 != None)):
					persondates = str(person_rel.person.year_2) + '-'
				else:
					persondates = str(person_rel.person.year_1) + '-' + str(person_rel.person.year_2)


				if ((person_rel.person.datetype == None) or (person_rel.person.datetype == 'life')):
					pass
				elif person_rel.person.datetype == 'approx':
					persondates = 'C. ' + persondates
				elif person_rel.person.datetype == 'profess':
					persondates = 'Active ' + persondates
				elif person_rel.person.datetype == 'century':
					persondates = ''
					if person_rel.person.year_2 != None:
						persondates = str(person_rel.person.year_1/100) + '-' + str(person_rel.person.year_2/100) + ' centuries'
					else:
						persondates = str(person_rel.person.year_1/100) + ' century'



				person_holder[personid] = {"name": person_rel.person.name_display, "group": 1,
			 "role": person_rel.assoc_type, "dbkey": person_rel.person.id, 'id': personid, 'date': persondates, 'url': url_for('view_person', personid=person_rel.person.id)}
			else:
				person_holder[personid]['role'] = person_holder[personid]['role'] + ', ' + person_rel.assoc_type
			
		#then add each person in the holder to the pagedict
		for person in person_holder:
			returndict['nodes'].append(person_holder[person])
			returndict['links'].append({"source": person, "target": resultid, "value": 10})


		for place_rel in result.places:
			placeid = '2_' + str(place_rel.id)
			returndict['nodes'].append({"name": place_rel.place_name, "group": 2, "role": place_rel.place_type, "dbkey": place_rel.id, 'id': placeid, 'url': url_for('view_place', placeid = place_rel.id)})
			returndict['links'].append({"source": placeid, "target": resultid, "value": 10})


		for ms_watermark in result.watermarks:
			watermarkid = '3_' + str(ms_watermark.id)
			returndict['nodes'].append({"name": ms_watermark.name + " (watermark " + str(ms_watermark.id) + ")", "group": 3, "role": "watermark", "dbkey": ms_watermark.id, "id": watermarkid, 'url': url_for('view_wm', wmid = ms_watermark.id), 'briq_url': ms_watermark.url})
			returndict['links'].append({"source": watermarkid, "target": resultid, "value": 10})


		#separate, preliminary placement of orgs into holder dict to account for and prevent duplicate entities
		org_holder = {}
		for org_assoc in result.orgs:
			orgid = '4_'+ str(org_assoc.org_id)
			if orgid not in org_holder:
				org_holder[orgid] = {'name': org_assoc.org.name, 'group': 4, 'role': org_assoc.relationship, 'dbkey': org_assoc.org_id, 'id': orgid, 'url': url_for('org_view', orgid = org_assoc.org_id)}
			else:
				org_holder[orgid]['role'] = org_holder[orgid]['role'] + ', ' + org_assoc.relationship

		for org in org_holder:
			returndict['nodes'].append(org_holder[org])
			returndict['links'].append({'source': org, 'target': resultid, 'value': 10})



		for exdoc in result.treatments:
			exdocid = '5_' + str(exdoc.id)
			if exdoc.doc_title == '':
				exdoctitle = exdoc.ex_work.work_title
			else:
				exdoctitle = exdoc.doc_title

			returndict['nodes'].append({'name': exdoctitle, 'group': 5, 'role': 'citing article', 'dbkey': exdoc.id, 'id': exdocid, 'dates': exdoc.doc_year, 'author': exdoc.doc_author, 'url': url_for('ex_doc_view', doc_id = exdoc.id)})
			returndict['links'].append({'source': exdocid, 'target': resultid, 'value': 10})

		return returndict



	elif table == 'person':

		resultid = '1_' + str(result.id)
		if ((result.year_1 == None) and (result.year_2 == None)):
			persondates = ''
		elif ((result.year_1 != None) and (result.year_2 == None)):
			persondates = str(result.year_1) + '-'
		elif ((result.year_1 == None) and (result.year_2 != None)):
			persondates = str(result.year_2) + '-'
		else:
			persondates = str(result.year_1) + '-' + str(result.year_2)


		if ((result.datetype == None) or (result.datetype == 'life')):
			pass
		elif result.datetype == 'approx':
			persondates = 'C. ' + persondates
		elif result.datetype == 'profess':
			persondates = 'Active ' + persondates
		elif result.datetype == 'century':
			persondates = ''
			if result.year_2 != None:
				persondates = str(result.year_1/100) + '-' + str(result.year_2/100) + ' centuries'
			else:
				persondates = str(result.year_1/100) + ' century'


		returndict['nodes'].append({"name": result.name_display, "group": 1, "role": 'person', "dbkey": result.id, 'id': resultid, 'date': persondates, 'url': url_for('view_person', personid=result.id)})
		#returndict['nodes'].append({"name": result.name_display, "group": 1, "role": 'person', "dbkey": result.id, 'id': resultid})

		#not bothering with roles in this instance...add related MSS to a holder dict first to avoid multiple nodes from multiple relationships
		holder = {}
		for ms_rel in result.ms_relations:
			ms_rel_id = '0_' + str(ms_rel.ms_id)

			if ms_rel_id not in holder:
				holder[ms_rel_id] = return_ms_data(ms_rel.ms_id)

		

		for prelim_ms in holder:
			returndict['nodes'].append(holder[prelim_ms])
			returndict['links'].append({'source': holder[prelim_ms]['id'], 'target': resultid, 'value': 10})
		
		return returndict

	elif table == 'place':
		resultid = '2_' + str(result.id)
		#returndict['nodes'].append({'name': (result.place_name), 'group': 2, 'role': 'place', 'dbkey': result.id, 'id': resultid})
		
		returndict['nodes'].append({"name": result.place_name, "group": 2, "role": "place", "dbkey": result.id, 'id': resultid, 'url': url_for('view_place', placeid = result.id)})

		for ms_rel in result.mss:
			ms_rel_id = '0_' + str(ms_rel.id)

			ms_rel_dict = return_ms_data(ms_rel.id)

			returndict['nodes'].append(ms_rel_dict)
			returndict['links'].append({'source': ms_rel_id, 'target': resultid, 'value': 10})

		return returndict


	elif table == 'watermark':
		resultid = '3_' + str(result.id)
		returndict['nodes'].append({'name': result.name + ' (watermark ' + str(result.id) + ')', 'group': 3, 'role': 'watermark', 'dbkey': result.id, 'id': resultid, 'url': url_for('view_wm', wmid = result.id), 'briq_url': result.url})
		
		for ms_rel in result.mss:
			ms_rel_id = '0_' + str(ms_rel.id)
			ms_rel_dict = return_ms_data(ms_rel.id)
			returndict['nodes'].append(ms_rel_dict)
			returndict['links'].append({'source': ms_rel_id, 'target': resultid, 'value': 10})

		return returndict


	elif table == 'org':
		resultid = '4_' + str(result.id)
		returndict['nodes'].append({'name': (result.name), 'group': 4, 'role': 'organization', 'dbkey': result.id, 'id': resultid, 'url': url_for('org_view', orgid = result.id)})
		
		holder = {}
		for ms_rel in result.ms_relations:
			ms_rel_id = '0_' + str(ms_rel.ms_id)
			if ms_rel_id not in holder:
				ms_rel_dict = return_ms_data(ms_rel.ms_id)
				holder[ms_rel_id] = ms_rel_dict
			else:
				holder[ms_rel_id]['role'] = holder[ms_rel_id]['role'] + ', ' + ms_rel.relationship

		for ms in holder:
			returndict['nodes'].append(holder[ms])
			returndict['links'].append({'source': ms, 'target': resultid, 'value': 10})

		return returndict

	elif table == 'exdoc':
		resultid = '5_' + str(result.id)
		#returndict['nodes'].append({'name': result.doc_title, 'group': 5, 'role': 'citing article', 'dbkey': result.id, 'id': resultid})
	
		#new:
		if result.doc_title == '':
			exdoctitle = result.ex_work.work_title
		else:
			exdoctitle = result.doc_title

		returndict['nodes'].append({'name': exdoctitle, 'group': 5, 'role': 'citing article', 'dbkey': result.id, 'id': resultid, 'dates': result.doc_year, 'author': result.doc_author, 'url': url_for('ex_doc_view', doc_id = result.id)})

		for ms in result.mss:
			ms_id = '0_' + str(ms.id)
			ms_rel_dict = return_ms_data(ms.id)
			returndict['nodes'].append(ms_rel_dict)
			returndict['links'].append({'source': ms_id, 'target': resultid, 'value': 10})

		#add containing work
		contain_work = result.ex_work
		contain_work_id = '6_' + str(contain_work.id)
		returndict['nodes'].append({'name': contain_work.work_title, 'group': 6, 'role': 'external publication', 'dbkey': contain_work.id, 'publisher': contain_work.work_publisher, 'location': contain_work.work_location, 'id': contain_work_id, 'url': url_for('ex_work_view', exworkid = contain_work.id)})
		returndict['links'].append({'source': contain_work_id, 'target': resultid, 'value': 10})

		return returndict

	elif table == 'exwork':
		result_id = '6_' + str(result.id)
		returndict['nodes'].append({'name': result.work_title, 'group': 6, 'role': 'external publication', 'dbkey': result.id, 'publisher': result.work_publisher, 'location': result.work_location, 'id': result_id, 'url': url_for('ex_work_view', exworkid = result.id)})

		for article in result.work_constituents:
			article_id = '5_' + str(article.id)
			returndict['nodes'].append({'name': article.doc_title, 'group': 5, 'role': 'citing article', 'dbkey': article.id, 'id': article_id, 'dates': article.doc_year, 'author': article.doc_author, 'url': url_for('ex_doc_view', doc_id = article.id)})
			returndict['links'].append({'source': article_id, 'target': result_id, 'value': 10})
		return returndict

def return_ms_data(shelf_id):
	this_ms = models.manuscript.query.get(shelf_id)
	resultid = '0_' + str(shelf_id)

	authorquery = this_ms.assoc_people.filter_by(assoc_type = 'author').first()
	if authorquery != None:
		result_author = authorquery.person.name_display
	else:
		result_author = ''
		
	result_title = this_ms.titles.filter_by(title_type='main').first().title_text

	if this_ms.date2 == None:
		result_datestring = str(this_ms.date1)
	else:
		result_datestring = str(this_ms.date1) + '-' + str(this_ms.date2)

	msreturndict = {"name": this_ms.shelfmark, "group": 0, "role": 'manuscript', "dbkey": shelf_id, 'id': resultid,
			'title': result_title, 'date': result_datestring, 'author': result_author, 'url': url_for('ms_view',idno=shelf_id)}

	return msreturndict


@app.route('/sendcontentsjson', methods=['GET'])
def contents_json():
	focus_ms_id = request.args.get('msid')
	contents = models.content_item.query.filter_by(ms_id =focus_ms_id).order_by(models.content_item.id).all()
	returnlist = {item.id: item.text[:50] for item in contents}
	#print returnlist
	return jsonify(returnlist)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
	#declare form
	user_login = LoginForm()

	#get URL of desired page for redirect
	next = request.args.get('next')

	if request.method == 'GET':
	#initial arrival to login page
		return render_template('login.html', userform=user_login, errormessage = None)

	elif request.method == 'POST':
	#info submitted from login page
		retrieved_user = models.user.query.filter_by(username = user_login.username.data).first()
		
		if retrieved_user == None:
		#user not in DB
			return render_template('login.html', userform=user_login, errormessage = 'No such user.')
		else:
		#user in db...retrieve hashed password and salt, compare with input data
			
			#cast unicode string (WTForms input) to ascii (Python default)
			eval_pw = str(user_login.userpassword.data)
			
			#hash and salt are stored b64encoded in database; decode to evaluate
			dec_salt = b64decode(retrieved_user.salt)
			dec_hash = b64decode(retrieved_user.hashed_pw)

			#hash new password with retrieved salt
			newhash = pbkdf2_hmac('sha512', eval_pw, dec_salt, 100000)

			#evaluate hash of newly input password with retrieved salt against stored hash
			if newhash != dec_hash:
				#password is wrong: return login page with error message
				return render_template('login.html', userform=user_login, errormessage = 'Wrong password.  Please try again.')	
			else:
				#password is right; put username in session, redirect to desired page
				session['username'] = user_login.username.data
				return redirect(next)

@app.route('/logout', methods=['GET'])
def logout_user():
	if 'username' not in session:
		return redirect(url_for('login_user'))
	else:
		session.pop('username', None)
		return redirect(url_for('homepage'))

@app.route('/admin', methods=['GET'])
def admin_menu():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/admin'))

	return render_template('adminmenu.html', pagetitle = 'Menu')


@app.route('/addexdoc', methods=['GET', 'POST'])
def add_ex_doc():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/addexdoc'))
	#populate select menus for existing MSS and external works
	msoptions = [(ms.id, (str(ms.id))) for ms in models.manuscript.query.all()]
	exworkoptions = [(work.id, work.work_title) for work in models.external_work.query.all()]

	newExForm = ExtDocForm()
	newExForm.ex_ref_ms.choices = msoptions
	newExForm.ex_main_title.choices = exworkoptions
	
	if request.method == 'POST':
	#user is submitting new data

		if newExForm.ex_main_title_new.data != '':
		#new source work: needs to be created and committed before work
			newwork = models.external_work(
				work_title = newExForm.ex_main_title_new.data,
				work_publisher = newExForm.ex_publisher.data,
				work_location = newExForm.ex_pub_loc.data
				)
			db.session.add(newwork)
			db.session.commit()

			workid = newwork.id

		else:
		#existing source work: assign input from main title as foreign key
			workid = newExForm.ex_main_title.data

		newdoc = models.external_doc(
			doc_title = newExForm.ex_sub_title.data,
			doc_author = newExForm.ex_author.data,
			doc_year = newExForm.ex_pub_year.data,
			doc_volume = newExForm.ex_pub_volume.data,
			doc_issue = newExForm.ex_pub_issue.data,
			doc_page_range = newExForm.ex_page_range.data,
			doc_notes = newExForm.ex_pub_notes.data,
			work_id = workid,
			mss = [models.manuscript.query.get(shelfmark) for shelfmark in newExForm.ex_ref_ms.data]
			)
		db.session.add(newdoc)
		db.session.commit()



		return render_template('submitted.html', pagetitle = "Document Submitted", doctype = "External Document", msnumber = newExForm.ex_ref_ms.data)

	else:
	#user is simply viewing page

		return render_template('addexdoc.html', pagetitle = "New External Document", newExForm = newExForm)

@app.route('/editexdoc', methods=['GET', 'POST'])
def edit_ex_doc():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/editexdoc'))

	if (request.method == 'GET') and (request.args.get('item_to_edit') == None):
		ex_doc_select = ItemSelectForm()
		docoptions = [(doc.id, (doc.doc_author + ': ' + doc.doc_title[:50])) for doc in models.external_doc.query.all()]
		ex_doc_select.item_to_edit.choices = docoptions
		return render_template('msedit_select.html', pagetitle = 'Document Selection', doctype='External Document', edit_item_select = ex_doc_select)

	elif (request.method == 'GET') and (request.args.get('item_to_edit') != None):
		edit_doc_id = request.args.get('item_to_edit')
		edit_doc = models.external_doc.query.get(edit_doc_id)

		
		msoptions = [(ms.id, (str(ms.id))) for ms in models.manuscript.query.all()]
		exworkoptions = [(work.id, work.work_title) for work in models.external_work.query.all()]
		currentwork = models.external_work.query.get(edit_doc.work_id)
		#print edit_doc.work_id
		docform = ExtDocForm(ex_ref_ms = [ms.id for ms in edit_doc.mss], ex_main_title = edit_doc.work_id)

		docform.ex_ref_ms.choices = msoptions
		docform.ex_main_title.choices = exworkoptions
		
		#docform.ex_ref_ms.data = edit_doc.mss
		#docform.ex_main_title.data = currentwork.work_title
		docform.ex_sub_title.data = edit_doc.doc_title
		docform.ex_author.data = edit_doc.doc_author
		docform.ex_pub_volume.data = edit_doc.doc_volume
		docform.ex_pub_issue.data = edit_doc.doc_issue
		docform.ex_page_range.data = edit_doc.doc_page_range
		docform.ex_pub_year.data = edit_doc.doc_year
		docform.ex_pub_notes.data = edit_doc.doc_notes
		docform.ex_id.data = edit_doc.id


		return render_template('editexdoc.html', pagetitle = 'Edit External Document', modExForm = docform)

	elif request.method == 'POST':
		if request.form.get('ex_main_title_new') != None:
		#new source work: needs to be created and committed before work
			newwork = models.external_work(
				work_title = request.form.get('ex_main_title_new'),
				work_publisher = request.form.get('ex_publisher'),
				work_location = request.form.get('ex_pub_loc')
				)
			db.session.add(newwork)
			db.session.commit()

			workid = newwork.id		

		else:
			#print request.form.get('ex_main_title')
			workid = request.form.get('ex_main_title')

		#print workid
		#print type(workid)
		mod_doc = models.external_doc.query.get(request.form.get('ex_id'))
		mod_doc.doc_title = request.form.get('ex_sub_title')
		mod_doc.doc_author = request.form.get('ex_author')
		mod_doc.doc_year = request.form.get('ex_pub_year')
		mod_doc.doc_volume = request.form.get('ex_pub_volume')
		mod_doc.doc_issue = request.form.get('ex_pub_issue')
		mod_doc.doc_page_range = request.form.get('ex_page_range')
		mod_doc.doc_notes = request.form.get('ex_pub_notes')
		mod_doc.work_id = workid
		mod_doc.mss = [models.manuscript.query.get(shelfmark) for shelfmark in request.form.getlist('ex_ref_ms')]

		db.session.add(mod_doc)
		db.session.commit()		


		return render_template('submitted.html', pagetitle = "External Document Modified", doctype = "Changes to External Doc")



@app.route('/editms', methods = ['GET', 'POST'])
def edit_ms():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/editms'))

	if (request.method == 'GET') and (request.args.get('item_to_edit') == None):
		edit_item_select = ItemSelectForm()
		msoptions = [(ms.id, (str(ms.id))) for ms in models.manuscript.query.all()]
		edit_item_select.item_to_edit.choices = msoptions

		return render_template('msedit_select.html', pagetitle = 'MS Selection', doctype = 'Manuscript', edit_item_select = edit_item_select)

	elif (request.method == 'GET') and (request.args.get('item_to_edit') != None):
		ms_id = request.args.get('item_to_edit')
		edit_ms = models.manuscript.query.get(ms_id)
		msform = MsEditForm()
		
		#assign current values as defaults
		msform.ms_id.data = edit_ms.id
		msform.ms_format.data = edit_ms.ms_format
		msform.ms_date1.data = edit_ms.date1
		msform.ms_date2.data = edit_ms.date2
		msform.ms_datetype.data = edit_ms.datetype
		msform.ms_language.data = edit_ms.language
		msform.ms_summary.data = edit_ms.summary
		msform.ms_ownership.data = edit_ms.ownership_history
		msform.ms_origin.data = edit_ms.origin
		msform.ms_decoration.data = edit_ms.decoration
		msform.ms_binding.data = edit_ms.binding

		return render_template('msedit_edit.html', pagetitle = 'MS Editing', edit_ms = edit_ms, msform = msform)

	elif request.method == 'POST':
		#when form is submitted, retrieve record from DB and assign new records
		#print int(request.form.get('ms_id'))
		update_ms = models.manuscript.query.get(int(request.form.get('ms_id')))

		update_ms.ms_format = request.form.get('ms_format')
		if request.form.get('ms_date1') != '':
			update_ms.date1 = int(request.form.get('ms_date1'))
		else:
			update_ms.date1 = ''
		if request.form.get('ms_date2') != '':
			update_ms.date2 = int(request.form.get('ms_date2'))
		else:
			update_ms.date2 = ''
		update_ms.datetype = request.form.get('ms_datetype')
		update_ms.language = request.form.get('ms_language')
		update_ms.summary = request.form.get('ms_summary')
		update_ms.ownership_history = request.form.get('ms_ownership')
		update_ms.origin = request.form.get('ms_origin')
		update_ms.decoration = request.form.get('ms_decoration')
		update_ms.binding = request.form.get('ms_binding')

		db.session.add(update_ms)
		db.session.commit()

		return render_template('submitted.html', pagetitle = "MS Modified", doctype = "Changes to Manuscript")
	else:
		pass
		#404

@app.route('/editvolume', methods=['GET', 'POST'])
def edit_volume():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/editvolume'))

	if (request.method == 'GET') and (request.args.get('item_to_edit') == None):
		edit_item_select = ItemSelectForm()
		voloptions = [(vol.id, ('MS ' + str(vol.ms_id) + ', Volume ' + str(vol.numeration))) for vol in models.volume.query.order_by(models.volume.ms_id)]
		edit_item_select.item_to_edit.choices = voloptions
		return render_template('msedit_select.html', pagetitle = 'Volume Selection', doctype = 'Volume', edit_item_select = edit_item_select)

	elif (request.method == 'GET') and (request.args.get('item_to_edit') != None):
		vol_id = request.args.get('item_to_edit')
		edit_vol = models.volume.query.get(vol_id)
		volform = VolEditForm(scripts = [script.id for script in edit_vol.scripts], lines = [line.id for line in edit_vol.lines], ruling = [rule.id for rule in edit_vol.ruling])
		volform.scripts.choices = [(script.id, script.name) for script in models.script.query.order_by(models.script.name)]
		volform.lines.choices = [(line.id, str(line.id)) for line in models.lines.query.all()]
		volform.ruling.choices = [(rule.id, rule.name) for rule in models.ruling.query.all()]

		#assign current values as defaults
		volform.vol_id.data = edit_vol.id
		volform.numeration.data = edit_vol.numeration
		volform.support.data = edit_vol.support
		volform.extent.data = edit_vol.extent
		volform.extent_unit.data = edit_vol.extent_unit
		volform.bound_width.data = edit_vol.bound_width
		volform.bound_height.data = edit_vol.bound_height
		volform.leaf_width.data = edit_vol.leaf_width
		volform.leaf_height.data = edit_vol.leaf_height
		volform.written_width.data = edit_vol.written_width
		volform.written_height.data = edit_vol.written_height
		volform.size_unit.data = edit_vol.size_unit
		volform.quire_register.data = edit_vol.quire_register
		volform.phys_arrangement.data = edit_vol.phys_arrangement


		return render_template('volumeedit_edit.html', pagetitle='Edit Volume', edit_vol = edit_vol, volform = volform)

	elif request.method == 'POST':
		#print request.form.getlist('ruling')
		#print [item for item in request.form if item[0] == 'ruling']

		update_vol = models.volume.query.get(request.form.get('vol_id'))

		update_vol.numeration = request.form.get('numeration')
		update_vol.support = request.form.get('support')
		update_vol.extent = request.form.get('extent')
		update_vol.extent_unit = request.form.get('extent_unit')
		update_vol.bound_width = request.form.get('bound_width')
		update_vol.bound_height = request.form.get('bound_height')
		update_vol.leaf_width = request.form.get('leaf_width')
		update_vol.leaf_height = request.form.get('leaf_height')
		update_vol.written_width = request.form.get('written_width')
		update_vol.written_height = request.form.get('written_height')
		update_vol.size_unit = request.form.get('size_unit')
		update_vol.quire_register = request.form.get('quire_register')
		update_vol.phys_arrangement = request.form.get('phys_arrangement')
		update_vol.scripts = [models.script.query.get(scriptrec) for scriptrec in request.form.getlist('scripts')]
		update_vol.lines = [models.lines.query.get(linerec) for linerec in request.form.getlist('lines')]
		update_vol.ruling = [models.ruling.query.get(rule) for rule in request.form.getlist('ruling')]

		db.session.add(update_vol)
		db.session.commit()
		

		return render_template('submitted.html', pagetitle = "Volume Modified", doctype = "Changes to Volume")

@app.route('/editcontents', methods=['GET', 'POST'])
def edit_contents():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/editcontents'))

	if (request.method == 'GET') and (request.args.get('content_item') == None):
		edit_item_select = ItemSelectForm()
		#itemoptions = [(item.id, ('MS ' + str(item.ms_id) + ': ' + item.text[:50])) for item in models.content_item.query.order_by(models.content_item.ms_id)]
		itemoptions = [(ms.id, 'Robbins MS ' + str(ms.id)) for ms in models.manuscript.query.all()]
		edit_item_select.item_to_edit.choices = itemoptions
		return render_template('msedit_select.html', pagetitle = 'Content Item Selection', doctype = 'Content Item', edit_item_select = edit_item_select)

	elif (request.method == 'GET') and (request.args.get('content_item') != None):
		item_id = request.args.get('content_item')
		edit_item = models.content_item.query.get(item_id)

		contentform = ContentEditForm()
		contentform.item_id.data = item_id
		contentform.fol_start_num.data = edit_item.fol_start_num
		contentform.fol_start_side.data = edit_item.fol_start_side
		contentform.fol_end_num.data = edit_item.fol_end_num
		contentform.fol_end_side.data = edit_item.fol_end_side
		contentform.fol_text.data = edit_item.text

		return render_template('contentsedit_edit.html', pagetitle= 'Edit Content', contentform = contentform, edit_item = edit_item)

	elif request.method == 'POST':
		edit_item = models.content_item.query.get(str(request.form.get('item_id')))
		#print request.form.get('fol_start_num')
		#print edit_item
		edit_item.fol_start_num = request.form.get('fol_start_num')
		edit_item.fol_start_side = request.form.get('fol_start_side')
		edit_item.fol_end_num = request.form.get('fol_end_num')
		edit_item.fol_end_side = request.form.get('fol_end_side')
		edit_item.text = request.form.get('fol_text')

		db.session.add(edit_item)
		db.session.commit()

		return render_template('submitted.html', doctype = 'Changes to content item')

@app.route('/adduser', methods=['GET', 'POST'])
def add_user():
	if 'username' not in session:
		return redirect(url_for('login_user', next='/adduser'))

	#todo: imitate MS method, get volume to edit and then load data and form
	return render_template('adduser.html')

@app.route('/homesettings', methods=['GET', 'POST'])
def homepage_settings():
	if request.method =='GET':
		yescharts = json.dumps(sorted([{'id': showchart.id, 'name': showchart.title, 'order': showchart.displayorder} for showchart in models.chart.query.filter_by(display=True).order_by(models.chart.displayorder)], key=lambda retrievechart: retrievechart['order']))
		nocharts = json.dumps(sorted([{'id': showchart.id, 'name': showchart.title, 'order': showchart.displayorder} for showchart in models.chart.query.filter_by(display=False).order_by(models.chart.displayorder)], key=lambda retrievechart: retrievechart['order']))

		return render_template('adminhomeset.html', pagetitle = 'Home Page Settings', charts_shown=yescharts, charts_notshown=nocharts)

	else:
		newcharts = request.get_json()
		for chartindex in range(0, len(newcharts)):
			mod_chart = models.chart.query.get(newcharts[chartindex]['id'])
			mod_chart.displayorder = chartindex
			if newcharts[chartindex]['display'] == 1:
				mod_chart.display = True
			else:
				mod_chart.display = False
			db.session.add(mod_chart)
		db.session.commit()

		return render_template('submitted.html', pagetitle = "Charts Updated", doctype = "Changes to Homepage")

#TODO: add 404 handler
	
