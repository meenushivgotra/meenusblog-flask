from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json, os
from os.path import join, dirname, realpath
from flask_mail import Mail
from werkzeug.utils import secure_filename
import math

with open('config.json', 'r') as c:
    params = json.load(c) ['params']

local_server =  True


app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.config['upload_image'] = params['image_upload']
UPLOADS_PATH = join(dirname(realpath(__file__)), 'static\\img')
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
))

mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    p_no = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return '<Contacts %r>' % self.email

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    bg_img = db.Column(db.String(12), nullable=True)

    def __repr__(self):
        return '<Posts %r>' % self.title

@app.route('/dashboard', methods = ['GET','POST'])
def signin():
    if ('user' in session and session['user'] == params['admin']):
        all_posts = Posts.query.filter_by().all()
        three_post = Posts.query.filter_by().all()[::-1][:3]
        return render_template('admin/dashboard.html', params=params, all_posts = all_posts, three_post = three_post)
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        if (username == params['admin']  and  password == params['admin_password']):
            #session
            session['user'] = username
            all_posts = Posts.query.filter_by().all()
            three_post = Posts.query.filter_by().all()[::-1][:3]
            return render_template('admin/dashboard.html', params=params, all_posts = all_posts, three_post = three_post)
    return render_template('admin/signin.html', params = params)

@app.route('/logout')
def logout():
    if ('user' in session and session['user'] == params['admin']):
        session.pop('user')
        return redirect('/dashboard')

@app.route('/delete/<string:sno>', methods = ['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

@app.route('/edit/<string:sno>', methods = ['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin']):
        if request.method == 'POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')

            if sno == '0':
                post = Posts(title = title, slug= slug, content = content, date = datetime.now())
                if request.files['image'].filename != '':
                    print("true")
                    image = request.files['image']
                    image.save(os.path.join(UPLOADS_PATH, secure_filename(image.filename)))
                    post.bg_img = secure_filename(image.filename)
                db.session.add(post)
                db.session.commit()
                flash("Post added successfully.", "success")
                return redirect('/dashboard')

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.slug = slug
                post.content = content
                if request.files['image'].filename != '':
                    print('true')
                    image = request.files['image']
                    image.save(os.path.join(UPLOADS_PATH, secure_filename(image.filename)))
                    post.bg_img = secure_filename(image.filename)
                post.date = datetime.now()
                db.session.commit()
                flash("Post edited successfully.", "success")
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno = sno).first()
        return render_template('admin/edit_post.html', params = params, post = post, sno = sno)

@app.route('/')
def home():
    # flash("hi","success")
    # flash("bye","danger")
    all_posts = Posts.query.filter_by().all()[::-1][:params['no_of_posts']]
    last = math.ceil(len(all_posts) / int(params['no_of_posts']))
    # [0: params['no_of_posts']]
    # posts = posts[]
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = all_posts[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    # Pagination
    # First
    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page + 1)
    # last
    elif (page == last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    # middle
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template('index.html', params = params, all_posts = all_posts, prev=prev, next=next)

@app.route('/about')
def about():
    return render_template('about.html', params = params)


@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        """"Entry to DB """
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, email=email, p_no = phone, message = message, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from'+' '+ name, sender = email , recipients = [params['gmail_user']], body = message + "\n" +phone + "\n" + email)
        flash("Thanks for sending message. I will get back to you soon.", "success")
    return render_template('contact.html', params = params)

@app.route('/post/<string:post_slug>', methods = ['GET'])
def post(post_slug):
    slug  = str(post_slug)
    post_data = Posts.query.filter_by(slug = slug).first()

    return render_template('post.html', params = params, post_data =  post_data)

app.run(debug=True)