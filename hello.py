# stop @ 39

from flask import Flask, render_template, flash, request, redirect, url_for


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm, SearchForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os


# Create a Flask Instance
app = Flask(__name__)
# Add CKEditor
ckeditor = CKEditor(app)


# Add Database
# OLD SQL LITE DB
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

# NEW MYSQL DB
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:1234@localhost/our_users"
# Secret Key
app.config["SECRET_KEY"] = "my super secret key that no one is supposed to know"

UPLOAD_FOLDER = "static/images/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize the Database

db = SQLAlchemy(app)
# Diesen Befehl für Powershell: flask --app hello.py db migrate -m 'commit message'
migrate = Migrate(app, db)


# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



################
###  Routes  ###
################


# Add Post Page
@app.route("/add-post", methods=["GET", "POST"])
# @login_required
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title = form.title.data, content = form.content.data, poster_id = poster, slug = form.slug.data)
        # Clear The Form
        form.title.data = ""
        form.content.data = ""
        # form.author.data = ""
        form.slug.data = ""

        # add post data to database
        db.session.add(post)
        db.session.commit()

        # Return a Message
        flash("Blog Post Submitted Successfully!")

    # Redirect to the webpage
    return render_template("add_post.html", form = form)


@app.route("/admin")
@login_required
def admin():
    id = current_user.id
    if id == 1:
        return render_template("admin.html")
    else:
        flash("Sorry you must be the admin to access this page")
        return redirect(url_for("dashboard"))


@app.route("/user/add", methods = ["GET", "POST"])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email = form.email.data).first()
        if user is None:
            # hash the password
            hashed_pw = generate_password_hash(form.password_hash.data, method='pbkdf2:sha256')
            user = Users(username = form.username.data, name=form.name.data, email = form.email.data, favorite_color = form.favorite_color.data, password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ""
        form.username.data = ""
        form.email.data = ""
        form.favorite_color.data = ""
        form.password_hash = ""

        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    
    return render_template("add_user.html", form = form, name = name, our_users = our_users)


# Json return
@app.route("/date")
def get_current_date():
    favourite_pizza = {
        "John": "Pepperoni",
        "Mary": "Cheese",
        "Tim": "Mushroom"
    }
    return favourite_pizza

# Create Dashboard Page
@app.route("/dashboard", methods = ["GET", "POST"])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    
    if request.method == "POST":
        name_to_update.name = request.form["name"]
        name_to_update.email = request.form["email"]
        name_to_update.favorite_color = request.form["favorite_color"]
        name_to_update.username = request.form["username"]
        name_to_update.about_author = request.form["about_author"]
        name_to_update.profile_pic = request.files["profile_pic"]
        

        
        
        # Grab Image Name
        pic_filename = secure_filename(name_to_update.profile_pic.filename)
        # Set UUID
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        # Save the image file
        saver = request.files["profile_pic"]
        
        
        # Change pic_name to string to save to db
        name_to_update.profile_pic = pic_name

        try:
            db.session.commit()
            saver.save(os.path.join(app.config["UPLOAD_FOLDER"]), pic_name)
            flash("User Updated Successfully")
            return render_template("dashboard.html", form = form, name_to_update = name_to_update)
        except:
            flash("Error! Looks like there was a Problem!")
            return render_template("dashboard.html", form = form, name_to_update = name_to_update)
    
    else:
        return render_template("dashboard.html", form = form, name_to_update = name_to_update, id = id)
    
@app.route("/delete/<int:id>")

def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully!")

        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html", form = form, name = name, our_users = our_users)
        


    except:
        flash("Whoops! There was a problem deleting user, try again...")
        return render_template("add_user.html", form = form, name = name, our_users = our_users)


@app.route("/posts/delete/<int:id>")
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:

        try:
            db.session.delete(post_to_delete)
            db.session.commit()

            # Return a message
            flash("Blog post was deleted!")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts = posts)

        except:
            flash("Whoops! There was a problem deleting the post, try again...")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts = posts)
    else:
            flash("You aren't authorized to delete that post!")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts = posts)
    
    
