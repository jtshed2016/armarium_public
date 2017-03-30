###Script to scrape LawCat for Robbins manuscripts                ###
###Uses "Robbins MS" keyword query -- working as of 30 March 2017 ###
###Depends on data_parse_and_load.py script in app folder
###Makes calls to Geonames and Briquet Online servers (http://api.geonames.org, http://www.ksbm.oeaw.ac.at),
###as well as LawCat
import urllib, re, json
from bs4 import BeautifulSoup
from app import db, models

import data_parse_and_load


def get_urls_from_result_soup(resultsoup, main_array):
	'''
	Take Soup object from LawCat results page and return array of title-search_url dicts
	'''
	#'entry' represented by briefCitRow table element
	allentries = resultsoup.find_all('td', class_=re.compile('briefCitRow'))
	for item in allentries:

		itemholder = {}
		
		#get title from briefCitRow
		try:
			titlesoup = item.find('span', class_='briefcitTitle')
			itemholder['title'] = titlesoup.a.string
		except:
			itemholder['title'] = '**Problem Title**'
			#print item.string
			


		#get contextual search URL from briefCitRow
		try:
			search_url = 'http://lawcat.berkeley.edu' + titlesoup.a['href']
			itemholder['search_url'] = search_url
		except:
			itemholder['search_url'] = '**Problem URL**'
			#print item.string


		main_array.append(itemholder)

	return main_array

def get_shelfmark(record_list):	
	'''
	takes a list representing a single record, divided into lines, returns shelfmark number
	'''
	for line in record_list:
		
		if (line[:6] ==	"090 8 ") or (line[:6] == "099   ") or  (line[:6] =="090   "):
			#print(line[7:].split(' '))
			#print(len(line[7:].split()))
			try:
				if len((line[7:]).split())==3:
					shelfmark = ((line[7:]).split())[2].strip(' .\n')
				return int(shelfmark)
			except:
				return "Could not find valid shelfmark"


