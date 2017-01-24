
import os, sys, json, re
from fastpbkdf2 import pbkdf2_hmac

relpath = os.path.dirname(__file__)
sys.path.append(relpath)

from flask import render_template, redirect, request, session, url_for
from flask.json import dumps, jsonify
from app import app, models, db
from .forms import ExtDocForm, LoginForm, ItemSelectForm, MsEditForm, VolEditForm, ContentEditForm
from .data_parse_and_load import load
from base64 import b64encode, b64decode 

from sqlalchemy import func, distinct


@app.route('/')
def homepage():
	lats = 0
	lons = 0
	count = 0
	placedict = {}
	langdict = {}
	centdict = {}

	
	allmss = models.manuscript.query.all()
	
	
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
					lats = lats + allPlace.lat
					lons = lons + allPlace.lon

		#count up manuscripts from each century
		cent = str(ms.date1/100 +1)[:2]

		if cent not in centdict:
			centdict[cent] = 1
		else:
			centdict[cent] += 1

		#count up manuscripts in each language
		if ms.ms_language.name not in langdict:
			langdict[ms.ms_language.name] = {'id': ms.ms_language.id, 'count': 1}
		else:
			langdict[ms.ms_language.name]['count'] += 1

	centobj = dumps([{'century': key, 'frequency': centdict[key]} for key in sorted(centdict.keys())])
	subbedcent = re.sub(r'[\"\' ]', '', centobj)

	avlats = lats/count
	avlons = lons/count

	placeobj = dumps(placedict)
	#need to use regex to remove quotes in json string  
	subbedplace =re.sub(r'[\"\' ]', '', placeobj)

	langobj = dumps([{'language': key, 'frequency': langdict[key]['count'], 'id': langdict[key]['id']} for key in langdict])
	subbedlangs = re.sub(r'[\"\' ]', '', langobj)


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


	return render_template('home.html', avgLat = avlats, avgLon = avlons, places = subbedplace, centuries = subbedcent,
	 languages = langobj, people = peopleobj, pagetitle = 'Manuscripts of the Robbins Collection')

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
	support_vols = models.volume.query.filter_by(support=focussupport).order_by(models.volume.ms_id)
	support_mss = [models.manuscript.query.get(vol.ms_id) for vol in support_vols]
	headline = focussupport.title() + ' Manuscripts'

	return render_template('msresults.html', recs=support_mss, headline=headline)

@app.route('/ms<idno>', methods = ['GET'])
def ms_view(idno):
	"""Page view for individual MS"""
	
	pagems = models.manuscript.query.get(idno)
	
	
	#pagedict: dictionary of nodes and links in a graph centered on the MS; to be used for vis; pagemsid to be used for vis
	pagemsid = '0_' + str(pagems.id)
	pagedict = {'nodes': [{"name": pagems.shelfmark, "group": 0, "role": 'manuscript', "dbkey": pagems.id, 'id': pagemsid}], 'links': []}


	#temporary holder to prevent duplicate entries
	#first get all relationships, and put them all into the holder, with one record per person
	person_holder = {}
	for person_rel in pagems.assoc_people:
		personid = '1_' + str(person_rel.person.id)
		if personid not in person_holder:
			person_holder[personid] = {"name": person_rel.person.name_display, "group": 1,
		 "role": person_rel.assoc_type, "dbkey": person_rel.person.id, 'id': personid}
		else:
			person_holder[personid]['role'] = person_holder[personid]['role'] + ', ' + person_rel.assoc_type
		
	#then add each person in the holder to the pagedict
	for person in person_holder:
		pagedict['nodes'].append(person_holder[person])
		pagedict['links'].append({"source": person, "target": pagemsid, "value": 10})


	for place_rel in pagems.places:
		placeid = '2_' + str(place_rel.id)
		pagedict['nodes'].append({"name": place_rel.place_name, "group": 2, "role": place_rel.place_type, "dbkey": place_rel.id, 'id': placeid})
		pagedict['links'].append({"source": placeid, "target": pagemsid, "value": 10})


	for ms_watermark in pagems.watermarks:
		watermarkid = '3_' + str(ms_watermark.id)
		pagedict['nodes'].append({"name": ms_watermark.name  + ' (watermark)', "group": 3, "role": "watermark", "dbkey": ms_watermark.id, "id": watermarkid})
		pagedict['links'].append({"source": watermarkid, "target": pagemsid, "value": 10})


	#separate, preliminary placement of orgs into holder dict to account for and prevent duplicate entities
	org_holder = {}
	for org_assoc in pagems.orgs:
		orgid = '4_'+ str(org_assoc.org_id)
		if orgid not in org_holder:
			org_holder[orgid] = {'name': org_assoc.org.name, 'group': 4, 'role': org_assoc.relationship, 'dbkey': org_assoc.org_id, 'id': orgid}
		else:
			org_holder[orgid]['role'] = org_holder[orgid]['role'] + ', ' + org_assoc.relationship

	for org in org_holder:
		pagedict['nodes'].append(org_holder[org])
		pagedict['links'].append({'source': org, 'target': pagemsid, 'value': 10})



	for exdoc in pagems.treatments:
		exdocid = '5_' + str(exdoc.id)
		pagedict['nodes'].append({'name': exdoc.doc_title, 'group': 5, 'role': 'citing article', 'dbkey': exdoc.id, 'id': exdocid})
		pagedict['links'].append({'source': exdocid, 'target': pagemsid, 'value': 10})


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



	graphobj = json.dumps(pagedict)

	
	return render_template('msview.html', pagetitle = pagems.shelfmark, ms=pagems, people = relat_people, graphsend=graphobj)

