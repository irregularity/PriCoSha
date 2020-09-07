from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to index
@app.route('/')
def hello():
    cursor = conn.cursor()

    #Displays public content posted within the last day
    query = 'SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE is_pub = true AND post_time >= now() - INTERVAL 1 DAY'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', posts = data)

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    #location = request.form['location']
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE email = %s and password = %s'
    cursor.execute(query, (email, hashlib.md5(password.encode('utf8')).hexdigest() ) )
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        session['email'] = email
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    password = request.form['password']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (email))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, hashlib.md5(password.encode('utf8')).hexdigest(), fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    email = session['email']
    # Displays content posted by the user
    cursor = conn.cursor()
    query = 'SELECT item_name, file_path, post_time, email_post, item_id, location FROM contentitem WHERE email_post = %s ORDER BY post_time DESC'
    cursor.execute(query, (email))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=email, posts=data)


@app.route('/post', methods=['GET', 'POST'])
def post():
    email = session['email']
    cursor = conn.cursor()
    item_name = request.form['item_name']
    file_path = request.form['file_path']
    location = request.form['location']
    status = request.form['status']

    # if public check box was selected as yes then is_pub will be set to true, otherwise it will be set to false
    pub = None
    if (status == "Yes"):
        pub = True
    else:
        pub = False

    # posts content to the database
    query = 'INSERT INTO contentitem (email_post, post_time, file_path, item_name, is_pub, location) VALUES(%s, now(), %s, %s, %s, %s)'
    cursor.execute(query, (email, file_path, item_name, pub, location))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

# logs out of user session
@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')

# Define route for item
@app.route('/item', methods=["GET", "POST"])
def item():
    if (request.method == "GET"):
        error = request.args.get('error')
        itemID = request.args.get('itemID')

    else:
        itemID = request.args['itemID']
        error = None

    # displays item info
    cursorI = conn.cursor()
    queryI = 'SELECT item_name, file_path, post_time, email_post, item_id, location, is_pub FROM contentitem WHERE item_id = %s'
    cursorI.execute(queryI, (itemID))
    dataI = cursorI.fetchall()
    cursorI.close()

    # displays item tags
    cursorT = conn.cursor()
    queryT = 'SELECT fname, lname FROM tag NATURAL JOIN person WHERE item_id = %s AND status = 1 AND email_tagged = email'
    cursorT.execute(queryT, (itemID))
    dataT = cursorT.fetchall()
    cursorT.close()

    # displays item ratings
    cursorR = conn.cursor()
    queryR = 'SELECT fname, lname, emoji FROM rate NATURAL JOIN person WHERE item_id = %s'
    cursorR.execute(queryR, (itemID))
    dataR = cursorR.fetchall()
    cursorR.close()

    #displays item comments
    cursorC = conn.cursor()
    queryC = 'SELECT comment_text, comment_time, email_post FROM comment WHERE item_id = %s'
    cursorC.execute(queryC, (itemID))
    dataC = cursorC.fetchall()
    cursorC.close()
	
    return render_template('item.html', item_num = itemID, info = dataI, tagged = dataT, rate = dataR, comment = dataC, error=error)

# Define route for post
@app.route('/create_post')
def create_post():
    return render_template('create_post.html')

@app.route('/find_location', methods=['GET', 'POST'])
def find_location():
    cursor = conn.cursor()
    loc = request.form['location']
    query = 'SELECT item_id, email_post, post_time, file_path, item_name, location FROM contentitem WHERE is_pub = true AND location = %s'
    cursor.execute(query, (loc))
    data = cursor.fetchall()
    cursor.close()

    return render_template('find_location.html', loc_name = loc, loc_filter = data)
	
@app.route('/comment', methods=['GET','POST'])
def comment():
    email = session['email']
    cursor = conn.cursor()
    c_text = request.form['comment_text']
    itemID = request.form['itemID']
    query = 'INSERT INTO comment (item_id, email_post, comment_time, comment_text) VALUES(%s, %s, now(), %s)'
    cursor.execute(query, (itemID, email, c_text))
    conn.commit()
    cursor.close()
    error = ""

    return redirect(url_for('item', itemID=itemID, error=error))
	
	
