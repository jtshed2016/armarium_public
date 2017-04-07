'''
Deletes and recreates database, restoring all tables, and regenerates data on MSS in LawCat 
as of January 2016 from trial_II160119.json source file.
Does not restore data added through other means (i.e. the user, external_work, external_doc, and has_external_doc tables)
'''
from app import db, models
import data_parse_and_load
import os, sys, json

fairwarning = raw_input('WARNING: This script will erase all data, including that which it may not be possible to automatically regenerate.  Do you want to continue? (Y/N)\n').upper()
if fairwarning != 'Y':
	exit()



db.drop_all()
db.create_all()


relpath = os.path.dirname(__file__)
sys.path.append(relpath)
#sourcefile = os.path.join(relpath, 'app/half_2.json')
sourcefile = os.path.join(relpath, 'app/source04062017.json')
sourceobj = open(sourcefile)
sourcedict = json.load(sourceobj)
sourceobj.close()


#open file for initial configuration of home page charts, add configuration info to DB
chartconfigname = os.path.join(relpath, 'app/static/chart_info_config.json')
chartconfigobj = open(chartconfigname, 'r')
chartinfo = json.load(chartconfigobj)
chartconfigobj.close()

for tabledict in chartinfo['tables']:
	newtable = models.chart(
		chartname = tabledict['chartname'],
		title = tabledict['title'],
		qualifier = tabledict['qualifier'],
		x_axis_label = tabledict['x_axis_label'],
		y_axis_label = tabledict['y_axis_label'],
		urlpath = tabledict['urlpath'],
		displaytext = tabledict['displaytext'],
		display = tabledict['display'],
		displayorder = tabledict['order'],
		max_values = 15
		#default value of 15, can be adjusted in admin UI
		)
	db.session.add(newtable)
	db.session.commit()


#populate table of relations
relatortermsname = os.path.join(relpath, 'app/static/locrelcodes.json')
relatortermsobj = open(relatortermsname, 'r')
relatorterms = json.load(relatortermsobj)
relatortermsobj.close()

for relatorterm in relatorterms:
	#don't display former owners, owners, or associated names
	if relatorterm in {'asn', 'own', 'fmo'}:
		reldisplay = False
	else:
		reldisplay = True
	
	newrelator = models.person_rel_type(
		name = relatorterms[relatorterm],
		abbrev = relatorterm,
		display = reldisplay
		)

	db.session.add(newrelator)

subjrelator = models.person_rel_type(
	name='Subject',
	abbrev = 'sub',
	display = False)

db.session.add(subjrelator)
db.session.commit()


#parse data
allrecs = data_parse_and_load.load(sourcedict)

