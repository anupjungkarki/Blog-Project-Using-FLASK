from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import json
import os
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL='True',
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(120), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(120), nullable=True)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    content = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(120), nullable=True)
    img_file = db.Column(db.String(30), nullable=False)
    sub_heading = db.Column(db.String(80), nullable=False)


@app.route("/")
def home():
    post = Posts.query.filter_by().all()
    last = math.ceil(len(post) / int(params['no_of_posts']))
    # [0: params['no_of_posts']]
    # posts = posts[]
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    post = post[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    # Pagination Logic
    # First
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, post=post, prev=prev, next=next)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.all()
        return render_template('dashboard.html', params=params, post=post)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params['admin_password']:
            session['user'] = username
            post = Posts.query.all()
            return render_template('dashboard.html', params=params, post=post)
        else:
            return redirect('/dashboard')
    else:
        return render_template('login.html', params=params)


@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            title = request.form.get('title')
            subheading = request.form.get('sub_heading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            file = request.form.get('img_file')
            date = datetime.now()

            if id == '0':
                post = Posts(title=title, sub_heading=subheading, slug=slug, content=content, img_file=file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(id=id).first()
                post.title = title
                post.sub_heading = subheading
                post.slug = slug
                post.content = content
                post.img_file = file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + id)

    post = Posts.query.filter_by(id=id).first()
    return render_template('edit.html', params=params, post=post, id=id)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    return "Uploaded successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:id>', methods=['GET', 'POST'])
def delete(id):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('msg')

        entry = Contact(name=name, email=email, phone_no=phone, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        flash("Your Message Has Been Successfully Sent To Blog Admin", "success")
        mail.send_message("New Message From:" + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=msg + "\n" + phone
                          )
    return render_template('contact.html', params=params)


if __name__ == '__main__':
    app.run(debug=True)