#tags another email
@app.route('/tag', methods=['GET', 'POST'])
def tag():
    tagger = session['email']
    tagged = request.form['tag_email']
    itemID = request.form['itemID']

    #checks if tagged email exists first
    cursor_check = conn.cursor()
    query_check = 'SELECT * FROM person WHERE email = %s'
    cursor_check.execute(query_check, (tagged))
    data_check = cursor_check.fetchone()

    error = ""

    # checks if the person exists
    if (data_check):
        # checks if the person was already tagged
        cursor = conn.cursor()
        query = 'SELECT * FROM tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
        cursor.execute(query, (tagged, tagger, itemID))
        data = cursor.fetchone()

        # if tagged then it will report an error
        if (data):
            error = "Already tagged"
            return redirect(url_for('item', itemID = itemID, error=error))
        else:
            # checks if item_id is visible to tagged (if item_id is public or private)
            cursor_Istatus = conn.cursor()
            query_Istatus = 'SELECT is_pub, email_post FROM contentitem WHERE item_id = %s'
            cursor_Istatus.execute(query_Istatus, (itemID))
            data_Istatus = cursor_Istatus.fetchone()
            is_pub = data_Istatus["is_pub"]
            owner_email = data_Istatus["email_post"]
            cursor_Istatus.close()

            #can't tag owner of the post
            if (owner_email == tagged):
                error = "Can't tag poster"
                return redirect(url_for('item', itemID=itemID, error=error))

            #makes public if person tags themself
            if (tagger == tagged):
                status = True
            else:
                status = False

                # checks if item is private and tagged is not the tagger meaning it is not visible to the tagged
                if (is_pub == 0):
                    error = "You cannot propose this tag"
                    return redirect(url_for('item', itemID=itemID, error=error))

            # inserts the tag
            ins = 'INSERT INTO tag VALUES(%s, %s, %s, %s, now())'
            cursor.execute(ins, (tagged, tagger, itemID, status))
            conn.commit()
            cursor.close()
            return redirect(url_for('item', itemID=itemID, error=error))
    else:
        # returns error if the person does not exist
        error = "Email does not exist"
        return redirect(url_for('item', itemID=itemID, error=error))

#manage tags
@app.route('/manage_tag', methods=['GET','POST'])
def manage_tag():
    email = session['email']

    # displays unaccepted tags
    cursor_tagger = conn.cursor()
    query_tagger = 'SELECT email_tagger, item_id, tagtime FROM tag WHERE email_tagged = %s AND status = "0"'
    cursor_tagger.execute(query_tagger, email)
    data_tagger = cursor_tagger.fetchall()
    cursor_tagger.close()

    return render_template('manage_tag.html', tagger = data_tagger)

#update tag status to true
@app.route('/accept_tag', methods=['POST'])
def accept_tag():
    email = session['email']
    email_tagger = request.form['email_tagger']
    itemID = request.form['itemID']

    # changes tag to public
    cursor_update = conn.cursor()
    query_update = 'UPDATE tag SET status = "1" WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
    cursor_update.execute(query_update, (email, email_tagger, itemID))
    cursor_update.close()

    # goes back to manage tag page
    cursor_tagger = conn.cursor()
    query_tagger = 'SELECT email_tagger, item_id, status, tagtime FROM tag WHERE email_tagged = %s AND status = "0"'
    cursor_tagger.execute(query_tagger, email)
    data_tagger = cursor_tagger.fetchall()
    cursor_tagger.close()

    return render_template('manage_tag.html', tagger=data_tagger)

#deletes tag
@app.route('/delete_tag', methods=['POST'])
def delete_tag():
    email = session['email']
    email_tagger = request.form['email_tagger']
    itemID = request.form['itemID']

    # deletes the tag if rejected
    cursor_update = conn.cursor()
    query_update = 'DELETE FROM tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
    cursor_update.execute(query_update, (email, email_tagger, itemID))
    cursor_update.close()

    # goes back to manage tag page
    cursor_tagger = conn.cursor()
    query_tagger = 'SELECT email_tagger, item_id, status, tagtime FROM tag WHERE email_tagged = %s AND status = "0"'
    cursor_tagger.execute(query_tagger, email)
    data_tagger = cursor_tagger.fetchall()
    cursor_tagger.close()

    return render_template('manage_tag.html', tagger=data_tagger)

#manages groups
@app.route('/manage_group', methods=['GET','POST'])
def manage_group():
    email = session['email']
    if (request.method == "GET"):
        error = request.args.get('error')
    else:
        error = None

    # displays groups the user owns
    cursor_owned = conn.cursor()
    query_owned = 'SELECT fg_name, description FROM friendgroup WHERE owner_email = %s'
    cursor_owned.execute(query_owned, (email))
    data_owned = cursor_owned.fetchall()
    cursor_owned.close()

    # displays the groups the user is in
    cursor_in = conn.cursor()
    query_in = 'SELECT fg_name, owner_email, description, email FROM friendgroup NATURAL JOIN belong WHERE email = %s'
    cursor_in.execute(query_in, (email))
    data_in = cursor_in.fetchall()
    cursor_in.close()

    return render_template('manage_group.html', owned_groups=data_owned, in_groups=data_in, error=error)

