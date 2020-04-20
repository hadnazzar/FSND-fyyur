# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# run flask db init to create migrations folder
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.String())
    seeking_description = db.Column(db.String())


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String())
    seeking_venue = db.Column(db.String())
    seeking_description = db.Column(db.String())


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    venue_name = db.relationship('Venue', backref=db.backref('shows'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    artist = db.relationship('Artist', backref=db.backref('shows'))


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

    for city in cities:
        venues_in_city = db.session.query(Venue.id, Venue.name).filter(Venue.city == city[0]).filter(
            Venue.state == city[1])
        data.append({
            "city": city[0],
            "state": city[1],
            "venues": venues_in_city
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
    data = []

    for venue in venues:
        num_upcoming_shows = 0
        shows = db.session.query(Show).filter(Show.venue_id == venue.id)
        for show in shows:
            if (show.start_time > datetime.now()):
                num_upcoming_shows += 1

        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    response = {
        "count": len(venues),
        "data": data
    }


    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

    shows_list = db.session.query(Show).filter(Show.venue_id == venue_id)
    past_shows = []
    upcoming_shows = []

    for show in shows_list:
        artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).one()
        show_add = {
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime('%m/%d/%Y')
        }

        if (show.start_time < datetime.now()):
            # print(past_shows, file=sys.stderr)
            past_shows.append(show_add)
        else:
            upcoming_shows.append(show_add)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)

    try:
        venue = Venue(
            name=form.name.data,
            genres=form.genres.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            website=form.website.data,
            facebook_link=form.facebook_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
            image_link=form.image_link.data,
        )
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        # flash('Venue ' + request.form['name'] + ' was successfully listed!')
        flash('Venue ' + form.name.data + ' was successfully listed!')
    except:
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Venue ' + form.name.data + ' could not be added.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        db.session.query(Venue).filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted!')
    except:
        flash('An error occurred. Venue could not be deleted.')
    finally:
        db.session.close()
    return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    data = []
    artists = db.session.query(Artist.id, Artist.name)
    for artist in artists:
        data.append({
            "id": artist[0],
            "name": artist[1]
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artists = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
    data = []

    for artist in artists:
        num_upcoming_shows = 0
        shows = db.session.query(Show).filter(Show.artist_id == artist.id)
        for show in shows:
            if (show.stat_time > datetime.now()):
                num_upcoming_shows += 1;
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows
        })
    response = {
        "count": len(artists),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

    list_shows = db.session.query(Show).filter(Show.artist_id == artist_id)
    past_shows = []
    upcoming_shows = []

    for show in list_shows:
        venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()

        show_add = {
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime('%m/%d/%Y')
        }

        if (show.start_time < datetime.now()):
            # print(past_shows, file=sys.stderr)
            past_shows.append(show_add)
        else:
            print(show_add, file=sys.stderr)
            upcoming_shows.append(show_add)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)

    updated_artist = {
        "name": form.name.data,
        "genres": form.genres.data,
        "address": form.address.data,
        "city": form.city.data,
        "state": form.state.data,
        "phone": form.phone.data,
        "website": form.website.data,
        "facebook_link": form.facebook_link.data,
        "seeking_venue": form.seeking_venue.data,
        "seeking_description": form.seeking_description.data,
        "image_link": form.image_link.data,
    }
    try:
        db.session.query(Artist).filter(Artist.id == artist_id).update(updated_artist)
        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + form.name.data + 'could not be added')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)

    updated_venue = {
        "name": form.name.data,
        "genres": form.genres.data,
        "address": form.address.data,
        "city": form.city.data,
        "state": form.state.data,
        "phone": form.phone.data,
        "website": form.website.data,
        "facebook_link": form.facebook_link.data,
        "seeking_talent": form.seeking_talent.data,
        "seeking_description": form.seeking_description.data,
        "image_link": form.image_link.data
    }
    try:
        db.session.query(Venue).filter(Venue.id == venue_id).update(updated_venue)
        db.session.commit()
        flash('Venue' + form.name.data + ' was successfully updated!')
    except:
        flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm(request.form)

    artist = Artist(
        name=form.name.data,
        genres=form.genres.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        website=form.website.data,
        facebook_link=form.facebook_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data,
        image_link=form.image_link.data,
    )
    try:
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' + form.name.data + 'could not be added')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows = db.session.query(Show.artist_id, Show.venue_id, Show.start_time).all()

    for show in shows:
        artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show[0]).one()
        venue = db.session.query(Venue.name).filter(Venue.id == show[1]).one()
        data.append({
            "venue_id": show[1],
            "venue_name": venue[0],
            "artist_id": show[0],
            "artist_name": artist[0],
            "artist_image_link": artist[1],
            "start_time": str(show[2])
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    form = ShowForm(request.form)

    show = Show(
        venue_id=form.venue_id.data,
        artist_id=form.artist_id.data,
        start_time=form.start_time.data
    )

    try:
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed')
    except:
        # e.g., flash('An error occurred. Show could not be listed.')
        flash('An error occurred. Show could not be added')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
