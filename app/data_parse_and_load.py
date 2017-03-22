#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''
Parses data from a JSON source file and renders it into the form used by the Armarium database.  
'''

import json, re, csv, os
from urllib import urlopen
from bs4 import BeautifulSoup



relpath = os.path.dirname(__file__)

#get existing manuscript data in JSON format
sourcefile = os.path.join(relpath, 'trial_II160119.json')
sourceobj = open(sourcefile)
sourcedict = json.load(sourceobj)
sourceobj.close()

#get reference dictionaries for country, language, association codes
countryObj = open(os.path.join(relpath, 'static/loccountrycodes.json'))
langObj = open(os.path.join(relpath,'static/loclangcodes.json'))
relObj = open(os.path.join(relpath,'static/locrelcodes.json'))
countryCodesDict = json.load(countryObj)
countryCodesInverted = {countryCodesDict[key]: key for key in countryCodesDict}
langCodesDict = json.load(langObj)
relCodesDict = json.load(relObj)
countryObj.close()
langObj.close()
relObj.close()
regionList = ['Northern', 'Southern', 'Central', 'Eastern', 'Western']
rulingList = ['ink', 'hard point', 'dry point', 'lead', 'plummet', 'pencil', 'crayon']
scriptDict = {'hyphen': {'semi-textualis': 'semitextualis', 'semi-italic': 'semi-italic', 'half-uncial': 'half-uncial'},
'other': {'cursive': 'cursive', 'cursiva': 'cursive', 'secretary': 'secretary', 'gothic': 'Gothic',
'gothica': 'Gothic', 'libraria': 'libraria', 'textualis': 'textualis', 'semitextualis': 'semitextualis',
'bastard': 'bastard', 'batard': 'bastard', 'bâtarde': 'bastard', 'hybrida': 'bastard', 'bastarda': 'bastard',
'anglicana': 'Anglicana', 'humanistic': 'humanistic', 'humanistica': 'humanistic', 'currens': 'currens',
'italic': 'italic', 'book': 'book', 'bookhand': 'book', 'carolingian': 'Carolingian', 'caroline': 'Carolingian',
'minuscule': 'minuscule', 'cancelleresca': 'chancery', 'chancery': 'chancery', 'bononiensis': 'Bononiensis',
'yemenite': 'Yemenite', 'hebrew': 'Hebrew', 'square': 'square', 'naskhī': 'naskhī', 'temanic': 'Temanic',
'mashait': 'Mashait', 'sephardic': 'Sephardic', 'uncial': 'uncial', 'formata': 'formata', 'antica': 'antica',
'arisiensis': 'Parisiensis'}}

numerals = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}

subj_field_types = {'611': 'meeting', '630': 'uniform title', '648': 'chronology', '650': 'topic', '651': 'place', '655': 'form'}

placeCache = {}
#store places here after call to server; prevent unnecessary multiple calls

##################################################
#API keys for external services
#geonames
key_geonames = 'jtshed_geo2015'

##################################################
#define regular expressions for extracting data
lines = r'([0-9\-]*) [A-Za-z]* *lines'
linepat = re.compile(lines)

ruling = r'(([Ff]rame[- ]?)?[Rr]ul(ed|ing)) in ([A-Za-z ]+)[.:,;]'
rulingpat= re.compile(ruling)

scripts = r' in a?n? ?([\S ]+?)(script|hand)[s,.:;]? ' #add semicolon and period to final set?  
#Need to join with \S+ pattern below to catch non-ASCII characters
scriptpat = re.compile(scripts)
#above seems to be working for most cases as of 1/22 1429

scripts2 = r'in( a|an)* (\S+ )+script'
scriptpat2= re.compile(scripts2)

watermarkstring = r'Briquet|[Ww]atermark'
waterpat = re.compile(watermarkstring)

briquetstring = r'Briquet,? ([\'\"]?[\S ]*?[,\'\"]*) ?([0-9-]+)[;:).]*'
briqpat = re.compile(briquetstring)

#This one used below for splitting contents; do not cull
subfieldstring = r'\|[A-Za-z0-9]'
subfieldpat = re.compile(subfieldstring)
#just gets the flag itself

#replace with ' '
subfieldstring2 = r'(^|\|[A-Za-z0-9])([A-Za-z0-9 ]+)[,.]'
subfieldpat2 = re.compile(subfieldstring2)

subfieldstring3 = r'(\|[a-z0-9]{1})([\S ]+?)[,.]'
subfieldpat3 = re.compile(subfieldstring3)

subfieldstring4 = r'(\|[a-z0-9]{1})([\S ]+?)(?=[,.|])'
#non-consuming lookahead - gets flag and content up to next flag
subfieldpat4 = re.compile(subfieldstring4)

#get register of quires
#3/5/2016: not getting quires properly, may be Python2/3 problem; switching from codes to actual superscripts
#quires = '[⁶⁷⁺⁸¹²⁰³⁵⁴⁹⁻]+'
#quires = '([0-9-]+ ?[⁶⁷⁺⁸¹²⁰³⁵⁴⁹⁻]+)+ ?'
quires = u'([0-9-]+ ?[\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u207B\u207A\u207e\u207d]+)+ ?'
quirepat = re.compile(quires)
#quire2pat from notebook

#get publisher from field 260
pubstring = r'(?<=\|b).+?(?=[.,])'
pubpatt = re.compile(pubstring)

subflagpatt = re.compile(r'\|[a-z]')
#recognizes any letter subfield flag (e.g. "|c")

sfpat = re.compile(r'[Ss]ecundo [Ff]olio')
#finds phrase "secundo folio"
aflagpatt = re.compile(r'(?<=\|a).+$')
#finds flag "a" to end of string: for extracting secundo folio

volspatt = re.compile(r'(?<=\|a)([0-9]) v\. \(([0-9]+), ([0-9]+) ?([a-z]*)')
#finds number of volumes in field 300, if more than 1, and extents of volumes

folpatt = re.compile(r'[Ff]ol. ([0-9xvi])* ?(\(.*?\) )?\+? ?[0-9]+ ?(\(.*?\) ?)?\+? ?([0-9xvi])* ?(\(.*?\))?')
#finds layout of MS from 500/AMREMM 'Collation' field

##Regular expressions for decomposing field 300, physical description
mat_subfieldstring = r'(\|[a-z0-9]{1})([\S ]+?)(?=[.|;]|$)'
#non-consuming lookahead
mat_subfieldpat = re.compile(mat_subfieldstring)

#gets dims of supporting material (.groups()[0] = height, [1]= width)
supportdimstring = r'^([0-9]*) x ([0-9]*)'
supportdimpat = re.compile(supportdimstring)
#gets dims of written area, and units (.groups()[0] = height, [1] = width, [2] = units)
writtendimstring = r'\( ?([0-9]*)[x ]+([0-9]* ?)\) ([A-Za-z]{2})'
writtendimpat = re.compile(writtendimstring)
#gets dims of bound area (.groups()[0] = height,[1]=width)
bounddimstring = r'bound to ([0-9]*) x ([0-9]*)'
bounddimpat = re.compile(bounddimstring)
endunitstring = r'([a-z]*)\.?$'
endunitpat = re.compile(endunitstring)
##

motifpatt = re.compile(r'Motif: ([\S ]*?)[|\n]')
#finds name of pattern on Briquet Online website page for individual watermark
#of the type http://www.ksbm.oeaw.ac.at/_scripts/php/loadRepWmark.php?rep=briquet&refnr=<number>>&lang=fr'

##patterns for identifying types of dates, used in get_person_dates function for fields 100, 600, 700
onedate = re.compile(r'(?P<date1>[0-9]+)\??')
twodate = re.compile(r'(?P<ca1>ca\. ?)?(?P<date1>[0-9]+)\??-(?P<ca2>ca\. ?)?(?P<date2>[0-9]+)\??')
centurypat = re.compile('[0-9]+(?=th)')
##

##patterns for extracting contents from 505 field
#for identifying folio markers
contentsstring = r'[Ff]ol\. ?[0-9IVXLivxlvrab -]*'
contentspat = re.compile(contentsstring)

#for finding and eliminating leading punctuation
beginstring = r'^ ?[:.)\]] ?'
beginpat = re.compile(beginstring)

#for finding and eliminating trailing punctuation
endstring = r';?[ -]*$'
endpat = re.compile(endstring)

#for eliminating trailing numbers at end
trailingnumstring = r' [0-9]{1,2}\. ?$'
trailnumpat = re.compile(trailingnumstring)
##

########################################################
#field-specific processing functions
def getStructuredData(field008):
	returnDict = {}
	#takes field 008 and returns dict with dates, date type, country, and language
	
	returnDict['datetype'] = field008[6]
	
	if 'uu' not in field008[7:11]:
		returnDict['date1'] = int(field008[7:11])
	else:
		returnDict['date1'] = int(field008[7:9] + '00')

	if 'uu' in field008[11:15]:
		returnDict['date2'] = int(field008[11:13] + '00')
	elif field008[11:15] == '    ':
		returnDict['date2'] = None
	else:
		returnDict['date2'] = int(field008[11:15])


	#return country if there, else return none (to be added to list)
	if field008[15:18].strip() != 'xx':
		returnDict['country'] = countryCodesDict[field008[15:18].strip()]
	else:
		returnDict['country'] = None
	returnDict['language'] = langCodesDict[field008[35:38].strip()]

	return returnDict

def getPlace(field260, country):
	#gets location information from field 260, comparing to country from field 008
	#returns dict with additional locations and publisher, if in 260
	returnDict = {'places': []}

	place = field260.strip('[]').split('|')[0].strip('?,[]]: ')

	if place == '':
		return None
	if len(re.split('[,[\]()?]+', place)) == 1:
		if (place.split(' ')[0] in regionList) and (place.split(' ')[1] == country):
		#ignore if this is the same as in field 008
		#discards a more specific region (e.g. "Western...") of a country
			pass
		elif ' and ' in place:
		#evaluate multiple countries in "and" clause
			for segment in place.split(' and '):
				if segment.strip('?,[]]: ') == country:
				#discard if it's the same as assigned country
					pass
				elif segment.strip('?,[]]: ') in countryCodesInverted:
					placeItem = {'name': segment.strip('?,[]]: '), 'type':'country'}
					placeCoords = get_coords(placeItem['name'])
					placeItem['lat'] = placeCoords['lat']
					placeItem['lon'] = placeCoords['lon']
					returnDict['places'].append(placeItem)
		elif (' or ') in place:
		#evaluate multiple countries in "or" clause
			for segment in place.split(' or '):
				if segment.strip('?,[]]: ') == country:
				#discard if it's the same as assigned country
					pass
				elif segment.strip('?,[]]: ') in countryCodesInverted:
					placeItem = {'name': segment.strip('?,[]]: '), 'type':'country'}
					placeCoords = get_coords(placeItem['name'])
					placeItem['lat'] = placeCoords['lat']
					placeItem['lon'] = placeCoords['lon']
					returnDict['places'].append(placeItem)


		elif ((place not in countryCodesInverted) and (re.search('[Ss]\.[Ll]', place) == None)):
			placeItem = {'name': place, 'type':'area'}
			placeCoords = get_coords(placeItem['name'])
			placeItem['lat'] = placeCoords['lat']
			placeItem['lon'] = placeCoords['lon']
			returnDict['places'].append(placeItem)
	else:
		for segment in re.split('[,[\]()?]+', place):
			if (
				(segment.strip() != '') and
				(segment.strip() != country) and
				(re.search('[Ss]\.[Ll]', segment) == None) and
				(re.search('[0-9]{4}', segment) == None) and
				(segment.strip() not in countryCodesInverted)
			):
						
				placeItem = {'name': segment.strip('?,[]]: '), 'type':'area'}
				placeCoords = get_coords(placeItem['name'])
				placeItem['lat'] = placeCoords['lat']
				placeItem['lon'] = placeCoords['lon']
				returnDict['places'].append(placeItem)
	
	return returnDict

def get_coords(placename):
	###LIVE SERVER CALL
	#Sends place name from record to Geonames API, retrieves latitude and longitude
	
	namequery = 'http://api.geonames.org/searchJSON?q=' + placename + '&maxRows=10&username=' + key_geonames
	
	print 'Call to server'
	try:

		namerecords = urlopen(namequery).read().decode("utf-8")
		responsedict = json.loads(namerecords)
		#GeoNames brings up "New England" as first request for "England", so values are hardcoded
		if placename == 'England':
			return {'lat': 51.50853, 'lon': -0.12574}
		else:
			return {'lat': responsedict['geonames'][0]['lat'], 'lon': responsedict['geonames'][0]['lng']}
	except:
		print 'Call to server failed'
		
		return {'lat': None, 'lon': None}
	
	##Substitute return to prevent server call
	#print 'Simulated call to server'
	#return {'lat': 0.0, 'lon': 0.0}
	##

def getTitles(titleField, titleType):
	#takes title fields and returns cleaned up titles with appropriate values
	if titleType == '245':
	#main title
		return ('title', re.sub(r'\|[a-z]', ' ', titleField))
	if titleType == '246':
	#variant title or secundo folio
		if sfpat.search(titleField):
		#secundo folio
			return ('title_sec_folio', aflagpatt.search(titleField).group())
		else:
		#other variant
			return('title_var', re.sub(r'\|[a-z]', ' ', titleField))
	if titleType == '240':
	#uniform title
		return('title_uni', re.sub(r'\|[a-z]', ' ', titleField))


def getDimensions(dimString):
#function to extract dimensions from standard-format 300|c subfield
	#print('getting dimensions')
	returnDict = {}
	
	if supportdimpat.search(dimString):
		support = supportdimpat.search(dimString)
		returnDict['supportHeight'] = support.groups()[0]
		returnDict['supportWidth'] = support.groups()[1]
	else:
		returnDict['supportHeight'] = None
		returnDict['supportWidth'] = None
	
	if writtendimpat.search(dimString):
		written = writtendimpat.search(dimString)
		returnDict['writtenHeight'] = written.groups()[0]
		returnDict['writtenWidth'] = written.groups()[1]
		returnDict['units'] = written.groups()[2]
	else:
		returnDict['writtenHeight'] = None
		returnDict['writtenWidth'] = None
		returnDict['units'] = None
	
	if bounddimpat.search(dimString):
		bound = bounddimpat.search(dimString)
		returnDict['boundHeight'] = bound.groups()[0]
		returnDict['boundWidth'] = bound.groups()[1]
	else:
		returnDict['boundHeight'] = None
		returnDict['boundWidth'] = None
	
	#appends units from end if there is not already a unit specified
	#may be worth revising this to see what's better
	if endunitpat.search(dimString):
		if returnDict['units'] == None:
			endunits = endunitpat.search(dimString)
			returnDict['units'] = endunits.groups()[0]
	
	#print(returnDict)
	return returnDict

def getPhysDesc(field300):
	#takes a ***string*** of field 300; returns dict of volumes, extent, dimensions, material
	#returns None if the field is for microfilm
	
	firstFlag = subfieldpat4.search(field300).groups()
	if firstFlag[0] == '|3':
		if re.search('[Cc]opy', firstFlag[1]):
			#immediately return None if not original
			return None
		else:
			pass
	
	returnDict = {'volumeInfo': []}
	materials = None
	#get number of volumes; get extents of each from field formatted "2 v. (xxx, xxx)"
	if volspatt.search(field300):
		vols = volspatt.search(field300)
		#print(vols.groups())
		numVols = int(vols.group(1))
		returnDict['volumes'] = numVols
		#iterate over match groups to get extents of volumes
		for x in range(2, numVols+2):
			#print(int(vols.group(x)))
			#whole "extent" dictionary gets appended to instantiate "volume info" -- other non-"extent" info added later
			#this covers "extent" for multi-volume MSS
			holderDict = {'extent': int(vols.group(x)), 'extentUnit': vols.group(4)}
			returnDict['volumeInfo'].append(holderDict)
	else:
		returnDict['volumes'] = 1
		returnDict['volumeInfo'].append({})
		

	splitfields = mat_subfieldpat.findall(field300)
	#divide field into subfield flag, value tuples
	for subfield in splitfields:
		#if there is an extent subfield that hasn't already been harvested by volspatt, get it
		if (subfield[0] == '|a') and (returnDict['volumes'] ==1):
			#this covers "extent" for single-volume MSS
			#print 'a'
			#print('proposed extent: ', subfield[1].split(' ')[0].strip(':,;.[] '))
			#print('proposed extent unit: ', subfield[1].split(' ')[1].strip(' :,;[]'))
			if len(returnDict['volumeInfo']) == 0:
				holderDict = {'extent': int(subfield[1].split(' ')[0].strip(':,;.[] ')), 'extentUnit': subfield[1].split(' ')[1].strip(' :,;[]')}
				#returnDict['volumeInfo'].append({'extent': int(subfield[1].strip(' :,;'))})
				returnDict['volumeInfo'].append(holderDict)
			else:
				returnDict['volumeInfo'][0]['extent'] = int(subfield[1].split(' ')[0].strip(':,;.[] '))
				returnDict['volumeInfo'][0]['extentUnit'] = subfield[1].split(' ')[1].strip(' :,;[]')
		#find support
		elif subfield[0] == '|b':
			#print 'b'
			returnDict['support'] = subfield[1].strip(' :,;')
		#try to retrieve dimensions, assign to each volume;
		#set all to "none" if unable to retrieve
		elif subfield[0] == '|c':
			#print 'c'
			dimensions = subfield[1]
			
			#print(returnDict['volumeInfo'])
			
			for codex in returnDict['volumeInfo']:
			#iterate over 'volumeInfo' dicts of volume-specific information
			#get dimensions
			#check for missing extent and add if necessary
				try:
					dimensionDict = getDimensions(dimensions)
					for item in dimensionDict:
						codex[item] = dimensionDict[item]
						#returnDict[item] = dimensionDict[item]
				except:
					print('weird error with dimensions')
					codex['supportHeight'] = None
					codex['supportWidth'] = None
					codex['boundHeight'] = None
					codex['boundWidth'] = None
					codex['writtenHeight'] = None
					codex['writtenWidth'] = None
					codex['units'] = None


				#extent
				if 'extent' not in codex:
					extSegment = field300.split('|')[0].strip(' :,;')
					try:
						codex['extent'] = int(extSegment.split(' ')[0])
						codex['extentUnit'] = extSegment.split(' ')[1]
					except:
						print 'Failed to get extent'
						codex['extent'] = None
						codex['extentUnit'] = None

	if 'support' not in returnDict:
		returnDict['support'] = None

	if re.search('\|c', field300) == None:
		#couldn't find subfield flag for dimensions; set to none to avoid key error
		#need to iterate over volumes to ensure proper placement in dictionary
		#replace later with more granular search/replacement if possible
		for codex in returnDict['volumeInfo']:
			codex['supportHeight'] = None
			codex['supportWidth'] = None
			codex['boundHeight'] = None
			codex['boundWidth'] = None
			codex['writtenHeight'] = None
			codex['writtenWidth'] = None
			codex['units'] = None

		
	return returnDict

def getLayout(field500Layout):
	#take MARC AMREMM 500 "layout"
	#return numbers of lines and ruling materials
	returndict = {'lines': [], 'ruling': []}
	if linepat.search(field500Layout):
		for linenumber in linepat.findall(field500Layout):
			if (linenumber != '') and (str.isdigit(str(linenumber))):
				returndict['lines'].append(int(linenumber))
			else:
				if '-' in linenumber:
					for section in linenumber.split('-'):
						if section != '':
							returndict['lines'].append(int(section))

	if rulingpat.search(field500Layout):
		for rule in rulingpat.findall(field500Layout):
			for ruletype in rulingList:
				if ruletype in rule[3]:
					returndict['ruling'].append(ruletype)
			if 'drypoint' in rule[3]:
				returndict['ruling'].append('dry point')
			if 'hardpoint' in rule[3]:
				returndict['ruling'].append('hard point')
			if 'pen' in rule[3]:
				returndict['ruling'].append('ink')
	return returndict




def getWaterMarks(field500Coll):
#takes 500 Collation field, returns list of tuples (Briquet number - Briquet name - URL: 
#refers to defs splitnumbers, getBriq (both immediately below)


	#print('getting watermarks')
	if briqpat.search(field500Coll):
		#if there are watermarks, create list and get all of them
		watermarknums = []
		wms = briqpat.findall(field500Coll)

		for wm in wms:
			#iterate over watermarks, split if necessary and append to list
			if wm[1] !='':
				#wm[1] is the number
				for output_num in splitnumbers(wm[1]):
					#LIVE CALL TO REMOTE SERVER!!!
					retrievedInfo = getBriq(output_num)
					watermarknums.append((int(output_num), retrievedInfo[0], retrievedInfo[1]))
		return watermarknums

	else:
		return None


def splitnumbers(input_num):
#Takes a number, determines if it's a range, and returns all constituent numbers,
#correcting for abbreviations in watermark listings
	if '-' in input_num:
		multiples = input_num.split('-')
		if len(multiples[1])<len(multiples[0]):
			multiples[1] = multiples[0][0:len(multiples[0])-len(multiples[1])] + multiples[1]
		return multiples
	else:
		resultslist=[]
		resultslist.append(input_num)
		return resultslist

def getBriq(number):
	"""Takes Briquet number, returns tuple of name and address from Briquet Online"""
	baseurl = 'http://www.ksbm.oeaw.ac.at/_scripts/php/loadRepWmark.php?rep=briquet&refnr='
	endurl = '&lang=fr'
	targeturl = baseurl + number + endurl
	
	##Set 1: actual request to server (comment out to avoid)
	##
	print 'Briquet request fired'
	page = urlopen(targeturl)
	soup = BeautifulSoup(page, "html.parser")
	motiftext = soup.find('td', class_='wm_text').get_text()
	return (motifpatt.search(motiftext).group(1).strip(), targeturl)
	##

	##Set 2: Don't make server call, return dummy name
	##
	#print 'Simulated Briquet request fired'
	#return ('dummyname', targeturl)
	##

def get_person_dates(datestring):
	returnDict = {'date1': None, 'date2': None, 'datetype': None}
	"""Take 'd' string from 100, 600, or 700 record,
	strip symbols,
	and return start and end dates (if applicable) and
	date type"""
	#check for centuries
	cents = centurypat.findall(datestring)
	if len(cents) >0:
		returnDict['date1'] = int(cents[0] + '00')
		returnDict['datetype'] = 'century'
		if len(cents) == 2:
			returnDict['date2'] = int(cents[1] + '00')
		return returnDict
	
	#check for range of dates
	twodates = twodate.search(datestring)
	if twodates != None:
		#get dates
		returnDict['date1'] = int(twodates.group('date1'))
		returnDict['date2'] = int(twodates.group('date2'))
		#assign date type; check for markers of approximation
		if ((twodate.search(datestring).group('ca1')) 
			or (twodate.search(datestring).group('ca2')) 
			or re.search('[Aa]pprox(imately)?', datestring) 
			or re.search(' or ', datestring)
			or ('?' in datestring)):
			returnDict['datetype'] = 'approx'
		#check for markers of professional dates
		elif re.search('[Aa]ctive', datestring) or re.search('^[Ff]l\.', datestring):
			returnDict['datetype'] = 'profess'
		else:
			returnDict['datetype'] = 'life'
		return returnDict
	
	#if one date, determine type of date
	elif onedate.search(datestring):
		singledate = int(onedate.search(datestring).group('date1'))
		if (re.search(r'^ca\.', datestring)) or (re.search('[Aa]pprox(imately)?', datestring)) or ('?' in datestring):
			returnDict['datetype'] = 'approx'
		elif re.search('[Aa]ctive', datestring) or re.search('^[Ff]l\.', datestring):
			returnDict['datetype'] = 'profess'
		else:
			returnDict['datetype'] = 'life'
		
		if (re.match(r'^-[0-9]{3,4}', datestring) or re.search('^d\.', datestring)):
			returnDict['date2'] = singledate
		elif re.search(r'b\.', datestring) or re.match(r'[0-9]{3,4}-(\?|$)', datestring):
			returnDict['date1'] = singledate
		return returnDict
			
	else:
		return returnDict

def parsePerson(personField):
    """Takes a 100, 600, or 700 field and returns structured information about a person"""
    stubName = (personField.split('|')[0]).strip(',. ')
    
    returnDict = {'Numeration': None, 'Title': None,'Fullname': None, 'displayName': None,
    'date1': None, 'date2': None,'datetype': None, 'relationship': []}

    for attribute in subfieldpat4.findall(personField):
        if attribute[0] == '|b':
            returnDict['Numeration'] = attribute[1].strip(', .')
        elif attribute[0] == '|c':
            returnDict['Title'] = attribute[1].strip(', .')
        elif attribute[0] == '|d':
            datedict = get_person_dates(attribute[1])
            for date_att in datedict:
                returnDict[date_att] = datedict[date_att]
        elif attribute[0] == '|q':
            returnDict['Fullname'] = attribute[1].strip(', .()')
        elif (attribute[0] == '|t') or (attribute[0] == '|5') or (attribute[0] == '|v'): 
            pass
        elif (attribute[0] == '|e') or (attribute[0] == '|4'):
            #see if 'relationship' is in LOC relationship codes table, retrieve if so
            if str(attribute[1].strip()) in relCodesDict:
                returnDict['relationship'].append(relCodesDict[str(attribute[1].strip())])
            #if not, just add as is
            else:
                returnDict['relationship'].append(str(attribute[1].strip()))

    mainName = stubName
    if returnDict['Numeration'] != None:
        mainName = mainName + ' ' + returnDict['Numeration']
    if returnDict['Title'] != None:
        mainName = mainName + ', ' + returnDict['Title']
    
    if ',' in stubName:
        returnDict['displayName'] = stubName.split(',')[1].strip(' .,') + ' ' + stubName.split(',')[0].strip(' .,')
    if (returnDict['Fullname'] != None) and (returnDict['displayName'] != None):
        returnDict['displayName'] = returnDict['displayName'] + ' (' + returnDict['Fullname']+ ')'
    if (returnDict['Numeration'] != None) and (returnDict['displayName'] != None):
        returnDict['displayName'] = returnDict['displayName'] + ' ' + returnDict['Numeration']
    if (returnDict['Title'] != None) and (returnDict['displayName'] != None):
        returnDict['displayName'] = returnDict['displayName'] + ', ' + returnDict['Title']
    if returnDict['displayName'] == None:
        returnDict['displayName'] = mainName
    return (mainName, returnDict)

def parseOrg(orgField, fieldType):
	"""Takes 110, 610, or 710 field and returns a (name/key, info dict) tuple"""
	key = orgField.split('|')[0].strip('., ')
	returndict = {'subord_org': False, 'relator': None}
	if fieldType == '110':
		returndict['relator'] = 'author'
	elif fieldType == '610':
		returndict['relator'] = 'subject'
	elif fieldType == '710':
		returndict['relator'] = 'associated name'
		#Add general "associated name" relationship, but overwrite it later if more specific info appears
	
	if subfieldpat.search(orgField):
		for attribute in subfieldpat4.findall(orgField):
			if attribute[0] == '|b':
				returndict['subord_org'] = True
				returndict['relator'] = attribute[1].strip(',. ')
			elif ((attribute[0] == '|4') and (attribute[1].strip('., ') != 'asn')):
				returndict['relator'] = relCodesDict[attribute[1].strip('., ')]

	else:
		key = orgField.strip('., ')	
	
	return(key, returndict)

def parseContentsCoarse(inputString, matchList):
	#Takes a string of unstructured contents, list of RE matches, and REs for subfields, final numbers, and front-back trimming
	#Returns a list of dictionaries with key=foliation, value=contents
	contentsList = []
	for x in range(0, len(matchList)):
		key = matchList[x].group(0)
		start = matchList[x].end()
		if len(matchList) - x >=2:
			end = matchList[x+1].start()
		else:
			end = len(inputString)
		#eliminate numbers at end
		numberTrimmed = re.sub(trailnumpat, '', inputString[start:end])
		#eliminate subfield markers
		sectionString = re.sub(subfieldpat, '', numberTrimmed)
		#get rid of leading punctuation
		frontTrimmed = re.sub(beginpat, '', sectionString)
		#get rid of unnecessary characters at the end
		outputString = re.sub(endpat, '', frontTrimmed)
		#switch 'blank' to correct field if it's been wrongly assigned
		if key[-3:] == 'bla':
			key = key[:-4]
			outputString = 'bla' + outputString
		contentsList.append({key: outputString})
	return contentsList

def parseContentsFine(folia):
	#Takes string foliation of contents item and returns range of folia and sides
	returnDict = {'startFol': None, 'startSide': None, 'endFol': None, 'endSide': None}
	folnums = [match for match in re.finditer(r'(?P<num>[0-9]+)(?P<side>[rv]?)', folia)]
	#issue here: can't decide between grabbing 'verso' into greedy Roman numeral pattern, or ignoring Roman
	#numeral foliation...leaving out Roman numerals for now.  
	#find matches of <number><side> pattern ,e.g. "12v" or "149r"

	if len(folnums)==0:
		print 'ERROR'
		print(folia)

	#add beginning leaf and side; should be in all
	if len(folnums) >=1:
		if folnums[0].group('num'):
			returnDict['startFol'] = int(folnums[0].group('num'))
		
		if folnums[0].group('side'):
			returnDict['startSide'] = folnums[0].group('side')

	#add ending leaf and side, if there is one
	if len(folnums) >1:
		if folnums[1].group('num'):
			returnDict['endFol'] = int(folnums[1].group('num'))
		
		if folnums[1].group('side'):
			returnDict['endSide'] = folnums[1].group('side')
	return returnDict

def insert_space_before_punct(s):
    #Wenqin's from NLP final project
    s = re.sub(r'([.,!?;:")(])', r' \1', s)
    return s

def getSubjects(subj_type, fieldData):
    returndict = {'subj_type': subj_type,
                  'subj_name': fieldData.split('|')[0].strip('., '),
                  'form': [],
                  'topic': [],
                  'chronology': [],
                  'place': []}
    subfields = subfieldpat4.findall(fieldData)
    for subfield in subfields:
        if subfield[0] == '|v':
            returndict['form'].append(subfield[1])
        elif subfield[0] == '|x':
            returndict['topic'].append(subfield[1])
        elif subfield[0] == '|y':
            returndict['chronology'].append(subfield[1])
        elif subfield[0] == '|z':
            returndict['place'].append(subfield[1])
    return returndict

#########################################################
#########################################################
#########################################################

#chief function that calls all the other functions:

def load(recs):
	outputdict = {}

	#iterate over all records in JSON file
	for record in recs:
		#print(record)
		#create dictionary for each one, populated with initial empty arrays for multiple values(external entities)
		#add none for all values to avoid key errors
		outputdict[record] = {'shelfmark': None, 'volumes': None, 'language': None, 'date1': None, 'externaldocs': [],
		'date2': None, 'datetype': None, 'datecertain': True, 'places': [], 'format': None, 'decoration': None, 'binding': None,
		'titles': [], 'people': {}, 'organizations': {}, 'contents': [], 'summary': None, 'origin': None, 'ownership_history': None,
		'subjects': [], 'ds_url': None}
		

		#get structured data from field 008
		#print(record)
		structuredData = getStructuredData(recs[record]['008'][0])
		#iterate over components retrieved from 008
		for infoComp in structuredData:
			#'country' is treated differently: need to get latitude and longitude
			if (infoComp == 'country') and (structuredData[infoComp] != None):
				if structuredData[infoComp] in placeCache:
					#check to see whether it's in the cache first to avoid unnecessary server call
					print 'place cache hit'
					outputdict[record]['places'].append(placeCache[structuredData[infoComp]])
				else:
					#get coords from server
					place008 = {'name': structuredData[infoComp], 'type': 'country'}
					###LIVE CALL TO SERVER
					place008coords = get_coords(place008['name'])
					place008['lat'] = place008coords['lat']
					place008['lon'] = place008coords['lon']
					#add to output dict, and add to cache
					outputdict[record]['places'].append(place008)
					placeCache[place008['name']] = place008

			elif (infoComp == 'country') and (structuredData[infoComp] == None):
				pass
			#other info components go straight into output dict
			else:
				outputdict[record][infoComp] = structuredData[infoComp]
		

		#iterate over fields and get all information
		#sort keys to ensure prerequisite information is available when needed
		for field in sorted(recs[record]):

			
			#get shelfmark
			if '090' in field:
				outputdict[record]['shelfmark'] = recs[record][field][0].strip('.; ,')
			elif '099' in field:
				outputdict[record]['shelfmark'] = recs[record][field][0].strip('.; ,')

			#get place data
			if ('260' in field):
				#feed field 260 and country into function
				locInfo = getPlace(recs[record][field][0], 
					countryCodesDict[recs[record]['008'][0][15:18].strip()])
				
				if locInfo != None:
					for loc in locInfo['places']:
						outputdict[record]['places'].append(loc)
				
				if pubpatt.search(field):
				#assign publisher, if any, to 'organizations' with same structure as that data element (for fields 110, 610, 710)
				#assign LOC relator for "publisher"
					outputdict[record]['organizations'][pubpatt.search(field).group().strip('., ')] = {'subord_org': False, 'relator': 'publisher'} 
				

				#see if there are markers of uncertainty in the date, and adjust accordingly
				#this sets the "dateCertain" value to True or False
				#determines how the date is displayed in the manuscript view page, msview.html c. line 33
				try:
					date260 = recs[record][field][0].split('|c')[1]
					if(('?' in date260) or ('--' in date260) or ('ca.' in date260) or ('cent' in date260)):
						dateCertain = False
				except:
					#if the pattern doesn't work, remains "true" by default
					pass

			#get titles	
			if ('240' in field) or ('245' in field):
				title_cand = getTitles(recs[record][field][0], field[:3])
				if title_cand[0] == 'title':
					outputdict[record]['titles'].append({'type': 'main', 'text': title_cand[1]})
				elif title_cand[0] == 'title_uni':
					outputdict[record]['titles'].append({'type': 'uniform', 'text': title_cand[1]})

			if '246' in field:
				for vartitle in recs[record][field]:
					title_cand = getTitles(vartitle, field[:3])
					if title_cand[0] == 'title_sec_folio':
						outputdict[record]['titles'].append({'type': 'secundo', 'text': title_cand[1]})
					else:
						outputdict[record]['titles'].append({'type': 'varying', 'text': title_cand[1]})

			
			#get number of volumes, extent, dimensions, material from field 300
			#place into 
			if '300' in field:
				for materials in recs[record][field]:
					physical = getPhysDesc(materials)
					if physical != None:
						for physAttribute in physical:
							outputdict[record][physAttribute] = physical[physAttribute]
			

			#get AMREMM note field descriptions from fields 500
############			
			if '500' in field:
				#handle  volume-sensitive ones; iterate over volumes in volumeInfo list

				for volnum in range(1, outputdict[record]['volumes'] +1):
					#print(volnum)
					for descItem in recs[record][field]:

						if descItem[:3] == 'Ms.':
							formatfield = descItem[3:].strip('. ')
							if formatfield[-1] == 's':
								formatfield = formatfield[:-1]
							outputdict[record]['format'] = formatfield

						if descItem[:8] == 'Origin: ':
							outputdict[record]['origin'] = descItem[8:]

						if descItem[:11] == 'Decoration:':
							outputdict[record]['decoration'] = descItem[11:]

						if descItem[:8] == 'Binding:':
							outputdict[record]['binding'] = descItem[8:]
						
						#nest this: first "Collation"; if there are multiple volumes, check for "volume"
						if ('Collation' in descItem):
							volind = re.search('Volume ([0-9])', descItem)

							if volind != None:
							#this branch will activate if there are multiple volumes and there is a volume indicator
								if int(volind.group(1)) != volnum:
								#skip -- this field is not applicable to the current volume
									pass
								else:
									#this belongs to the current volume in the iteration
									#get watermarks, register of quires, arrangement, script
									mswms = getWaterMarks(descItem)
									if mswms != None:
										outputdict[record]['volumeInfo'][volnum-1]['watermarks'] = mswms
									else:
										outputdict[record]['volumeInfo'][volnum-1]['watermarks'] = []

									if quirepat.search(descItem):
										outputdict[record]['volumeInfo'][volnum-1]['quires'] = ' '.join(quirepat.findall(descItem))
									else:
										outputdict[record]['volumeInfo'][volnum-1]['quires'] = None

									if folpatt.search(descItem): 
										outputdict[record]['volumeInfo'][volnum-1]['arrangement'] = folpatt.search(descItem).group(0)
									else:
										outputdict[record]['volumeInfo'][volnum-1]['arrangement'] = None


							else:
							#no volume indicator: applicable to both or only volume
								if len(outputdict[record]['volumeInfo']) == 0:
								#add volumeInfo field if there is none
									outputdict[record]['volumeInfo'].append({})
								

								mswms = getWaterMarks(descItem)
								if mswms != None:
									#if there are watermarks, assign to record
									outputdict[record]['volumeInfo'][volnum-1]['watermarks'] = mswms
								else:
									#otherwise, add blank list
									outputdict[record]['volumeInfo'][volnum-1]['watermarks'] = []


								if quirepat.search(descItem):
									#add register of quires, if present
									
									outputdict[record]['volumeInfo'][volnum-1]['quires'] = ' '.join(quirepat.findall(descItem))
								else:
									outputdict[record]['volumeInfo'][volnum-1]['quires'] = None

								#add arrangement if present
								if folpatt.search(descItem): 
									outputdict[record]['volumeInfo'][volnum-1]['arrangement'] = folpatt.search(descItem).group(0)
								else:
									outputdict[record]['volumeInfo'][volnum-1]['arrangement'] = None

						if 'Script' in descItem:
							volind = re.search('Volume ([0-9])', descItem)
							if volind != None:
							#this branch will activate if there are multiple volumes and there is a volume indicator
								if int(volind.group(1)) != volnum:
								#skip -- this field is not applicable to the current volume
									pass
								else:
									#this belongs to the current volume in the iteration -- get script
									#get narrative script description
									outputdict[record]['volumeInfo'][volnum-1]['narr_script'] = descItem[8:]
									outputdict[record]['volumeInfo'][volnum-1]['script'] = []

									#get scripts from controlled vocab; first hyphenated ones
									scriptinput = insert_space_before_punct(descItem)
									scripttokens_space = scriptinput.split(' ')
									for scripttoken in scripttokens_space:
										if ((scripttoken.lower() in scriptDict['hyphen']) and (scripttoken.lower() not in outputdict[record]['volumeInfo'][volnum-1]['script'])):
											outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptDict['hyphen'][scripttoken.lower()])

									#then others
									scripttokens_other = re.split(' |-', scriptinput)
									for scripttoken in scripttokens_other:
										if ((scripttoken.lower() in scriptDict['other']) and (scripttoken.lower() not in outputdict[record]['volumeInfo'][volnum-1]['script'])):
											outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptDict['other'][scripttoken.lower()])

									#old script extraction method
									'''
									if scriptpat.search(descItem):
										outputdict[record]['volumeInfo'][volnum-1]['script'] = []
										for scriptInstance in scriptpat.findall(descItem):
											if (re.search('[,;:.]', scriptInstance[0])) and (len(scriptInstance[0].split())>5):
												outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptInstance[0][:re.search('[,;:.]', scriptInstance[0]).start()])
											else:
												outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptInstance[0].strip(' '))
									else:
										outputdict[record]['volumeInfo'][volnum-1]['script'] = []
									'''
							else:
								#no volume indicator: applicable to both or only volume
								outputdict[record]['volumeInfo'][volnum-1]['narr_script'] = descItem[8:]
								outputdict[record]['volumeInfo'][volnum-1]['script'] = []
								#get scripts from controlled vocab; first hyphenated ones
								scriptinput = insert_space_before_punct(descItem)
								scripttokens_space = scriptinput.split(' ')
								for scripttoken in scripttokens_space:
									if ((scripttoken.lower() in scriptDict['hyphen']) and (scripttoken.lower() not in outputdict[record]['volumeInfo'][volnum-1]['script'])):
										outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptDict['hyphen'][scripttoken.lower()])

								#then others
								scripttokens_other = re.split(' |-', scriptinput)
								for scripttoken in scripttokens_other:
									if ((scripttoken.lower() in scriptDict['other']) and (scripttoken.lower() not in outputdict[record]['volumeInfo'][volnum-1]['script'])):
										outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptDict['other'][scripttoken.lower()])



								#old script extraction method:
								'''
								outputdict[record]['volumeInfo'][volnum-1]['script'] = []
								for scriptInstance in scriptpat.findall(descItem):
									if (re.search('[,:;.]', scriptInstance[0])) and (len(scriptInstance[0].split())>5):
										outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptInstance[0][:re.search('[,;:.]', scriptInstance[0]).start()])
									else:
										outputdict[record]['volumeInfo'][volnum-1]['script'].append(scriptInstance[0].strip(' '))
								'''
						if 'Layout' in descItem:
							volind = re.search('Volume ([0-9])', descItem)
							if volind != None:
							#this branch will activate if there are multiple volumes and there is a volume indicator
								if int(volind.group(1)) != volnum:
								#skip -- this field is not applicable to the current volume
									pass
								else:
									#this belongs to the current volume in the iteration -- get layout info
									volLayout = getLayout(descItem)
									outputdict[record]['volumeInfo'][volnum-1]['ruling'] = volLayout['ruling']
									outputdict[record]['volumeInfo'][volnum-1]['lines'] = volLayout['lines']

							else:
								#no volume indicator: applicable to both or only volume
								volLayout = getLayout(descItem)
								outputdict[record]['volumeInfo'][volnum-1]['ruling'] = volLayout['ruling']
								outputdict[record]['volumeInfo'][volnum-1]['lines'] = volLayout['lines'] 


			#get person info from relevant main entry, subject, or added entry fields
			if ('100' in field) or ('600' in field) or ('700' in field):
				for personInstance in recs[record][field]:
					personData  = parsePerson(personInstance)
					#returns a tuple where 0 is the "main name" and 1 is the dictionary of retrieved values
					
					if ('100' in field) and (len(personData[1]['relationship']) == 0):
						personData[1]['relationship'].append('author')
					elif ('600' in field) and (len(personData[1]['relationship']) == 0):
						personData[1]['relationship'].append('subject')
					elif ('700' in field) and (len(personData[1]['relationship']) == 0):
						personData[1]['relationship'].append('associated name')

					outputdict[record]['people'][personData[0]] = personData[1]

			#get organization data
			if ('110' in field) or ('610' in field) or ('710' in field):
				for orgInstance in recs[record][field]:
					orgData = parseOrg(orgInstance, field[:3])
					outputdict[record]['organizations'][orgData[0]] = orgData[1]



			

			
			if '505' in field:
				#print(recs[record][field])
				#get content items (specifically listed textual elements with foliation and titles)
				#contentsHolder declared in outermost loop, because there may be multiple 505 fields
				
				#see if there are separate items by volume;
				

				for contentChunk in recs[record][field]:
					#set volume index (to determine what volume to assign contents to) to 0 by default
					volIndex = 0
					if re.search(r'^[Vv]olume (?P<number>[0-9IV])', contentChunk):
						#print(re.search(r'^[Vv]olume (?P<number>[0-9IV])', contentChunk).group('number'))
						contentsVolIndex = re.search(r'^[Vv]olume (?P<number>[0-9IV])', contentChunk).group('number')
						try:
						#get relevant volume number if Arabic numeral
							volIndex = int(contentsVolIndex) -1
						except ValueError:
							#if Roman numeral, try to get corresponding Arabic
							if contentsVolIndex in numerals:
								volIndex = numerals[contentsVolIndex] -1
							#otherwise, remains at default of zero
							
					#contentChunk: one item in the field 505 list, which may contain one or more content items
					matches = [result for result in contentspat.finditer(contentChunk)]
					smallContentsList = parseContentsCoarse(contentChunk, matches)
					
					for text in smallContentsList:
						for key in text:
							contentsHolder = {}
							contentsHolder['text'] = text[key]
							pagerange = parseContentsFine(key)
							for pageItem in pagerange:
								contentsHolder[pageItem] = pagerange[pageItem]
							#print(parseContentsFine(key))
							if 'contents' in outputdict[record]['volumeInfo'][volIndex]:
								outputdict[record]['volumeInfo'][volIndex]['contents'].append(contentsHolder)
							else:
								outputdict[record]['volumeInfo'][volIndex]['contents'] = [contentsHolder]
							

			if '520' in field:
				if len(recs[record][field]) >1:
					print('Multiple 520!!!')
				outputdict[record]['summary'] = recs[record][field][0]

			if '561' in field:
				if len(recs[record][field]) >1:
					print('Multiple 561!!!')
				outputdict[record]['ownership_history'] = recs[record][field][0]

			if field[:3] in {'611', '630', '650', '651', '655'}:
				for subjectinstance in recs[record][field]:
					outputdict[record]['subjects'].append(getSubjects(subj_field_types[field[:3]], subjectinstance))

			if '856' in field:
				url = re.search(r'(\|u)(.*$)', recs[record][field][0]).group(2)
				url = re.sub(' ', '', url)
				outputdict[record]['ds_url'] = url

############
#^top-level MARC field indent depth


		#sanity check for volume info and collation; should break this out later to separate function
		
		#print outputdict[record]['volumeInfo']
		
		#print '\n'

		if 'volumeInfo' not in outputdict[record]:
			outputdict[record]['volumeInfo'] = []
			#print(record, ': MISSING VOLUME INFO')
		


		for volumeItem in outputdict[record]['volumeInfo']:
			#print volumeItem['decoration']
			#print volumeItem['binding']
			for component in ['quires', 'arrangement','decoration', 'binding', 'narr_script']:
				if component not in volumeItem:
					volumeItem[component] = None;
			for listComponent in ['watermarks', 'contents', 'script', 'lines', 'ruling']:
				if listComponent not in volumeItem:
					volumeItem[listComponent] = []
			
	return outputdict


	
						
								

		
#results = load(sourcedict)

#for x in results:
#	print(results[x])
	#for vol in outputdict[x]['volumeInfo']:
	#	if 'watermarks' in vol:
			
			#for wm in vol['watermarks']:
				#EXTERNAL HTTP REQUEST: ONLY UNCOMMENT BELOW IF SERIOUS
				#print(getBriq(str(wm)))

	#	if ('watermarks' in vol) and (len(vol['watermarks']) >0):
	#		print(outputdict[x]['volumeInfo'])
	#print(outputdict[x]['volumes'])
	#print('\n')
	#if len(outputdict[x]['volumeInfo']) ==0:
	