#see a group in detail
@app.route('/group', methods=['GET','POST'])
def group():
    email = session['email']
    if (request.method == "GET"):
        fg_name = request.args['fg_name']
        error = request.args['error']
    else:
        fg_name = request.form['fg_name']
        error = None

    # displays information about a group
    cursor = conn.cursor()
    query = 'SELECT description, fname, lname, email, owner_email FROM friendgroup NATURAL JOIN belong NATURAL JOIN person WHERE owner_email = %s AND fg_name = %s'
    cursor.execute(query, (email, fg_name))
    data = cursor.fetchall()
    description = data[0]["description"]
    cursor.close()

    return render_template('group.html', group_data=data, description=description, fg_name=fg_name, error=error)

#html to create group
@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    return render_template('create_group.html')

#creates group if valid
@app.route('/create_fg', methods=['GET', 'POST'])
def create_fg():
    email = session['email']
    fg_name = request.form['fg_name']
    description = request.form['description']

    # obtains friend group info if it exists
    cursor_check = conn.cursor()
    query_check = 'SELECT * FROM friendgroup WHERE owner_email = %s AND fg_name = %s'
    cursor_check.execute(query_check, (email, fg_name))
    data = cursor_check.fetchone()
    cursor_check.close()

    #checks if friend group already exists under the same owner email
    error = ""
    if (data):
        error = "Friend Group already exists"
        return redirect(url_for('manage_group', error=error))
    else:
        # if it does not exist it create a new friendgroup into the database
        ins = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
        cursor_ins = conn.cursor()
        cursor_ins.execute(ins, (email, fg_name, description))
        conn.commit()
        cursor_ins.close()

        # makes the owner belong to the group they created
        ins_belong = 'INSERT INTO belong VALUES(%s, %s, %s)'
        cursor_ins_belong = conn.cursor()
        cursor_ins_belong.execute(ins_belong, (email, email, fg_name))
        conn.commit()
        cursor_ins_belong.close()

        return redirect(url_for('manage_group', error=error))

# Tag Group
@app.route('/taggroup', methods=['GET', 'POST'])
def taggroup():
    email = session['email']
    cursor = conn.cursor()
    tagged = request.form['tag_group']
    itemID = request.form['itemID']

    # checks if tagged group exists first
    cursor_check = conn.cursor()
    query_check = 'SELECT * FROM friendgroup WHERE fg_name = %s'
    cursor_check.execute(query_check, (tagged))
    data_check = cursor_check.fetchone()

    # check if the group exists
    if (data_check):
        # checks if the person was already tagged
        cursor = conn.cursor()
        query = 'SELECT * FROM taggroup WHERE group_tagged = %s AND email_tagger = %s AND item_id = %s'
        cursor.execute(query, (tagged, email, itemID))
        data = cursor.fetchone()

        # if tagged then it will report an error
        if (data):
            error = "Already tagged"
            return redirect(url_for('item', itemID=itemID, error=error))
        else:
            # checks if item_id is visible to tagged (if item_id is public or private)
            cursor_Istatus = conn.cursor()
            query_Istatus = 'SELECT is_pub FROM contentitem WHERE item_id = %s'
            cursor_Istatus.execute(query_Istatus, (itemID))
            data_Istatus = cursor_Istatus.fetchone()
            is_pub = data_Istatus["is_pub"]
            cursor_Istatus.close()

            if (email == tagged):
                status = True
            else:
                status = False

                # checks if item is private and tagged is not the tagger meaning it is not visible to the tagged
                if (is_pub == 0):
                    error = "You cannot propose this tag"
                    return redirect(url_for('item', itemID=itemID, error=error))

            # inserts the tag
            ins = 'INSERT INTO taggroup VALUES(%s, %s, %s, %s, now())'
            cursor.execute(ins, (tagged, email, itemID, status))

            # inserts people in group in tag
            cursor_tagging = conn.cursor()
            query_tagging = 'SELECT email FROM belong WHERE fg_name = %s AND owner_email = %s'
            # add owner email too
            cursor_tagging.execute(query_tagging, (tagged, email))
            data_tagging = cursor_tagging.fetchall()
            print(data_tagging)
            for email_tag in data_tagging:
                # Check if person is already tagged
                cursor_check = conn.cursor()
                query_check = 'SELECT * FROM tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
                cursor_check.execute(query, (email_tag["email"], email, itemID))
                data_person = cursor_check.fetchone()
                # if tagged then it will report an error
                if (data_person):
                    error = "One or more people are Already tagged"
                    return redirect(url_for('item', itemID = itemID, error=error))
                else:
                    # checks if item_id is visible to tagged (if item_id is public or private)
                    cursor_Istatus = conn.cursor()
                    query_Istatus = 'SELECT is_pub, email_post FROM contentitem WHERE item_id = %s'
                    cursor_Istatus.execute(query_Istatus, (itemID))
                    data_Istatus = cursor_Istatus.fetchone()
                    is_pub = data_Istatus["is_pub"]
                    owner_email = data_Istatus["email_post"]
                    cursor_Istatus.close()

                    #can't tag owner of the post
                    if (owner_email == email_tag["email"]):
                        error = "Can't tag poster"
                        return redirect(url_for('item', itemID=itemID, error=error))

                    #makes public if person tags themself
                    if (email == email_tag["email"]):
                        status = True
                    #else:
                    #    status = False

                    # checks if item is private and tagged is not the tagger meaning it is not visible to the tagged
                    if (is_pub == 0):
                        error = "You cannot propose this tag"
                        return redirect(url_for('item', itemID=itemID, error=error))
                    else:
                        ins = 'INSERT INTO tag VALUES(%s, %s, %s, %s, now())'
                        cursor.execute(ins, (email_tag["email"], email, itemID, status))
            conn.commit()
            cursor.close()
            return redirect(url_for('item', itemID=itemID, error=error))

    else:
        # returns error if the person does not exist
        error = "Group does not exist"
        return redirect(url_for('item', itemID=itemID, error=error))


