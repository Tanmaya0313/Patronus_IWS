from flask import Flask,render_template,flash,redirect,url_for,request,session,logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app= Flask(__name__); #__name__ is a placeholder for the current module, in this case app.py

#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='root'
app.config['MYSQL_DB']='forum_db'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#init MYSQL_DB
mysql=MySQL(app)

#Articles= Articles() #pulling articles out from the file data.py and not the database so commenting it out

"""The route() decorator in Flask is used to bind URL to a function
 As a result, if a user visits http:/localhost:5000/hello URL, the output of the hello_world() function will be
  rendered in the browser."""

  #Index
@app.route('/') #analogous to home controller
def index():
    return render_template('home.html')

#About
@app.route('/about') #this is like controller in MVC
def about():
    return render_template('about.html')

#Articles
@app.route('/postlist') #this is like controller in MVC
def postlist():
    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    result=cur.execute('SELECT * from Posts')
    post=cur.fetchall()
    if result>0:
        return render_template('postlist.html',post=post)
    else:
        msg="No Articles Found"
        return render_template('postlist.html',msg=msg)
    return render_template('postlist.html')
    return render_template('postlist.html',post=post)
    
    
#Comments Form Class
class CommentForm(Form):
    comment_body=TextAreaField('Comment',[validators.Length(min=10)])

#single post
@app.route('/post/<string:id>/',methods=['GET', 'POST'])
def post(id):
    form=CommentForm(request.form)
    cur=mysql.connection.cursor()
    #Insert comment in db
    if request.method=='POST' and form.validate():
        body=form.comment_body.data
        
        #Create cursor
        cur=mysql.connection.cursor()
        #Execute
        cur.execute("INSERT INTO Comments(post_id,body,author) VALUES(%s,%s,%s)",(id,body,session['username']))
        #Commit to DB
        mysql.connection.commit()
        #Close connection
        #cur.close()
   # elif request.method=='POST':

    

    #end

    

    #Get article
    
    result=cur.execute('SELECT * from Posts WHERE id= %s',[id])
    post=cur.fetchone()
    res1= cur.execute('SELECT * from Comments where post_id=%s',[id])
    commentList=cur.fetchall();

    return render_template('post.html',post=post,form=form,comments=commentList)
    
   
@app.route('/contact') #this is like controller in MVC
def contact():
    return render_template('contact.html')

#Register Form Class
class RegisterForm(Form):
    name= StringField('Name', [validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[
     validators.DataRequired(),
     validators.Length(min=4,max=50),
     validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm=PasswordField('Confirm Password')
    interest=StringField('Interest',[validators.Length(min=2,max=50)])

#Login Form class
'''class LoginForm(Form):
    loginname=StringField('loginname',[validators.DataRequired()])
    loginpwd=StringField('loginpwd',[validators.DataRequired()])'''

#User Register
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        interest=form.interest.data
        #create cursor
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO User(email,username,password,interest,name) VALUES(%s,%s,%s,%s,%s)",(email,username,password,interest,name))
        #commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close();
        #display flash message on successful registration
        flash('You are now registered and can be logged in','success')
        return redirect(url_for('login'))

    return render_template('register.html',form=form)
#User Login
@app.route('/login',methods=['GET','POST']) #this is like controller in MVC
def login():
    #form=LoginForm(request.form)
    if request.method=='POST':
        username=request.form['username']
        password_candidate=request.form['password'];
        #username=form.loginname.data
        #password_candidate=form.loginpwd.data

        #Create cursor
        cur=mysql.connection.cursor()
        #Get user by username
        result=cur.execute('SELECT * from User WHERE username= %s',[username])
        if result >0:
            #Get stored hash
            data=cur.fetchone()
            password=data['password']

            #Compare the Passwords
            if sha256_crypt.verify(password_candidate,password):
                #passed
                session["logged_in"]= True;
                session["username"]=username;
                flash("You are now logged in","success")
                return redirect(url_for('dashboard'))
                #msg="You have logged in successfully"
                #return render_template('login.html',msg=msg)
            else:
                    error="Invalid Login"
                    return render_template('login.html',error=error)
            #Close Connection
            cur.close();

        else:
            error="Username doesn't exist"
            return render_template('login.html',error=error)

    return render_template('login.html')

#Check if user logged in
#we use decorators here  which are used for injecting additional functionality to one or more functions
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
                return f(*args,**kwargs)
        else:
            flash("Unauthorized, please login","danger")
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You have been logged out","success")
    return redirect(url_for('login'))
#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur=mysql.connection.cursor()

    #Get articles
    #result=cur.execute('SELECT * from Articles WHERE author=%s',[session['username']])
    result=cur.execute('SELECT * from Posts WHERE author=%s',[session['username']])
    posts=cur.fetchall()
    if result>0:
        return render_template('dashboard.html',posts=posts)
    else:
        msg="No Posts Found"
        return render_template('dashboard.html',msg=msg)
    return render_template('dashboard.html')
#Article form class
class PostForm(Form):
    title= StringField('Title', [validators.Length(min=1,max=200)])
    body=TextAreaField('Body',[validators.Length(min=30)])
    category=StringField('Category', [validators.Length(min=2,max=50)])

#Add article
@app.route('/add_post',methods=['GET','POST'])
@is_logged_in
def add_post():
   
    form=PostForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data
        category=form.category.data;

        #Create cursor
        cur=mysql.connection.cursor()
        #Execute
        cur.execute("INSERT INTO Posts(author,title,body,upvote,category) VALUES(%s,%s,%s,%s,%s)",(session['username'],title,body,0,category))
        #Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()

        flash('Discussion Thread created','success')
        return redirect(url_for('dashboard'))
    return render_template('add_post.html',form=form)

#edit Article

@app.route('/edit_post/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_post(id):
    cur=mysql.connection.cursor()
    #Get the article by id
    result=cur.execute("SELECT * from Posts where id=%s",[id])
    post=cur.fetchone()

    #Get form
    form=PostForm(request.form)

    #Populate article from fields
    form.title.data=post['title']
    form.body.data=post['body']


    if request.method=='POST' :
        title=request.form['title']
        body=request.form['body']

        #Create cursor
        cur=mysql.connection.cursor()
        #Execute
        cur.execute("UPDATE Posts SET title=%s,body=%s WHERE id=%s",(title,body,id))
        #Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()

        flash('Post Updated','success')
        return redirect(url_for('dashboard'))
    return render_template('edit_post.html',form=form)

#delete article
@app.route('/delete_post/<string:id>',methods=['POST'])
@is_logged_in
def delete_post(id):
    #Create cursor
     cur=mysql.connection.cursor()
     #Execute
     cur.execute('DELETE from Posts WHERE id=%s',[id])
     #commit to db
     mysql.connection.commit()
     #Close connection
     cur.close()
     flash('Post Deleted','success')
     return redirect(url_for('dashboard'))

if __name__=='__main__':  #this means the script which is gonna be executed
    app.secret_key='secret123'
    app.run(debug=True)
