
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
			if allPlace.place_type == 'country':
				
				if allPlace.place_name not in placedict:
					placedict[allPlace.place_name] = {'center': {'lat': allPlace.lat, 'lng': allPlace.lon}, 'count': 1, 'id': allPlace.id}
				else:
					placedict[allPlace.place_name]['count'] += 1
					lats = lats + allPlace.lat
					lons = lons + allPlace.lon

		cent = str(ms.date1/100 +1)[:2]

		if cent not in centdict:
			centdict[cent] = 1
		else:
			centdict[cent] += 1

		if ms.language not in langdict:
			langdict[ms.language] = 1
		else:
			langdict[ms.language] += 1

	centobj = dumps([{'century': key, 'frequency': centdict[key]} for key in sorted(centdict.keys())])
	subbedcent = re.sub(r'[\"\' ]', '', centobj)

	avlats = lats/count
	avlons = lons/count

	placeobj = dumps(placedict)
	#need to use regex to remove quotes in json string  
	subbedplace =re.sub(r'[\"\' ]', '', placeobj)

	langobj = dumps([{'language': key, 'frequency': langdict[key]} for key in langdict])
	subbedlangs = re.sub(r'[\"\' ]', '', langobj)

	return render_template('home.html', avgLat = avlats, avgLon = avlons, places = subbedplace, centuries = subbedcent, languages = langobj, pagetitle = 'Manuscripts of the Robbins Collection')

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
	print centmss
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

@app.route('/mss_by_language_<focuslanguage>', methods = ['GET'])
def ms_by_language(focuslanguage):
	langmss = models.manuscript.query.filter_by(language=focuslanguage)
	headline = 'Manuscripts written in ' + focuslanguage

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

	#pagedict: dictionary of nodes and links in a graph centered on the MS; to be used for vis
	pagedict = {'nodes': [{"name": pagems.shelfmark, "group": 0, "role": 'manuscript', "dbkey": pagems.id}], 'links': []}
	index = 1
	for person_rel in pagems.assoc_people:
		pagedict['nodes'].append({"name": person_rel.person.name_display, "group": 1,
		 "role": person_rel.assoc_type, "dbkey": person_rel.person.id})
		pagedict['links'].append({"source": index, "target": 0, "value": 10})
		index +=1

	for place_rel in pagems.places:
		pagedict['nodes'].append({"name": place_rel.place_name, "group": 2, "role": place_rel.place_type, "dbkey": place_rel.id})
		pagedict['links'].append({"source": index, "target": 0, "value": 10})
		index +=1

	for exdoc in pagems.treatments:
		pagedict['nodes'].append({'name': exdoc.doc_title, 'group': 4, 'role': 'citing article', 'dbkey': exdoc.id})
		pagedict['links'].append({'source': index, 'target': 0, 'value': 10})
		index +=1

	#separate, preliminary placement of orgs into holder dict to account for and prevent duplicate entities
	holder = {}
	for org_assoc in pagems.orgs:
		if org_assoc.org_id in holder:
			holder[org_assoc.org_id]['role'] = holder[org_assoc.org_id]['role'] + ', ' + org_assoc.relationship
		else:
			holder[org_assoc.org_id] = {'name': org_assoc.org.name, 'group': 4, 'role': org_assoc.relationship}

	for item in holder:
		pagedict['nodes'].append(holder[item])
		pagedict['links'].append({'source': index, 'target': 0, 'value': 10})
		index +=1

	#in order to avoid treating multiple relationships as relationships with multiple people,
	#this retrieves all people in this layer and sends the view a dict of {person_id: {'name': '', 'role': ''}}
	relat_people = {}
	for person_assoc in pagems.assoc_people:
		if person_assoc.person_id not in relat_people:
			relat_people[person_assoc.person_id] = {}
			relat_people[person_assoc.person_id]['roles'] = person_assoc.assoc_type
			relat_people[person_assoc.person_id]['name'] = person_assoc.person.name_display
		else:
			relat_people[person_assoc.person_id]['roles'] = relat_people[person_assoc.person_id]['roles'] + ', ' + person_assoc.assoc_type


	#if pagems.publisher
	#publisher not yet implemented, but need to add
	#print(pagedict)

	graphobj = json.dumps(pagedict)
	#graphobj = jsonify(pagedict)
	
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
	valuemap = {'manuscript': models.manuscript, 'person': models.person, 'watermark': models.watermark,
	 'place': models.place, 'org': models.organization, 'exdoc': models.external_doc}
	table = request.args.get('entity')
	ent_id = request.args.get('id')
	result = valuemap[table].query.get(ent_id)

	returndict = {'nodes': [], 'links': []}
	index = 1
	#index starts from 0; on transferring to vis, will have to append and adjust indices
	if table == 'manuscript':
		#this function was called from a manuscript; send back MS and related entities
		#don't need the manuscript itself; calling item is already in the graph and doesn't need to be added
		#actually, this is contextually dependent; need to figure out a way to deal
		for person_rel in result.assoc_people:
			returndict['nodes'].append({'name': person_rel.person.name_display, 'group': 1,
			 'role': person_rel.assoc_type, "dbkey": person_rel.person.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1

		for place_rel in result.places:
			returndict['nodes'].append({"name": place_rel.place_name, "group": 2, "role": place_rel.place_type, "dbkey": place_rel.id})
			returndict['links'].append({"source": index, "target": 0, "value": 10})
			#print place_rel.place_name, place_rel.lat, place_rel.lon
			index +=1

		for wm in result.watermarks:
			returndict['nodes'].append({'name': wm.name, 'group': 3, 'role': 'watermark', 'dbkey': wm.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1
		
		for exdoc in result.treatments:
			returndict['nodes'].append({'name': exdoc.doc_title, 'group': 4, 'role': 'citing article', 'dbkey': exdoc.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1


		return jsonify(returndict)

	elif table == 'person':
		returndict['nodes'].append({'name': result.name_display, 'group': 1, 'role': '', 'dbkey': result.id})

		for ms_rel in result.ms_relations:
			returndict['nodes'].append({'name': models.manuscript.query.get(ms_rel.ms_id).shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1

		return jsonify(returndict)

	elif table == 'watermark':
		returndict['nodes'].append({'name': ('Watermark '+ result.name), 'group': 3, 'role': 'watermark', 'dbkey': result.id})
		
		for ms_rel in result.mss:
			returndict['nodes'].append({'name': ms_rel.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1

		return jsonify(returndict)

	elif table == 'place':
		returndict['nodes'].append({'name': (result.place_name), 'group': 2, 'role': 'place', 'dbkey': result.id})
		
		for ms_rel in result.mss:
			returndict['nodes'].append({'name': ms_rel.shelfmark, 'group': 0, 'role': 'manuscript', 'dbkey': ms_rel.id})
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1

		return jsonify(returndict)

	elif table == 'org':
		returndict['nodes'].append({'name': (result.name), 'group': 4, 'role': 'organization', 'dbkey': result.id})
		
		holder = {}
		for ms_rel in result.ms_relations:
			if ms_rel.ms_id in holder:
				holder[ms_rel.ms_id]['role'] = holder[ms_rel.ms_id]['role'] + ', ' + ms_rel.relationship
			else:
				holder[ms_rel.ms_id] = {'name': ms_rel.ms.shelfmark, 'group': 0, 'role': ms_rel.relationship}

		for item in holder:
			returndict['nodes'].append(holder[item])
			returndict['links'].append({'source': index, 'target': 0, 'value': 10})
			index +=1

		return jsonify(returndict)

	else:
		raise NotImplementedError('Entity not yet implemented')

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
	
