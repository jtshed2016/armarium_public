from app import db

from sqlalchemy.types import TypeDecorator, Unicode

class CoerceUTF8(TypeDecorator):
    """Safely coerce Python bytestrings to Unicode
    before passing off to the database."""

    impl = Unicode

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            value = value.decode('utf-8')
        return value

#association table for a manuscript and a watermark (see below)
has_watermark = db.Table('has_watermark',
	db.Column('ms_id', db.Integer, db.ForeignKey('manuscript.id')),
	db.Column('wm_id', db.Integer, db.ForeignKey('watermark.id'))
	)

#association table for manuscript and place
has_place = db.Table('has_place',
	db.Column('ms_id', db.Integer, db.ForeignKey('manuscript.id')),
	db.Column('place_id', db.Integer, db.ForeignKey('place.id'))
	)

#association table for manuscript and external document
has_external_doc = db.Table('has_external_doc',
	db.Column('ms_id', db.Integer, db.ForeignKey('manuscript.id')),
	db.Column('art_id', db.Integer, db.ForeignKey('external_doc.id'))
	)


#association table for volume of a manuscript and number of lines
line_assoc = db.Table('line_assoc',
	db.Column('vol_id', db.Integer, db.ForeignKey('volume.id')),
	db.Column('num_lines', db.Integer, db.ForeignKey('lines.id'))
	)

#association table for a manuscript and the script in which it's written
ms_has_script = db.Table('ms_has_script',
	db.Column('ms_id', db.Integer, db.ForeignKey('manuscript.id')),
	db.Column('script_id', db.Integer, db.ForeignKey('script.id'))
	)

#association table for a volume and the script in which it's written
vol_has_script = db.Table('vol_has_script',
	db.Column('vol_id', db.Integer, db.ForeignKey('volume.id')),
	db.Column('script_id', db.Integer, db.ForeignKey('script.id'))
	)

#association table for a volume and the material used for ruling
has_ruling = db.Table('has_ruling',
	db.Column('vol_id', db.Integer, db.ForeignKey('volume.id')),
	db.Column('ruling_id', db.Integer, db.ForeignKey('ruling.id'))
	)


subdivision_assoc = db.Table('subdivision_assoc',
	db.Column('assoc_id', db.Integer, db.ForeignKey('ms_subject_assoc.id')),
	db.Column('sub_id', db.Integer, db.ForeignKey('subject.id')))


#the central entity of the system, representing a unified textual item
class manuscript(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	shelfmark = db.Column(db.String(15))
	ms_format = db.Column(db.String(20))
	date1 = db.Column(db.Integer)
	date2 = db.Column(db.Integer)
	datetype = db.Column(db.String(1))
	language = db.Column(db.Integer, db.ForeignKey('language.id'))
	summary = db.Column(db.String(1000))
	#520
	ownership_history = db.Column(db.String(1000))
	#561
	origin = db.Column(db.String(1000))
	decoration = db.Column(db.String(1000))
	binding = db.Column(db.String(1000))
	num_volumes = db.Column(db.Integer)
	catalog_url = db.Column(db.String(1000))
	ds_url = db.Column(db.String(1000))
	#relationships
	volumes = db.relationship('volume',
		cascade = 'delete, delete-orphan',
		backref = 'ms',
		lazy='dynamic')
	contents = db.relationship('content_item', 
		backref = 'ms', 
		lazy='dynamic')
	titles = db.relationship('title', 
		cascade = 'delete, delete-orphan',
		backref = 'ms', 
		lazy='dynamic'
		)
	watermarks = db.relationship('watermark',
		secondary = has_watermark,
		backref = db.backref('mss', lazy='dynamic')
		)
	assoc_people = db.relationship('person_ms_assoc',
		cascade = 'delete, delete-orphan',
		backref = 'ms',
		lazy='dynamic')
	places = db.relationship('place',
		secondary = has_place,
		backref = db.backref('mss', lazy='dynamic')
		)
	orgs = db.relationship('org_ms_assoc',
		cascade = 'delete, delete-orphan',
		backref= 'ms', 
		lazy='dynamic')
	treatments = db.relationship('external_doc',
		secondary=has_external_doc,
		backref = db.backref('mss', lazy='dynamic')
		)
	subjects = db.relationship('ms_subject_assoc',
		backref = 'ms', 
		lazy = 'dynamic'
		)

	def __repr__(self):
		return '<' + self.shelfmark + '>'

#the physical manifestation of a manuscript; there may be more than one
#for a multi-volume item
class volume(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	numeration = db.Column(db.Integer)
	support = db.Column(db.String(15)) 
	extent = db.Column(db.Integer)
	extent_unit = db.Column(db.String(3))
	bound_width = db.Column(db.Integer)
	bound_height = db.Column(db.Integer)
	leaf_width = db.Column(db.Integer)
	leaf_height = db.Column(db.Integer)
	written_width = db.Column(db.Integer)
	written_height = db.Column(db.Integer)
	size_unit = db.Column(db.String(3))
	quire_register = db.Column(db.String(60))
	phys_arrangement = db.Column(db.String(60))
	narr_script = db.Column(db.String(1000))
	#500 script, free text
	contents = db.relationship('content_item',
		cascade = 'delete, delete-orphan', 
		backref = 'volume', 
		lazy='dynamic')
	scripts = db.relationship('script',
		secondary = vol_has_script,
		backref= db.backref('mss', lazy='dynamic')
		)
	lines = db.relationship('lines',
		secondary=line_assoc, 
		backref = db.backref('volumes', lazy='dynamic')
		)
	ruling = db.relationship('ruling',
		secondary = has_ruling,
		backref = db.backref('volumes', lazy='dynamic')
		)

	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))

	def __repr__(self):
		return '<MS ' + str(self.ms_id) + ', Vol ' + str(self.numeration) + '>'
	