@app.route("/posts/edit/<int:id>", methods = ["GET", "POST"])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        # post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data
        # Update Database
        db.session.add(post)
        db.session.commit()
        flash("Post has been updated!")
        return redirect(url_for("post", id=post.id))
    
    if current_user.id == post.poster_id:

        form.title.data = post.title
        # form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template("edit_post.html", form = form)
    
    else:
        flash("You aren't authorized to edit this post!")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts = posts)

# Create Login Page
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username = form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successfull!")
                return redirect(url_for("dashboard"))
            
            else:
                flash("Wrong Password - Try Again!")
        
        else:
            flash("That User Doesn't Exist! Try Again...")
            
    return render_template("login.html", form = form)

# Create a route decorator
@app.route("/")
def index():


    first_name = "John"
    stuff = "This is <strong>Bold</strong> Text!"


    favourite_pizza = ["pepperoni", "cheese", "salami", 41]

    return render_template("index.html", first_name = first_name, stuff = stuff, favourite_pizza = favourite_pizza)


# Internal Server Error
@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

# Create Logout Page
@app.route("/logout", methods = ["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out! Thanks for stopping by...")
    return redirect(url_for("login"))

# Create Name Page
@app.route("/name", methods=["GET", "POST"])
def name():
    name = None
    form = NamerForm()
    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ""
        flash("Form Submitted Successfully!")
    return render_template("name.html", name = name, form = form)
     

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/posts/<int:id>")
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template("post.html", post = post)

@app.route("/posts")
def posts():
    # Grab all the posts from the database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts = posts)

# Pass stuff to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form = form)

# Create search function
@app.route("/search", methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        # Get data from submitted form
        post.searched = form.searched.data
        # Query the database
        posts = posts.filter(Posts.content.like("%" + post.searched + "%"))
        posts = posts.order_by(Posts.title).all()

        return render_template("search.html", form = form, searched = post.searched, posts = posts)
    

# Create Password Test Page
@app.route("/test_pw", methods=["GET", "POST"])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()


    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        # Clear the form
        form.email.data = ""
        form.password_hash.data = ""

        # Look up user by email address
        pw_to_check = Users.query.filter_by(email = email).first()
        
        # CHeck Hashed Password
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template("test_pw.html", email = email, password = password, form = form, pw_to_check = pw_to_check, passed = passed)
     

# Update Database Record
@app.route("/update/<int:id>", methods = ["GET", "POST"])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    
    if request.method == "POST":
        name_to_update.name = request.form["name"]
        name_to_update.email = request.form["email"]
        name_to_update.favorite_color = request.form["favorite_color"]
        name_to_update.username = request.form["username"]
        try:
            db.session.commit()
            flash("User Updated Successfully")
            return render_template("update.html", form = form, name_to_update = name_to_update, id = id)
        except:
            flash("Error! Looks like there was a Problem!")
            return render_template("update.html", form = form, name_to_update = name_to_update, id = id)
    
    else:
        return render_template("update.html", form = form, name_to_update = name_to_update, id = id)


@app.route("/user/<name>")
def user(name):
    return render_template("user.html", user_name = name)









      




#################
### DB STUFF ####
#################


# Create a Blog Post Model
class Posts(db.Model):

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default = datetime.now(timezone.utc))
    slug = db.Column(db.String(255))
    # Foreign key to link users (refer to primary key of users)
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))

# Create Users Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique = True)
    name = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(120), nullable = False, unique = True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500), nullable = True)
    date_added = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    profile_pic = db.Column(db.String(255), nullable = True)
    # Do some password stuff
    password_hash = db.Column(db.String(128))

    # User can have many posts
    posts = db.relationship("Posts", backref = "poster")

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create A String
    def __repr__(self):
        return "<Name %r>" % self.name
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Datenbank wurde erstellt.")
    app.run(host ="0.0.0.0", port = 5555, debug = True)