@app.route('/search', methods = ['GET', 'POST'])
def mss_search():
	#needs lots of work, not yet fully implemented
	searchform = SearchForm()
	if searchform.validate_on_submit():
		searchquery = searchform.searchfield.data
		results = models.manuscript.query.filter(searchquery in manuscript.summary)
		#print(results)
		return render_template('searchresult.html', results =results)

@app.route('/places', methods = ['GET'])
def list_places():
	place_list = models.place.query.all()

	return render_template('placelist.html', recs=place_list, pagetitle='Places of the Robbins Manuscripts')


@app.route('/place<placeid>', methods = ['GET'])
def view_place(placeid):
	#show info about a place in conjunction with their relationships with MSS
	focusplace = models.place.query.get(placeid)
	return render_template ('placeview.html', location=focusplace, pagetitle=focusplace.place_name + ' in the Robbins Manuscripts')

@app.route('/person<personid>', methods = ['GET'])
def view_person(personid):
	#show info about a person in conjunction with their relationships with MSS
	focusperson = models.person.query.get(personid)
	
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

	return render_template('personview.html', person = focusperson, ms_rels = mss, pagetitle = focusperson.name_display + ' in the Robbins Manuscripts')

@app.route('/people', methods = ['GET'])
def list_people():
	allpeople = models.person.query.order_by(models.person.name_main).all()

	return render_template('personlist.html', pagetitle='People in the Robbins Manuscripts', people=allpeople)

@app.route('/watermark<wmid>', methods = ['GET', 'POST'])
def view_wm(wmid):
	#show info about a watermark, link to Briquet page, graph of use in MSS
	page_wm = models.watermark.query.get(wmid)
	
	return render_template('wmview.html', mainwm = page_wm, pagetitle = page_wm.name + ', ' + str(page_wm.id))

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


	return render_template('orgview.html', pagetitle=focusorg.name, org=focusorg, suborgs=suborgs,
	 otherMSrel=otherMSrel)

@app.route('/exworks', methods = ['GET'])
def list_ex_works():
	allworks = models.external_work.query.all()

	return render_template('externalworks.html', pagetitle='Citing Works', works = allworks)

@app.route('/exwork<exworkid>', methods=['GET'])
def ex_work_view(exworkid):

	focuswork = models.external_work.query.get(exworkid)

	return render_template('exworkview.html', work = focuswork)

