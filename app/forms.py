from flask.ext.wtf import Form
from wtforms import StringField, IntegerField, SelectField, SelectMultipleField, FloatField, PasswordField, TextAreaField, HiddenField, BooleanField
from flask_wtf.html5 import EmailField
from wtforms.validators import DataRequired, InputRequired

class MsForm(Form):
	shelfmark = StringField('shelfmark', validators=[DataRequired()])
	mstitle = StringField('mstitle', validators=[DataRequired()])
	mstitle_var = StringField('mstitle')

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
	ms_language = SelectField('language', coerce=int, validators=[DataRequired()])
	ms_summary = TextAreaField('summary')
	ms_ownership = TextAreaField('ownership_history')
	ms_origin = TextAreaField('origin')
	ms_decoration = TextAreaField('decoration')
	ms_binding = TextAreaField('binding')

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

###
class TitleForm(Form):
	ms_id = SelectField('ms_id', coerce=int)
	title_id = HiddenField('title_id')
	title_text = StringField('title_text')
	title_type = SelectField('title_type', choices = [('main', 'Main'), ('secundo', 'Secundo folio'), ('uniform', 'Uniform title'), ('varying', 'Varying')])

class WatermarkForm(Form):
	wmid = IntegerField('briquet_number')
	name = StringField('watermark_name')

class LanguageForm(Form):
	lang_id = HiddenField('lang_id')
	lang_name = StringField('lang_name')

class LineForm(Form):
	num_lines = IntegerField('num_lines')

class ScriptForm(Form):
	script_id = HiddenField('script_id')
	script_name = StringField('script_name')

class RulingForm(Form):
	ruling_id = HiddenField('script_id')
	ruling_type = StringField('ruling_type')

class PlaceForm(Form):
	place_id = HiddenField('place_id')
	place_name = StringField('place_name')
	place_type = SelectField('place_type', choices=[('area', 'City or region'), ('country', 'State or nation')])
	latitude = FloatField('latitude')
	longitude = FloatField('longitude')

class SubjectForm(Form):
	subect_id = HiddenField('subject_id')
	subject_name = StringField('subject_name')
	subject_type = SelectField('subject_type', choices = [('topic', 'Topical Term'), ('place', 'Geographical Term'), ('chronology', 'Chronological Term'), ('uniform title', 'Uniform Title'), ('form', 'Genre/Form'), ('meeting', 'Meeting Name')])


###
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

class NewUserForm(Form):
	username = StringField('username', validators=[DataRequired()])
	password_main = PasswordField('password_main', validators=[DataRequired()])
	password_check = PasswordField('password_check', validators=[DataRequired()])

class PasswordEditForm(Form):
	user_id = HiddenField('user_id')
	curr_password = PasswordField('password_main', validators=[DataRequired()])
	upd_password_main = PasswordField('password_main', validators=[DataRequired()])
	upd_password_check = PasswordField('password_check', validators=[DataRequired()])

class HometextForm(Form):
	text_content = TextAreaField('text_content')

