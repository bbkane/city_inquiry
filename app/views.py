from flask import render_template, redirect
from app import app
from .forms import CityForm
from app import api_calls as apis


@app.route('/', methods=['GET', 'POST'])
def index():
    city_form = CityForm()
    if city_form.validate_on_submit():
        # turn into REST
        return redirect('/results/{}/{}'.format(city_form.state.data,
                                                city_form.city.data))
    return render_template('index.html',
                           city_form=city_form,
                           title="Title")


@app.route('/results/<state>/<city>')
def results(state, city):
    # call a bunch of apis here
    # I'll end up doing these with futures, but not right now
    # on error, each of my api calls returns None
    # the html template checks to see if they're None
    return render_template('results.html',
                           title=city + ' : results',
                           city=city,
                           weather=apis.get_weather(city),
                           schools=apis.get_schools_generator(state, city),
                           latlng=apis.get_latlng(state, city))