@app.route('/sendjson', methods = ['GET'])
def send_json():
	#return JSON of relationships, to expand and re-render graphs

	##Final word (1/24/2017): Now using unique IDs for nodes and referring to these in link arrays.  
	##Since the view script eliminates duplicate nodes/links and d3 resolves with existing ones,
	##it's okay to send back the origin node.  In fact, it should be included, since this function will 
	##be called by entity view pages to initialize graphs. 
	valuemap = {'manuscript': models.manuscript, 'person': models.person, 'watermark': models.watermark,
	 'place': models.place, 'org': models.organization, 'exdoc': models.external_doc}
	table = request.args.get('entity')
	ent_id = request.args.get('id')
	
	result = valuemap[table].query.get(ent_id)
	
	#'initial' flags whether function is being called in the controller or through an HTTP request.
	#if 'state' is in request, it's HTTP to expand the graph, return HTTP JSON response
	#otherwise, it's within the controller; dump JSON to string and pass
	if 'state' in request.args:
		initial = False
	else:
		initial = True


	returndict = {'nodes': [], 'links': []}


	if table == 'manuscript':
		resultid = '0_' + str(result.id)
		#this function was called from a manuscript; send back related entities
		returndict['nodes'].append({"name": result.shelfmark, "group": 0, "role": 'manuscript', "dbkey": result.id, 'id': resultid})

		person_holder = {}
		for person_rel in result.assoc_people:
			personid = '1_' + str(person_rel.person.id)
			if personid not in person_holder:
				person_holder[personid] = {"name": person_rel.person.name_display, "group": 1,
			 "role": person_rel.assoc_type, "dbkey": person_rel.person.id, 'id': personid}
			else:
				person_holder[personid]['role'] = person_holder[personid]['role'] + ', ' + person_rel.assoc_type
			
		#then add each person in the holder to the pagedict
		for person in person_holder:
			returndict['nodes'].append(person_holder[person])
			returndict['links'].append({"source": person, "target": resultid, "value": 10})


		for place_rel in result.places:
			placeid = '2_' + str(place_rel.id)
			returndict['nodes'].append({"name": place_rel.place_name, "group": 2, "role": place_rel.place_type, "dbkey": place_rel.id, 'id': placeid})
			returndict['links'].append({"source": placeid, "target": resultid, "value": 10})


		for ms_watermark in result.watermarks:
			watermarkid = '3_' + str(ms_watermark.id)
			returndict['nodes'].append({"name": ms_watermark.name, "group": 3, "role": "watermark", "dbkey": ms_watermark.id, "id": watermarkid})
			returndict['links'].append({"source": watermarkid, "target": resultid, "value": 10})


		#separate, preliminary placement of orgs into holder dict to account for and prevent duplicate entities
		org_holder = {}
		for org_assoc in result.orgs:
			orgid = '4_'+ str(org_assoc.org_id)
			if orgid not in org_holder:
				org_holder[orgid] = {'name': org_assoc.org.name, 'group': 4, 'role': org_assoc.relationship, 'dbkey': org_assoc.org_id, 'id': orgid}
			else:
				org_holder[orgid]['role'] = org_holder[orgid]['role'] + ', ' + org_assoc.relationship

		for org in org_holder:
			returndict['nodes'].append(org_holder[org])
			returndict['links'].append({'source': org, 'target': resultid, 'value': 10})



		for exdoc in result.treatments:
			exdocid = '5_' + str(exdoc.id)
			returndict['nodes'].append({'name': exdoc.doc_title, 'group': 5, 'role': 'citing article', 'dbkey': exdoc.id, 'id': exdocid})
			returndict['links'].append({'source': exdocid, 'target': resultid, 'value': 10})

		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)



	elif table == 'person':
		resultid = '1_' + str(result.id)
		returndict['nodes'].append({"name": result.name_display, "group": 1, "role": 'person', "dbkey": result.id, 'id': resultid})

		for ms_rel in result.ms_relations:
			ms_rel_id = '0_' + str(ms_rel.ms_id)
			returndict['nodes'].append({'name': models.manuscript.query.get(ms_rel.ms_id).shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.ms_id, 'id': ms_rel_id})
			returndict['links'].append({'source': ms_rel_id, 'target': resultid, 'value': 10})
		
		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)

	elif table == 'place':
		resultid = '2_' + str(result.id)
		returndict['nodes'].append({'name': (result.place_name), 'group': 2, 'role': 'place', 'dbkey': result.id, 'id': resultid})
		
		for ms_rel in result.mss:
			ms_rel_id = '0_' + str(ms_rel.id)
			returndict['nodes'].append({'name': ms_rel.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.id, 'id': ms_rel_id})
			returndict['links'].append({'source': ms_rel_id, 'target': resultid, 'value': 10})

		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)


	elif table == 'watermark':
		resultid = '3_' + str(result.id)
		returndict['nodes'].append({'name': result.name + ' (watermark)', 'group': 3, 'role': 'watermark', 'dbkey': result.id, 'id': resultid})
		
		for ms_rel in result.mss:
			ms_rel_id = '0_' + str(ms_rel.id)
			#is this right?  Keep an eye out here if there are errors
			returndict['nodes'].append({'name': ms_rel.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.id, 'id': ms_rel_id})
			returndict['links'].append({'source': ms_rel_id, 'target': resultid, 'value': 10})

		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)



	elif table == 'org':
		resultid = '4_' + str(result.id)
		returndict['nodes'].append({'name': (result.name), 'group': 4, 'role': 'organization', 'dbkey': result.id, 'id': resultid})
		
		holder = {}
		for ms_rel in result.ms_relations:
			ms_rel_id = '0_' + str(ms_rel.ms_id)
			if ms_rel_id not in holder:
				holder[ms_rel_id] = {'name': ms_rel.ms.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.ms_id, 'id': ms_rel_id}
			else:
				holder[ms_rel_id]['role'] = holder[ms_rel_id]['role'] + ', ' + ms_rel.relationship

		for ms in holder:
			returndict['nodes'].append(holder[ms])
			returndict['links'].append({'source': ms, 'target': resultid, 'value': 10})

		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)

	elif table == 'exdoc':
		resultid = '5_' + str(result.id)
		returndict['nodes'].append({'name': result.doc_title, 'group': 5, 'role': 'citing article', 'dbkey': result.id, 'id': resultid})



		for ms in result.mss:
			ms_id = '0_' + str(ms.id)
			print ms_id
			returndict['nodes'].append({'name': ms.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms.id, 'id': ms_id})
			returndict['links'].append({'source': ms_id, 'target': resultid, 'value': 10})
		print returndict
		
		if initial == False:
			return jsonify(returndict)
		else:
			return json.dumps(returndict)


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
			
			#cast unicdoe string (WTForms input) to ascii (Python default)
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

#TODO: add 404 handler
	