if __name__ == '__main__':
	#get shelfmarks of MSS currently in database
	current_mss = models.manuscript.query.all()
	current_ids = {ms.id for ms in current_mss}

	#print 'Currently in database: ', current_ids

	#first page of "Robbins MS" results on LawCat
	initial_target = 'http://lawcat.berkeley.edu/search/X?SEARCH=%22robbins+ms%22&SORT=D'

	#main array for storage
	resultsarray = []

	#get URLs from first page
	initial_page = urllib.urlopen(initial_target)
	initial_soup = BeautifulSoup(initial_page)
	get_urls_from_result_soup(initial_soup, resultsarray)


	#iterate over all pages of results
		#check for "next" button to see if there are more results
	nextbuttons = initial_soup.find_all("a", text="Next")
	pagecounter = 2
	while len(nextbuttons) > 0:
		#print pagecounter
		new_target = 'http://lawcat.berkeley.edu' + nextbuttons[0].attrs['href']
		new_page = urllib.urlopen(new_target)
		new_soup = BeautifulSoup(new_page)
		get_urls_from_result_soup(new_soup, resultsarray)

		nextbuttons = new_soup.find_all("a", text="Next")

		pagecounter +=1


	#iterate over all results; get stable URLs and preformatted MARC info
	recordscounter = 1
	for record in resultsarray:
		#print 'Record ' + str(recordscounter)
		recordpage = urllib.urlopen(record['search_url'])
		recordsoup = BeautifulSoup(recordpage)
		record['stable_url'] = 'http://lawcat.berkeley.edu' + (recordsoup.find('a', id='recordnum')).get('href')
		
		marctarget = 'http://lawcat.berkeley.edu' + ((recordsoup.find('a', href=re.compile('marc'))).get('href'))
		marcpage = urllib.urlopen(marctarget)
		marcsoup = BeautifulSoup(marcpage)
		record['marcstring'] = marcsoup.pre.text
		recordscounter +=1
	
	#make dictionary of output values
	output_dict = {}
	for record in resultsarray:
		recordlines = record['marcstring'].split('\n')
		record_shelfmark = get_shelfmark(recordlines)


		item_list = []
		item_dict = {}
		#produce a list where 1 MARC field == 1 line == 1 list value
		for line in recordlines:
			#print(line)
			if line[:6].strip() == '':
				pass
			elif line[:6] != "      ":
				item_list.append(line.strip())
			else:
				item_list[len(item_list)-1] = item_list[len(item_list)-1] + " " + line.strip()

		for marc_line in item_list:
			if marc_line[:6].strip() in item_dict:
				item_dict[marc_line[:6].strip()].append(marc_line[7:])
			else: 
				item_dict[marc_line[:6].strip()] = [marc_line[7:]]

		output_dict[record_shelfmark] = item_dict


	###Select data to parse and ingest: only use new records

	new_ids = {recordno for recordno in output_dict if isinstance(recordno, int)}

	#print new_ids
	additions = new_ids.difference(current_ids)

	#print additions

	go_ahead = raw_input('Continue parsing and loading data?  (Y/N)')
	if go_ahead.lower() != 'y':
		exit()

	##################
	###Parse data to necessary format for database ingestion
	##################
	
	data_to_parse = {ms_id: output_dict[ms_id] for ms_id in additions}
	parsed_data = data_parse_and_load.load(data_to_parse)



	##################
	###Load data into database
	##################

	for parsed_record in parsed_data:
		if parsed_record == 'RobbinsMSCould not find valid shelfmark':
			continue
		#print parsed_record
		if ((parsed_data[parsed_record]['format'] == '') or (parsed_data[parsed_record]['format'] == None)):
			thismsformat = 'unspecified'
		else:
			thismsformat = parsed_data[parsed_record]['format']

		ms = models.manuscript(
			id = int(parsed_data[parsed_record]['shelfmark'].split(' ')[2]),
			shelfmark = parsed_data[parsed_record]['shelfmark'],
			ms_format = thismsformat,
			date1 = parsed_data[parsed_record]['date1'],
			date2 = parsed_data[parsed_record]['date2'],
			datetype = parsed_data[parsed_record]['datetype'],
			#language = parsed_data[parsed_record]['language'],
			num_volumes = parsed_data[parsed_record]['volumes'],
			summary = parsed_data[parsed_record]['summary'],
			ownership_history = parsed_data[parsed_record]['ownership_history'],
			origin = parsed_data[parsed_record]['origin'],
			decoration = parsed_data[parsed_record]['decoration'],
			binding = parsed_data[parsed_record]['binding'],
			ds_url = parsed_data[parsed_record]['ds_url']
			)
		db.session.add(ms)


		db.session.commit()

		#check whether ms's language is already in database; create parsed_record if not, otherwise, establish relationship
		if models.language.query.filter_by(name=parsed_data[parsed_record]['language']).first() == None:
			newLang = models.language(
				name = parsed_data[parsed_record]['language'],
				mss = [ms]
				)
		else:
			mslang = models.language.query.filter_by(name=parsed_data[parsed_record]['language']).first()
			mslang.mss.append(ms)


		#iterate over volumes to add volume-specific entities (volume attributes, watermarks, content items)
		#volcounter = used to number volumes in order ("Volume 1," etc.)
		volcounter = 1
		for msvol in parsed_data[parsed_record]['volumeInfo']:
			#print(msvol)
			volItem = models.volume(
				numeration = volcounter,
				support = parsed_data[parsed_record]['support'],
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
				#print parsed_data[parsed_record]

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

		for title in parsed_data[parsed_record]['titles']:
			titleInstance = models.title(
				title_text = title['text'],
				title_type = title['type'],
				ms_id = ms.id
				)
			db.session.add(titleInstance)
		db.session.commit()

		for person in parsed_data[parsed_record]['people']:
			#print(parsed_data[parsed_record]['people'][person])
			#print(parsed_data[parsed_record]['people'][person]['relationship'])

			#check to see if person is already in database; 
			#if not, add to DB
			#if so, retrieve and add new relationships
			personQuery = models.person.query.filter_by(name_main=person).first()
			if personQuery == None:
				personRec = models.person(
					name_main = person,
					name_display = parsed_data[parsed_record]['people'][person]['displayName'],
					name_fuller = parsed_data[parsed_record]['people'][person]['Fullname'],
					year_1 = parsed_data[parsed_record]['people'][person]['date1'],
					year_2 = parsed_data[parsed_record]['people'][person]['date2'],
					datetype = parsed_data[parsed_record]['people'][person]['datetype'],
					numeration = parsed_data[parsed_record]['people'][person]['Numeration'],
					title = parsed_data[parsed_record]['people'][person]['Title']
					)
				db.session.add(personRec)
				db.session.commit()
				
				#new query of newly committed person entity to get ID
				newPersonRecord = models.person.query.filter_by(name_main=person).first()
				for rel in parsed_data[parsed_record]['people'][person]['relationship']:
					relRec = models.person_ms_assoc(
						person_id = newPersonRecord.id,
						ms_id = ms.id,
						assoc_type = rel
						)
					db.session.add(relRec)
					db.session.commit()

			else:
				for rel in parsed_data[parsed_record]['people'][person]['relationship']:
					relRec = models.person_ms_assoc(
						person_id = personQuery.id,
						ms_id = ms.id,
						assoc_type = rel
						)
					db.session.add(relRec)
					db.session.commit()

		for relOrg in parsed_data[parsed_record]['organizations']:
			orgQuery = models.organization.query.filter_by(name=relOrg).first()

			if orgQuery == None:
				addedOrg = models.organization(
					name=relOrg
					)
				db.session.add(addedOrg)
				db.session.commit()

				addedOrgRel = models.org_ms_assoc(
					subord_org = parsed_data[parsed_record]['organizations'][relOrg]['subord_org'],
					relationship = parsed_data[parsed_record]['organizations'][relOrg]['relator'],
					ms_id = ms.id,
					org_id = addedOrg.id
					)
				db.session.add(addedOrgRel)
				db.session.commit()

			else:
				addedOrgRel = models.org_ms_assoc(
					subord_org = parsed_data[parsed_record]['organizations'][relOrg]['subord_org'],
					relationship = parsed_data[parsed_record]['organizations'][relOrg]['relator'],
					ms_id = ms.id,
					org_id = orgQuery.id
					)
				db.session.add(addedOrgRel)
				db.session.commit()


		for placelisting in parsed_data[parsed_record]['places']:
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

		for subject in parsed_data[parsed_record]['subjects']:
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