#a discrete textual item in a manuscript
class content_item(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.String(1000))
	fol_start_num = db.Column(db.Integer)
	fol_start_side = db.Column(db.String(1))
	fol_end_num = db.Column(db.Integer)
	fol_end_side = db.Column(db.String(1))

	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))
	vol_id = db.Column(db.Integer, db.ForeignKey('volume.id'))

	def __repr__(self):
		return '<Contents ' + str(self.id) + ', MS ' + str(self.ms_id) + '>'

#a person related to a manuscript or text
class person(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name_display = db.Column(db.String(200))
	##name_display is a friendlier format that contains 
	##first name, last name (if applicable), numeration, title, and
	##fuller name(subfield q, extension of initials) in parens
	name_main = db.Column(db.String(200))
	##name_simple is a string that uniquely identifies a person by
	##last name, first name, numeration, and title
	name_fuller = db.Column(db.String(200))
	##name_fuller is subfield q, fuller name or expansion of initials
	##not used in app
	year_1 = db.Column(db.Integer)
	year_2 = db.Column(db.Integer)
	##Years of life or professional activity, as indicated by datetype
	datetype = db.Column(db.Integer)
	##Type of dates: approx = approximate, life = dates of birth and death,
	#profess = span of professional activity, century = only century specified
	numeration = db.Column(db.String(20))
	title = db.Column(db.String(30))
	ms_relations = db.relationship('person_ms_assoc',
		cascade = 'delete, delete-orphan',
		backref = 'person', 
		lazy='dynamic')

	def __repr__(self):
		return '<Person ' + self.name_main + '>'

#an association between a person and a manuscript;
#rendered as a full model to capture nature of relationship
class person_ms_assoc(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))
	#assoc_type = db.Column(db.String(50))
	assoc_type = db.Column(db.Integer, db.ForeignKey('person_rel_type.id'))
	#role_relation = db.relationship('person_rel_type',
	#	backref = 'people',
	#	lazy='dynamic')

	def __repr__(self):
		return '<person_ms_assoc ' + str(self.id) + '>'

class person_rel_type(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(50))
	abbrev = db.Column(db.String(3))
	display = db.Column(db.Boolean)
	role_relation = db.relationship('person_ms_assoc',
		backref = 'relator_type',
		lazy = 'dynamic')


	def __repr__(self):
		return '<role ' + self.name + '>'
#an organization that is the subject, author, or publisher 
#of or otherwise associated with a manuscript, or a state
class organization(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	ms_relations = db.relationship('org_ms_assoc',
		cascade = 'delete, delete-orphan',
		backref='org',
		lazy='dynamic')

	def __repr__(self):
		return '<Org '+ self.name + '>'

#association between an organization entity and a manuscript, containing relationship info
class org_ms_assoc(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	org_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))
	relationship = db.Column(db.String(50))
	subord_org = db.Column(db.Boolean)

	def __repr__(self):
		return '<org_ms_assoc ' + str(self.id) + '>'



#title of a manuscript, whether main or alternate name/spelling
class title(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title_text = db.Column(db.String(150))
	title_type = db.Column(db.String(20))
	#possible values are main, uniform, varying, secundo folio
	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))

	def __repr__(self):
		return '<title ' + self.title_text + '>'

#a watermark in the manuscript's support
class watermark(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(40))
	url = db.Column(db.String(100))

	def __repr__(self):
		return '<watermark Briquet ' + self.name + str(self.id) + '>'

