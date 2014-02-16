###############################################################################
import common

###############################################################################
SUBPREFIX = 'tmdb'

API_KEY = 'a3dc111e66105f6387e99393813ae4d5'

TMDB_CONFIG = None
TMDB_DATA   = {}

###############################################################################
def get_config():
	global TMDB_CONFIG

	if TMDB_CONFIG == None:
		TMDB_CONFIG = JSON.ObjectFromURL('http://api.themoviedb.org/3/configuration?api_key={0}'.format(API_KEY))
	return TMDB_CONFIG

###############################################################################
def get_data(imdb_id):
	global TMDB_DATA

	if not imdb_id in TMDB_DATA:
		TMDB_DATA[imdb_id] = JSON.ObjectFromURL('http://api.themoviedb.org/3/movie/{0}?api_key={1}&append_to_response=credits'.format(imdb_id, API_KEY))
	return TMDB_DATA[imdb_id]

###############################################################################
@route(common.PREFIX + '/' + SUBPREFIX + '/get_art')
def get_art(imdb_id):
	return Redirect(get_config()['images']['base_url'] + 'original' + get_data(imdb_id)['backdrop_path'])

###############################################################################
@route(common.PREFIX + '/' + SUBPREFIX + '/get_thumb')
def get_thumb(imdb_id):
	return Redirect(get_config()['images']['base_url'] + 'original' + get_data(imdb_id)['poster_path'])

###############################################################################
@route(common.PREFIX + '/' + SUBPREFIX + '/create_movie_object')
def create_movie_object(imdb_id):
	try:
		movie_data = get_data(imdb_id)
	except Exception as exception:
		Log.Error('[BitTorrent][tmdb] Unhandled exception: {0}'.format(exception))
		return

	movie_object = MovieObject()

	try:
		movie_object.duration = int(movie_data['runtime']) * 60 * 1000
		movie_object.title    = movie_data['title']
		movie_object.tagline  = movie_data['tagline']
		movie_object.summary  = movie_data['overview']
		movie_object.rating   = movie_data['vote_average']
		movie_object.art      = Callback(get_art, imdb_id=imdb_id)
		movie_object.thumb    = Callback(get_thumb, imdb_id=imdb_id)
	except:
		pass

	try:
		movie_object.originally_available_at = Datetime.ParseDate(movie_data['release_date']).date()
		movie_object.year                    = movie_object.originally_available_at.year
	except:
		pass
	
	try:
		movie_object.studio = movie_data['production_companies'][0]['name'].strip()
	except:
		pass

	movie_object.genres.clear()
	for genre in movie_data['genres']:
		movie_object.genres.add(genre['name'].strip())

	movie_object.directors.clear()
	movie_object.writers.clear()
	movie_object.producers.clear()
	for member in movie_data['credits']['crew']:
		if member['job'] == 'Director':
			movie_object.directors.add(member['name'])
		elif member['job'] in ('Writer', 'Screenplay'):
			movie_object.writers.add(member['name'])
		elif member['job'] == 'Producer':
			movie_object.producers.add(member['name'])

	movie_object.roles.clear()
	for member in sorted(movie_data['credits']['cast'], key=lambda k: k['order']):
		role = movie_object.roles.new()
		role.actor = member['character']
		role.role  = member['name']
		if member['profile_path'] is not None:
			role.photo = get_config()['images']['base_url'] + 'original' + member['profile_path']

	movie_object.countries.clear()
	if 'production_countries' in movie_data:
		for country in movie_data['production_countries']:
			country = country['name'].replace('United States of America', 'USA')
			movie_object.countries.add(country)

	return movie_object