print 'Loading to DB'
#load mss into database
for record in allrecs:
	print record, allrecs[record]['shelfmark']
	if record == ('RobbinsMSCould not find valid shelfmark') or (record =='Could not find valid shelfmark'):
		continue
	
	if ((allrecs[record]['format'] == '') or (allrecs[record]['format'] == None)):
		thismsformat = 'unspecified'
	else:
		thismsformat = allrecs[record]['format']

	ms = models.manuscript(
		id = int(allrecs[record]['shelfmark'].split(' ')[2]),
		shelfmark = allrecs[record]['shelfmark'],
		ms_format = thismsformat,
		date1 = allrecs[record]['date1'],
		date2 = allrecs[record]['date2'],
		datetype = allrecs[record]['datetype'],
		num_volumes = allrecs[record]['volumes'],
		summary = allrecs[record]['summary'],
		ownership_history = allrecs[record]['ownership_history'],
		origin = allrecs[record]['origin'],
		decoration = allrecs[record]['decoration'],
		binding = allrecs[record]['binding'],
		catalog_url = allrecs[record]['stable_url'],
		ds_url = allrecs[record]['ds_url']
		)
	db.session.add(ms)


	db.session.commit()

	#check whether ms's language is already in database; create record if not, otherwise, establish relationship
	if models.language.query.filter_by(name=allrecs[record]['language']).first() == None:
		newLang = models.language(
			name = allrecs[record]['language'],
			mss = [ms]
			)
	else:
		mslang = models.language.query.filter_by(name=allrecs[record]['language']).first()
		mslang.mss.append(ms)


	#iterate over volumes to add volume-specific entities (volume attributes, watermarks, content items)
	#volcounter = used to number volumes in order ("Volume 1," etc.)
	volcounter = 1
	for msvol in allrecs[record]['volumeInfo']:
		#print(msvol)
		volItem = models.volume(
			numeration = volcounter,
			support = allrecs[record]['support'],
			extent = msvol['extent'],
			extent_unit = msvol['extentUnit'],
			bound_width = msvol['boundWidth'],
			bound_height = msvol['boundHeight'],
			leaf_width = msvol['supportWidth'],
			leaf_height = msvol['supportHeight'],
			written_width = msvol['writtenWidth'],
			written_height = msvol['writtenHeight'],
			size_unit = msvol['units'],
			quire_register = msvol['quires'],
			phys_arrangement = msvol['arrangement'],
			narr_script = msvol['narr_script'],
			ms_id = ms.id
			)

		db.session.add(volItem)
		db.session.commit()
		volcounter +=1
		#commit here to have id
		
		#if 'watermarks' not in msvol:
			#print allrecs[record]

		for ms_wm in msvol['watermarks']:
			wmQuery = models.watermark.query.get(ms_wm[0])
			if wmQuery == None:
				wmItem  = models.watermark(
					id = ms_wm[0],
					name = ms_wm[1],
					url = ms_wm[2],
					mss = [models.manuscript.query.get(ms.id)]
					)
				db.session.add(wmItem)
			else:
				wmItem = models.watermark.query.get(ms_wm[0])
				wmItem.mss.append(models.manuscript.query.get(ms.id))

		for contentItem in msvol['contents']:
			contentObj = models.content_item(
				text = contentItem['text'],
				fol_start_num = contentItem['startFol'],
				fol_start_side = contentItem['startSide'],
				fol_end_num = contentItem['endFol'],
				fol_end_side = contentItem['endSide'],
				ms_id = ms.id,
				vol_id = volItem.id
				)
			db.session.add(contentObj)

		for linenum in msvol['lines']:
			if models.lines.query.get(linenum) == None:
				newLineObj = models.lines(
					id=linenum
					)
				db.session.add(newLineObj)
				db.session.commit()

			volItem.lines.append(models.lines.query.get(linenum))

		for script_instance in msvol['script']:
			prevScriptObj = models.script.query.filter_by(name=script_instance).first()
			if prevScriptObj == None:
				newScriptObj = models.script(
					name=script_instance
					)
				db.session.add(newScriptObj)
				db.session.commit()
				volItem.scripts.append(newScriptObj)
			else:
				volItem.scripts.append(prevScriptObj)

		for rule_type in msvol['ruling']:
			prevRuleObj = models.ruling.query.filter_by(name=rule_type).first()
			if prevRuleObj == None:
				newRuleObj = models.ruling(
					name=rule_type
					)
				db.session.add(newRuleObj)
				db.session.commit()
				volItem.ruling.append(newRuleObj)
			else:
				volItem.ruling.append(prevRuleObj)

		

	db.session.commit()

	for title in allrecs[record]['titles']:
		titleInstance = models.title(
			title_text = title['text'],
			title_type = title['type'],
			ms_id = ms.id
			)
		db.session.add(titleInstance)
	db.session.commit()

	for person in allrecs[record]['people']:
		#print(allrecs[record]['people'][person])
		#print(allrecs[record]['people'][person]['relationship'])

		#check to see if person is already in database; 
		#if not, add to DB
		#if so, retrieve and add new relationships
		personQuery = models.person.query.filter_by(name_main=person).first()
		if personQuery == None:
			personRec = models.person(
				name_main = person,
				name_display = allrecs[record]['people'][person]['displayName'],
				name_fuller = allrecs[record]['people'][person]['Fullname'],
				year_1 = allrecs[record]['people'][person]['date1'],
				year_2 = allrecs[record]['people'][person]['date2'],
				datetype = allrecs[record]['people'][person]['datetype'],
				numeration = allrecs[record]['people'][person]['Numeration'],
				title = allrecs[record]['people'][person]['Title']
				)
			db.session.add(personRec)
			db.session.commit()
			
			#new query of newly committed person entity to get ID
			newPersonRecord = models.person.query.filter_by(name_main=person).first()
			for rel in allrecs[record]['people'][person]['relationship']:
				#print rel
				relator_type_record = models.person_rel_type.query.filter(models.person_rel_type.name.ilike(rel)).first()
				rel_id = relator_type_record.id

				relRec = models.person_ms_assoc(
					person_id = newPersonRecord.id,
					ms_id = ms.id,
					assoc_type = rel_id
					#role_relation = relator_type_record

					)
				db.session.add(relRec)
				db.session.commit()

		else:
			for rel in allrecs[record]['people'][person]['relationship']:
				#print rel
				relator_type_record = models.person_rel_type.query.filter(models.person_rel_type.name.ilike(rel)).first()
				rel_id = relator_type_record.id

				relRec = models.person_ms_assoc(
					person_id = personQuery.id,
					ms_id = ms.id,
					assoc_type = rel_id
					#role_relation = relator_type_record
					)
				db.session.add(relRec)
				db.session.commit()

	for relOrg in allrecs[record]['organizations']:
		orgQuery = models.organization.query.filter_by(name=relOrg).first()

		if orgQuery == None:
			addedOrg = models.organization(
				name=relOrg
				)
			db.session.add(addedOrg)
			db.session.commit()

			addedOrgRel = models.org_ms_assoc(
				subord_org = allrecs[record]['organizations'][relOrg]['subord_org'],
				relationship = allrecs[record]['organizations'][relOrg]['relator'],
				ms_id = ms.id,
				org_id = addedOrg.id
				)
			db.session.add(addedOrgRel)
			db.session.commit()

		else:
			addedOrgRel = models.org_ms_assoc(
				subord_org = allrecs[record]['organizations'][relOrg]['subord_org'],
				relationship = allrecs[record]['organizations'][relOrg]['relator'],
				ms_id = ms.id,
				org_id = orgQuery.id
				)
			db.session.add(addedOrgRel)
			db.session.commit()


	for placelisting in allrecs[record]['places']:
		#iterate over places
		#check db to see if it exists
		placeQuery = models.place.query.filter_by(place_name = placelisting['name']).first()
		if placeQuery == None:
		#if not, create new place
			addedPlace = models.place(
				place_name = placelisting['name'],
				place_type = placelisting['type'],
				lat = placelisting['lat'],
				lon = placelisting['lon'],
				mss = [models.manuscript.query.get(ms.id)]
				)
			db.session.add(addedPlace)
			db.session.commit()
		else:
			placeQuery.mss.append(models.manuscript.query.get(ms.id))
			db.session.commit()

	for subject in allrecs[record]['subjects']:
		subjquery = models.subject.query.filter_by(subj_name=subject['subj_name']).first()
		if subjquery == None:
			newSubj = models.subject(
				subj_name = subject['subj_name'],
				subj_type = subject['subj_type'],
				)
			db.session.add(newSubj)
			db.session.commit()

		#make sure all subdivisions are in DB
		for subjarea in ['form', 'topic', 'place', 'chronology']:
			for subdivision in subject[subjarea]:
				subdiv_query = models.subject.query.filter_by(subj_name=subdivision).first()
				if subdiv_query == None:
					newSubdiv = models.subject(
						subj_name=subdivision,
						subj_type= subjarea)
					db.session.add(newSubdiv)
					db.session.commit()
		
		#add all subdivisions to array to be used to instantiate association table of subject for MS
		assoc_subdivisions = []
		for subjarea in ['form', 'topic', 'place', 'chronology']:
			for subdivision in subject[subjarea]:
				added_subdiv = models.subject.query.filter_by(subj_name=subdivision).first()
				assoc_subdivisions.append(added_subdiv)
				
		subjectInstance = models.ms_subject_assoc(
			ms_id = ms.id,
			main_subj_id = models.subject.query.filter_by(subj_name=subject['subj_name']).first().id,
			subdivisions = assoc_subdivisions
			)

		db.session.add(subjectInstance)
		db.session.commit()