class place(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	place_name = db.Column(db.String(60))
	place_type = db.Column(db.String(10))
	lat = db.Column(db.Float)
	lon = db.Column(db.Float)

	def __repr__(self):
		return '<place ' + self.place_name + ' (' + self.place_type + ')>'

class external_doc(db.Model):
	#A specific section of an article, book chapter, or other item citing or based on
	#Robbins manuscript (as in MARC fields 510 and 581).  Relates to cited MS
	#(many-to-many) and to its containing work, such as a journal or title (many-to-many)
	id = db.Column(db.Integer, primary_key = True)
	doc_title = db.Column(db.String(200))
	doc_author = db.Column(db.String(200))
	doc_year = db.Column(db.String(20))
	doc_volume = db.Column(db.String(15))
	doc_issue = db.Column(db.String(15))
	doc_page_range = db.Column(db.String(15))
	#year, volume, issue, page range are free text to accommodate Roman numerals, ranges, etc.
	doc_notes = db.Column(db.String(1000))
	work_id = db.Column(db.Integer, db.ForeignKey('external_work.id'))

	def __repr__(self):
		return '<exdoc ' + str(self.id) + ' ' + self.doc_title[:50] + '>'


class external_work(db.Model):
	#A bibliographically distinct publication (monograph or journal) that is not a
	#Robbins MS but contains an article or chapter (entity external_doc) citing or describing one.
	id = db.Column(db.Integer, primary_key = True)
	work_title = db.Column(db.String(200))
	work_publisher = db.Column(db.String(200))
	work_location = db.Column(db.String(100))
	work_constituents = db.relationship('external_doc', backref = 'ex_work', lazy='dynamic')

	def __repr__(self):
		return '<exwork ' + str(self.id) + ' ' + self.work_title[:50] + '>'

class lines(db.Model):
	#the number of lines in which a manuscript is written
	#number of lines is the id since it's an int and this is a many-many
	#relationship with an association table
	id = db.Column(db.Integer, primary_key=True)

	def __repr__(self):
		return '<' + str(self.id) + '>'

class script(db.Model):
	#the script in which a manuscript is written
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(100))

	def __repr__(self):
		return '<script ' + self.name + '>'

class ruling(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(50))
	#method used for ruling the manuscript
	
	def __repr__(self):
		return '<ruling ' + self.name + '>'

#many manuscripts to one language
class language(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(60))
	mss = db.relationship('manuscript', 
		backref = 'ms_language',
		lazy='dynamic')

	def __repr__(self):
		return '<language ' + str(self.id) + ': ' + self.name + '>'

class ms_subject_assoc(db.Model):
	#association table to store main and subdivision subjects for MSS
	id = db.Column(db.Integer, primary_key=True)
	ms_id = db.Column(db.Integer, db.ForeignKey('manuscript.id'))
	main_subj_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
	subdivisions = db.relationship('subject', 
		secondary=subdivision_assoc, 
		backref=db.backref('ms_associations', lazy='dynamic'))

	def __repr__(self):
		return '<subject_assoc ' + str(self.id) + ' (MS' + str(self.ms_id) + ')>'

class subject(db.Model):
	#600 fields and subfields
	id = db.Column(db.Integer, primary_key=True)
	subj_name = db.Column(db.String(100))
	subj_type = db.Column(db.String(50))
	main_sub_relationship = db.relationship('ms_subject_assoc', 
		cascade = 'delete, delete-orphan',
		backref='subjects', 
		lazy='dynamic')
	
	#topic, place, meeting, uniform title, genre/form
	#organization, people subjects stored as those types

	def __repr__(self):
		return '<subject ' + self.subj_name + ' (' + self.subj_type + ')>'
	
class user(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String)
	hashed_pw = db.Column(db.String)
	salt = db.Column(db.String)

	def __repr__(self):
		return '<user ' + self.username + '>'

class chart(db.Model):
	#table that stores information for populating charts on the home page
	id = db.Column(db.Integer, primary_key = True)
	chartname = db.Column(db.String(30))
	title = db.Column(db.String(50))
	qualifier = db.Column(db.String(20))
	#unique, descriptive string appended to HTML IDs to make them unique per page
	x_axis_label = db.Column(db.String(50))
	y_axis_label = db.Column(db.String(50))
	urlpath = db.Column(db.String(50))
	displaytext = db.Column(db.String(1000))
	display = db.Column(db.Boolean)
	displayorder = db.Column(db.Integer)
	max_values = db.Column(db.Integer)


	def __repr__(self):
		return '<chart ' + self.chartname + '>'

class hometext(db.Model):
	#store info for welcome text on home page...really only needs one record
	id = db.Column(db.Integer, primary_key = True)
	displaytext = db.Column(db.String(1000))

	def __repr__(self):
		return '<hometext ' + str(self.id) + '>'

class comment(db.Model):
	#store comments left by users through feedback function
	id = db.Column(db.Integer, primary_key = True)
	commenter_name = db.Column(db.String(75))
	commenter_address = db.Column(db.String(75))
	comment_text = db.Column(db.String(1000))
	comment_date = db.Column(db.DateTime)
	comment_read = db.Column(db.Boolean)
