from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)





# Connect to Database and create database session
engine = create_engine('postgresql://catalog:catalog@0.0.0.0/restaurant')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#######################
#OAUTH LOGIN FUNCTIONS#
#######################

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    CLIENT_ID = json.loads(open('/var/www/Catalog/go_client_secrets.json', 'r').read())['web']['client_id']
    APPLICATION_NAME = "Restaurant Menu Application"
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
    # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/Catalog/go_client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'% access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    
    login_session['provider']='google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    user_id=getUserId(login_session['email'])
    if not user_id:
        user_id=createUser(login_session)
    login_session['user_id']=user_id
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output
    


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('/var/www/Catalog/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(open('/var/www/Catalog/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

   
#################################
#DISCONNECT FROM OAUTH PROVIDERS#
#################################

@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session and login_session['provider']=='google':	# Only disconnect a connected user.
		credentials = login_session.get('credentials')
		if credentials is None:
			response = make_response(
			json.dumps('Current user not connected.'), 401)
			response.headers['Content-Type'] = 'application/json'
			return response
		access_token = login_session.get('credentials')
		print access_token
		url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
		print url
		h = httplib2.Http()
		result = h.request(url, 'GET')[0]
		if result['status'] == '200':
			# Reset the user's sesson.
			del login_session['provider']
			del login_session['credentials']
			del login_session['gplus_id']
			del login_session['username']
			del login_session['email']
			del login_session['picture']
			del login_session['user_id']

			response = make_response(json.dumps('Successfully disconnected.'), 200)
			response.headers['Content-Type'] = 'application/json'
			flash("Successfully logged out!")
			return redirect(url_for("showRestaurants"))
		else:
			print result['status']
			# For whatever reason, the given token was invalid.
			response = make_response(
			json.dumps('Failed to revoke token for given user.', 400))
			response.headers['Content-Type'] = 'application/json'
			return response
	if 'provider' in login_session and login_session['provider']=='facebook':
		facebook_id = login_session['facebook_id']
		# The access token must be included to successfully logout
		access_token = login_session['access_token']
		print access_token
		url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
		h = httplib2.Http()
		result = h.request(url, 'DELETE')[1]
		del login_session['provider']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		flash("Successfully logged out!")
		return redirect(url_for("showRestaurants"))
	else:
		flash("You were not logged in")
		return redirect(url_for("showRestaurants"))
################
#JSON ENDPOINTS#
################

# JSON APIs to view Restaurant Information
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items])

#JSON to return single menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
	Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
	return jsonify(Menu_Item=Menu_Item.serialize)

#JSON to return all restaurants
@app.route('/restaurant/JSON')
def restaurantsJSON():
	restaurants = session.query(Restaurant).all()
	return jsonify(restaurants=[r.serialize for r in restaurants])

###############################
#RESTAURANT ROUTING FUNCTIONS:#
###############################

# Show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
	restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
	return render_template('restaurants.html', restaurants=restaurants,login_session=login_session)

# Create a new restaurant
@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newRestaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
		session.add(newRestaurant)
		flash('New Restaurant %s Successfully Created' % newRestaurant.name)
		session.commit()
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('newrestaurant.html')

# Edit a restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if authorizeCheck(restaurant):#make sure only authorized users have control
		if request.method == 'POST':
			if request.form['name']:
			    editedRestaurant.name = request.form['name']
			    session.add(editedRestaurant)
			    session.commit()
			    flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
			return redirect(url_for('showRestaurants'))
		else:
			return render_template('editrestaurant.html', restaurant=editedRestaurant)
	else: 
		flash("You are not authorized to edit this restaurant")
		return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
	
# Delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if authorizeCheck(restaurantToDelete):#make sure only authorized users have control
		if request.method == 'POST':
			session.delete(restaurantToDelete)
			flash('%s Successfully Deleted' % restaurantToDelete.name)
			session.commit()
			return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
		else:
			return render_template('deleterestaurant.html', restaurant=restaurantToDelete)
	else:
		flash("You are not authorized to delete this restaurant")
		return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
	
	
#########################
#MENU ROUTING FUNCTIONS:#
#########################
	
	
	
# Show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	creator = getUserInfo(restaurant.user_id)
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()    
	if authorizeCheck(restaurant):#make sure only authorized users have control
		return render_template('menu.html', items=items, restaurant=restaurant, creator=creator,restaurant_id=restaurant_id)
	else:
		return render_template('menudisplay.html', items=items, restaurant=restaurant,creator=creator, restaurant_id=restaurant_id)

# Create a new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if authorizeCheck(restaurant):#make sure only authorized users have control
		if request.method == 'POST':
			newItem = MenuItem(name=request.form['name'], description=request.form['description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=login_session['user_id'])
			session.add(newItem)
			session.commit()
			flash('New Menu Item %s Successfully Created' % (newItem.name))
			return redirect(url_for('showMenu', restaurant_id=restaurant_id))
		else:
			return render_template('newmenuitem.html', restaurant_id=restaurant_id)
	else:
		flash("You are not authorized to add a menu item to this restaurant")
		return redirect(url_for('showMenu', restaurant_id=restaurant_id))
	
# Edit a menu item


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if authorizeCheck(restaurant):#make sure only authorized users have control
		if request.method == 'POST':
			if request.form['name']:
				editedItem.name = request.form['name']
			if request.form['description']:
				editedItem.description = request.form['description']
			if request.form['price']:
				editedItem.price = request.form['price']
			if request.form['course']:
				editedItem.course = request.form['course']
				session.add(editedItem)
				session.commit()
			flash('Menu Item Successfully Edited')
			return redirect(url_for('showMenu', restaurant_id=restaurant_id))
		else:
			return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=editedItem)
	else:
		flash('You are not authorized to edit menu items from this restaurant')
		return redirect(url_for('showMenu', restaurant_id=restaurant_id))


# Delete a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
	if authorizeCheck(restaurant):#make sure only authorized users have control
		if request.method == 'POST':
			session.delete(itemToDelete)
			session.commit()
			flash('Menu Item Successfully Deleted')
			return redirect(url_for('showMenu', restaurant_id=restaurant_id))
		else:
			return render_template('deletemenuitem.html', item=itemToDelete, restaurant_id=restaurant_id)
	else:
		flash("You are not authorized to delete this item")
		return redirect(url_for('showMenu', restaurant_id=restaurant_id))

#########################
#LEFTOVER USER FUNCTIONS#
#########################

def getUserId(email):#exchanges email for local user id
	try:
		user =session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

def getUserInfo(user_id):#exchanges user id for local user 
	user = session.query(User).filter_by(id=user_id).one()
	return user
    
def authorizeCheck(restaurant):#checks to see if the user in login session is the owner of the restaurant
	owner=getUserInfo(restaurant.user_id)
	if 'email' in login_session and owner.email==login_session['email']:
		return True
	else:
		return False    

def createUser(login_session):#with user's first login adds a user to local database
    newUser=User(name=login_session['username'], email = login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user=session.query(User).filter_by(email=login_session['email']).one()
    return user.id
    
    

if __name__ == '__main__':
    app.secret_key = 'grader'
    #app.debug = True
    app.run(host='0.0.0.0', port=5000)
