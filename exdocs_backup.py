import json, os
from app import db, models

relpath = os.path.dirname(__file__)

option = raw_input('Enter _I_ to import external docs from a backup file to a database, _X_ to export them to a file: ')

if option.upper() == 'I':
	sourcefilename = raw_input('Enter the name of the file to load from: ')
	sourcefile = open(sourcefilename, 'r')
	data = json.load(sourcefile)
	sourcefile.close()

	for work in data['works']:
		newwork = models.external_work(
			id = int(work),
			work_title = data['works'][work]['title'],
			work_publisher = data['works'][work]['publisher'],
			work_location = data['works'][work]['location']
			)
		db.session.add(newwork)
		db.session.commit()

	for doc in data['docs']:
		try:
			newdoc = models.external_doc(
				id = int(doc),
				doc_title = data['docs'][doc]['title'],
				doc_author = data['docs'][doc]['author'],
				doc_year = data['docs'][doc]['year'],
				doc_volume = data['docs'][doc]['volume'],
				doc_issue = data['docs'][doc]['issue'],
				doc_page_range = data['docs'][doc]['page_range'],
				doc_notes = data['docs'][doc]['notes'],
				work_id = int(data['docs'][doc]['assoc_work']),
				mss = [models.manuscript.query.get(int(shelfmark)) for shelfmark in data['docs'][doc]['mss']]
				)
			db.session.add(newdoc)
			db.session.commit()
		except:
			print 'IMPORT FAILED'
			for x in doc:
				print x, doc[x]

elif option.upper() == 'X':
	outputname = raw_input('Name your backup file (no suffix): ')
	outputname = outputname + '.json'

	#get all works and put into dict
	allworks = models.external_work.query.all()
	worksoutput = {}
	for work in allworks:
		worksoutput[work.id] = {
		'title': work.work_title, 
		'publisher': work.work_publisher, 
		'location': work.work_location
		}

	#get all docs and put into dict
	alldocs = models.external_doc.query.all()
	docsoutput = {}
	for doc in alldocs:
		docsoutput[doc.id] = {
		'title': doc.doc_title,
		'author': doc.doc_author,
		'year': doc.doc_year,
		'volume': doc.doc_volume,
		'issue': doc.doc_issue,
		'page_range': doc.doc_page_range,
		'notes': doc.doc_notes,
		'assoc_work': doc.work_id,
		'mss': [ms.id for ms in doc.mss]
		}

	#print worksoutput
	#print docsoutput

	outputfile = open(outputname, 'w')
	json.dump({'works': worksoutput, 'docs': docsoutput}, outputfile)
	outputfile.close()