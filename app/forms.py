from flask.ext.wtf import Form
from wtforms import StringField, IntegerField, SelectField, SelectMultipleField, FloatField, PasswordField, TextAreaField, HiddenField
from flask_wtf.html5 import EmailField
from wtforms.validators import DataRequired, InputRequired

class MsForm(Form):
	shelfmark = StringField('shelfmark', validators=[DataRequired()])
	mstitle = StringField('mstitle', validators=[DataRequired()])
	mstitle_var = StringField('mstitle')


class SearchForm(Form):
	searchfield = StringField('query', validators=[DataRequired()])

class ExtDocForm(Form):
	ex_ref_ms = SelectMultipleField('ex_ref_ms', coerce=int, validators=[DataRequired()])
	#select shelfmark of MS referred to in work
	ex_main_title = SelectField('ex_main_title', coerce=int)
	#title of book or journal already in database
	ex_main_title_new = StringField('ex_main_title_new')
	#title of book or journal, if new
	ex_sub_title = StringField('ex_sub_title')
	#title of relevant article within journal or book chapter
	ex_author = StringField('ex_author')
	#author or authors of work
	ex_pub_volume = StringField('ex_pub_volume')
	#volume of multi-volume work or periodical
	ex_pub_issue = StringField('ex_pub_issue')
	#issue of periodical
	ex_page_range = StringField('ex_page_range')
	#extent of article or relevant pages within work
	ex_publisher = StringField('ex_publisher')
	ex_pub_loc = StringField('ex_pub_loc')
	#publisher location
	ex_pub_year = StringField('ex_doc_year', validators=[DataRequired()])
	#year(s) of publication; string, free format
	ex_pub_notes = StringField('ex_doc_notes')
	#additional explanatory notes on publication
	ex_id = HiddenField('ex_id')
	#holds key of existing document when updating DB; not used when creating new doc

class LoginForm(Form):
	username = StringField('username',  validators=[DataRequired()])
	userpassword = PasswordField('password', validators=[DataRequired()])

class ItemSelectForm(Form):
	item_to_edit = SelectField('item_to_edit', coerce=int, validators=[DataRequired()])
	#select shelfmark of MS referred to in work

class MsEditForm(Form):
	ms_id = HiddenField('ms_id')
	ms_format = StringField('ms_format')
	ms_date1 = IntegerField('date1')
	ms_date2 = IntegerField('date2')
	ms_datetype = SelectField('datetype', choices = [('q', 'Questionable date'),
		('s', 'Single known date/probable date'),
		('i', 'Inclusive dates of collection'), 
		('k', 'Range of years of bulk of collection'),
		('m', 'Multiple dates'),
		('b', 'No dates given;B.C. date'),
		('n', 'Dates unknown')])
	ms_language = StringField('language')
	ms_summary = TextAreaField('summary')
	ms_ownership = TextAreaField('ownership_history')
	ms_origin = TextAreaField('origin')
	ms_decoration = TextAreaField('decoration')
	ms_binding = TextAreaField('binding')
	#Things relating to other entities -- volumes, titles -- omitted for now

class VolEditForm(Form):
	vol_id = HiddenField('vol_id')
	numeration = IntegerField('numeration')
	support = StringField('support')
	extent = IntegerField('extent')
	extent_unit = StringField('extent_unit')
	bound_width = IntegerField('bound_width')
	bound_height = IntegerField('bound_height')
	leaf_width = IntegerField('leaf_width')
	leaf_height = IntegerField('leaf_height')
	written_width = IntegerField('written_width')
	written_height = IntegerField('written_height')
	size_unit = StringField('size_unit')
	quire_register = StringField('quire_register')
	phys_arrangement = StringField('phys_arrangement')
	scripts = SelectMultipleField('scripts', coerce=int)
	lines = SelectMultipleField('lines', coerce=int)
	ruling = SelectMultipleField('ruling', coerce=int)

class ContentEditForm(Form):
	item_id = HiddenField('item_id')
	fol_start_num = IntegerField('fol_start_num')
	fol_start_side = SelectField('fol_start_side', choices = [('v', 'Verso'), ('r', 'Recto')])
	fol_end_num = IntegerField('fol_end_num')
	fol_end_side = SelectField('fol_end_side', choices = [('v', 'Verso'), ('r', 'Recto')])
	fol_text = TextAreaField('content_item_text')

class FeedbackForm(Form):
	feedback_name = StringField('feedback_name')
	feedback_email = StringField('feedback_email')
	feedback_comment = TextAreaField('feedback_comment')

class ChartEditForm(Form):
	chart_id = HiddenField('chart_id')
	chart_title = StringField('chart_title')
	chart_y_label = StringField('chart_y_label')
	chart_x_label = StringField('chart_x_label')
	chart_text = TextAreaField('chart_text')
	chart_max_values = IntegerField('chart_max_values')
	people_chart_roles = SelectMultipleField('people_roles', coerce=int)

