from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import MySQLdb.cursors
import re
import pandas as pd 
import os
from os.path import exists
from email.message import EmailMessage
import ssl
import smtplib

from flask_paginate import Pagination, get_page_parameter

email_sender = ""
email_password = ""

credentials = {
    "developer_token": "J4ZIPTCgPRdKp5qcz9Ugbg",
    "client_id": "988169984630-315oq2dvf0k51pug1nso1bjv6jujrca3.apps.googleusercontent.com",
    "client_secret": "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",
    "refresh_token": "1//09260HtwS53f3CgYIARAAGAkSNwF-L9Ir6UB1VWQ5CKLajUZ7cWzgzWKy5yNPu77wQj7mxEc8CXl3qrBtTPduPTx5lOMQXV2omQ4",
    "use_proto_plus": "True"}

client = GoogleAdsClient.load_from_dict(credentials)
print("connected successfully to the api!")

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'KeywordSearchUser.mysql.pythonanywhere-services.com' #''
app.config['MYSQL_USER'] = 'KeywordSearchUse' #''
app.config['MYSQL_PASSWORD'] = 'wZmn6kVn1C' #''
app.config['MYSQL_DB'] = 'KeywordSearchUse$sql9563698'  #''

# Intialize MySQL
mysql = MySQL(app)

_DEFAULT_LOCATION_IDS = ["1023191"]  # location ID for New York, NY
_DEFAULT_LANGUAGE_ID = "1000"  # language ID for English
# [START generate_keyword_ideas]
def main(
    client, customer_id, location_ids, language_id, keyword_texts, page_url
):
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    keyword_competition_level_enum = client.get_type(
        "KeywordPlanCompetitionLevelEnum"
    ).KeywordPlanCompetitionLevel
    keyword_plan_network = client.get_type(
        "KeywordPlanNetworkEnum"
    ).KeywordPlanNetwork.GOOGLE_SEARCH_AND_PARTNERS
    location_rns = _map_locations_ids_to_resource_names(client, location_ids)
    language_rn = client.get_service("GoogleAdsService").language_constant_path(
        language_id
    )
    
    keyword_annotation = client.enums.KeywordPlanKeywordAnnotationEnum
    
    # Either keywords or a page_url are required to generate keyword ideas
    # so this raises an error if neither are provided.
    if not (keyword_texts or page_url):
        raise ValueError(
            "At least one of keywords or page URL is required, "
            "but neither was specified."
        )
    
    
    
    # Only one of the fields "url_seed", "keyword_seed", or
    # "keyword_and_url_seed" can be set on the request, depending on whether
    # keywords, a page_url or both were passed to this function.
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = language_rn
    request.geo_target_constants = location_rns
    request.include_adult_keywords = False
    request.keyword_plan_network = keyword_plan_network
    request.keyword_annotation = keyword_annotation
    
    
    
    # To generate keyword ideas with only a page_url and no keywords we need
    # to initialize a UrlSeed object with the page_url as the "url" field.
    if not keyword_texts and page_url:
        request.url_seed.url = url_seed
 
    # To generate keyword ideas with only a list of keywords and no page_url
    # we need to initialize a KeywordSeed object and set the "keywords" field
    # to be a list of StringValue objects.
    if keyword_texts and not page_url:
        request.keyword_seed.keywords.extend(keyword_texts)
 
    # To generate keyword ideas using both a list of keywords and a page_url we
    # need to initialize a KeywordAndUrlSeed object, setting both the "url" and
    # "keywords" fields.
    if keyword_texts and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keyword_texts)
 
    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(
        request=request
    )
    
    list_keywords = []
    for idea in keyword_ideas:
        competition_value = idea.keyword_idea_metrics.competition.name
        list_keywords.append(idea)
    
    return list_keywords
 
def map_keywords_to_string_values(client, keyword_texts):
    keyword_protos = []
    for keyword in keyword_texts:
        string_val = client.get_type("StringValue")
        string_val.value = keyword
        keyword_protos.append(string_val)
    return keyword_protos
 
 
def _map_locations_ids_to_resource_names(client, location_ids):
    """Converts a list of location IDs to resource names.
    Args:
        client: an initialized GoogleAdsClient instance.
        location_ids: a list of location ID strings.
    Returns:
        a list of resource name strings using the given location IDs.
    """
    build_resource_name = client.get_service(
        "GeoTargetConstantService"
    ).geo_target_constant_path
    return [build_resource_name(location_id) for location_id in location_ids]



# http://localhost:5000/api/ - the following will be our login page, which will use both GET and POST requests
@app.route('/api/', methods=['GET', 'POST'])
def login():
    # remove result csv file
    if (exists("csv/result.csv")):
        os.remove("csv/result.csv")
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg='')

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/api/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/api/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'

            subject = "Confirmation of registration"
            email_receiver = email
            body = f"""
            Hello {username}, thanks for joining our platform!
            """
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)



# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/api/reset', methods=['GET', 'POST'])
def reset():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'newPassword' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        newPassword = request.form['newPassword']
        if not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not newPassword:
            msg = 'Please fill out the form!'
        else:
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
            account = cursor.fetchone()
            print(account)
            if account:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE accounts SET password = %s WHERE username = %s', (newPassword, username,))
                mysql.connection.commit()
                msg = 'You have successfully reset your password!'
            else:
                msg = 'Account does not exist!'            
            
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('reset.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/api/home', methods=['GET'])
def home():
    # Check if user is loggedin
    if request.args.get('keyword') is None:
        if 'loggedin' in session:
            # User is loggedin show them the home page
            return render_template('home.html', username=session['username'], data={"FirstName": ["Achraf"], "LastName": ["Haddar"]}, number=1, result_list=None, keyword=None)
        # User is not loggedin redirect to login page
        return redirect(url_for('login'))
    else:
        keyword = request.args.get('keyword')
        #keyword = request.form['keyword']
        list_keywords = main(client, "6283255293", ["2840"], "1000", [keyword], None)  
        result_list = []
        for x in range(len(list_keywords)):            
            result_list.append([list_keywords[x].text, list_keywords[x].keyword_idea_metrics.avg_monthly_searches, str(list_keywords[x].keyword_idea_metrics.competition)[28::]])
        print(result_list)
        # Save CSV file
        pd.DataFrame(result_list, columns = ["Keyword", "Average Searches", "Competition Level"]).to_csv('csv/result.csv', header=True, index=False)

        search = False
        q = request.args.get('q')
        if q:
            search = True
        page = request.args.get(get_page_parameter(), type=int, default=1)
        pagination = Pagination(per_page=50, page=page, total=len(list_keywords), search=search, record_name='result_list')
        
        return render_template("home.html", username=session['username'], data={"FirstName": ["Achraf"], "LastName": ["Haddar"]}, number=1, result_list=result_list[(page-1)*50:(50*page)-1], keyword=keyword, pagination=pagination)

@app.route("/api/getCSV")
def getCSV():
    # with open("outputs/Adjacency.csv") as fp:
    #     csv = fp.read()
    path = "csv/result.csv"
    if (exists(path)):
        return send_file(path, as_attachment=True, cache_timeout=0)
    return send_file("csv/empty.csv", as_attachment=True, cache_timeout=0)

if __name__ == "__main__":
    app.run()