# remove a person from friend group
@app.route('/defriend', methods=['POST'])
def defriend():
    owner_email = request.form['owner_email']
    remove_email = request.form['remove_email']
    fg_name = request.form['fg_name']
    error = ""

    # in case someone tries to remove themselves from a group they own
    if (owner_email == remove_email):
        error = "Can't remove yourself from your own group"
    else:
        # removes a person from a group
        cursor_remove = conn.cursor()
        query_remove = 'DELETE FROM belong WHERE owner_email = %s AND email = %s AND fg_name = %s'
        cursor_remove.execute(query_remove, (owner_email, remove_email, fg_name))
        cursor_remove.close()

    return redirect(url_for('manage_group', error=error))

# checks if friend can be added
@app.route('/check_friend', methods=['GET', 'POST'])
def check_friend():
    #obtains info from adding group
    owner_email = session['email']
    fname = request.form['fname']
    lname = request.form['lname']
    fg_name = request.form['fg_name']
    error = None

    #obtain the amount of people with the same first name and last name
    cursor = conn.cursor()
    query = 'SELECT email, count(*) AS count FROM person WHERE fname = %s AND lname = %s'
    cursor.execute(query, (fname, lname))
    data = cursor.fetchone()

    # if there is no entry then that means the person does not exist
    if (data["count"] == 0):
        error = "Person does not exist"

    # if there is a single entry then it will add the person into the friend group
    elif (data["count"] == 1):
        add_email = data["email"]
        error = check_in_group(add_email, owner_email, fg_name)
        if (error == None):
            add_friend(add_email, owner_email, fg_name)
            error = ""
    # if there are multiple people with the same name it will redirect to a page to select the email of the person
    else:
        return redirect(url_for('select_email', fg_name=fg_name, fname=fname, lname=lname))

    return redirect(url_for('group', group_data=data, fg_name=fg_name, error=error))


#pick an email from friend group
@app.route('/select_email', methods=['GET'])
def select_email():
    fname = request.args['fname']
    lname = request.args['lname']
    fg_name = request.args['fg_name']

    # displays all emails with that name
    cursor_select = conn.cursor()
    query_select = 'SELECT DISTINCT email FROM person WHERE fname = %s AND lname = %s'
    cursor_select.execute(query_select, (fname, lname))
    data_select = cursor_select.fetchall()
    cursor_select.close()

    return render_template('select_email.html', data_select=data_select, fg_name=fg_name, fname=fname, lname=lname)

#add friend after selecting email
@app.route('/add_after_select', methods=['GET', 'POST'])
def add_after_select():
    owner_email = session['email']
    friend = request.args['friend']
    fg_name = request.args['fg_name']

    #checks if the person is valid
    error = check_in_group(friend, owner_email, fg_name)
    if (error == None):
        # add person to friend group if valid
        add_friend(friend, owner_email, fg_name)
        error = ""

    return redirect(url_for('group', fg_name=fg_name, error=error))

# executes query to add a person to a friend group
def add_friend(email, owner_email, fg_name):
    cursor = conn.cursor()
    ins = 'INSERT INTO belong VALUES(%s, %s, %s)'
    cursor.execute(ins, (email, owner_email, fg_name))
    conn.commit()
    cursor.close()
    return

#sees if the person exists in friend group already
def check_in_group(email, owner_email, fg_name):
    cursor_group = conn.cursor()
    query_group = 'SELECT * FROM belong WHERE email = %s AND owner_email = %s AND fg_name = %s'
    cursor_group.execute(query_group, (email, owner_email, fg_name))
    data = cursor_group.fetchone()
    cursor_group.close()
    error = None
    if (data):
        error = "Friend already in group"
    return error


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)

