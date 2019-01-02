from flask import (Flask, g, render_template, flash, redirect, url_for,
                   request, abort)
from flask_bcrypt import check_password_hash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from slugify import slugify

import forms
import models


DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = 'djkcndjcnjkdscndjscdjsncjadscascdqwjdqw'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    """ Get user """
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """ Before request open database """
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """ after request close db """
    g.db.close()
    return response


@app.route('/login', methods=('GET', 'POST'))
def login():
    """ Login to site """
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Your username or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """ Logout from site """
    logout_user()
    flash("You've been logged out! Come back soon!", "success")
    return redirect(url_for('index'))


@app.route('/entry', methods=('GET', 'POST'))
@login_required
def add():
    """ Add an entry to database """
    # if the form is submitted
    form = forms.EntryForm()
    tag_form = forms.TagForm()
    if form.validate_on_submit():
        entry = models.Entry.create(
            title=form.title.data,
            date=form.date.data,
            duration=form.duration.data,
            learned=form.learned.data,
            resources=form.resources.data,
            slug=slugify(form.title.data)
        )
        if tag_form.validate_on_submit():
            tags = tag_form.tags.data
            split_tags = [tag.strip() for tag in tags.split(',')]
            for split_tag in split_tags:
                if len(split_tag) > 0:
                    models.Tag.create(
                        tag=split_tag,
                        entry=entry,
                        slug=slugify(split_tag)
                    )
            # tell them the entry was created
            flash('Entry created')
            return redirect(url_for('index'))
    # forward to the details page
    return render_template('new.html', form=form, tag_form=tag_form)


@app.route('/entries/<slug>')
def detail(slug):
    """Shows the details of a specific blog post"""
    try:
        entry = models.Entry.select().where(models.Entry.slug == slug).get()
    except models.DoesNotExist:
        abort(404)
    return render_template('detail.html', entry=entry)


@app.route("/delete/<slug>")
@login_required
def delete(slug):
    """Add the ability to delete a journal entry."""
    try:
        entry = models.Entry.select().where(models.Entry.slug == slug).get()
    except models.DoesNotExist:
        abort(404)
    else:
        entry.delete_instance(recursive=True)
        flash("Entry deleted.", "success")
    return redirect(url_for('index'))


@app.route("/entries/edit/<slug>", methods=('POST', 'GET'))
@login_required
def edit(slug):
    """ Add the ability to edit an entry """
    try:
        entry = models.Entry.select().where(models.Entry.slug == slug).get()
        tags = models.Tag.select().where(models.Tag.entry == entry)
        tag_list = []
        for tag in tags:
            tag_list.append(tag.tag)
        entry_tags = ", ".join(tag_list)
    except models.DoesNotExist:
        abort(404)
    else:
        form = forms.EntryForm(obj=entry)
        tag_form = forms.TagForm(tags=entry_tags)
        if request.method == 'POST':
            if form.validate_on_submit():
                entry.title = form.title.data
                entry.date = form.date.data
                entry.duration = form.duration.data
                entry.learned = form.learned.data
                entry.resources = form.resources.data
                entry.slug = slugify(entry.title)
                entry.save()
                if tag_form.validate_on_submit():
                    q = models.Tag.delete().where(models.Tag.entry == entry)
                    q.execute()
                    tags = tag_form.tags.data
                    split_tags = [tag.strip() for tag in tags.split(',')]
                    for split_tag in split_tags:
                        if len(split_tag) > 0:
                            models.Tag.create(
                                tag=split_tag,
                                entry=entry,
                                slug=slugify(split_tag)
                            )
                    flash('Entry updated', "success")
                    return redirect(url_for('index'))
    # forward to the details page
    return render_template('new.html', form=form, tag_form=tag_form,
                           entry=entry, entry_tags=entry_tags)


@app.route("/tags")
def all_tags():
    """ Collects all the unique tags to display"""
    unique_tags = []
    all_tags = models.Tag.select(models.Tag.tag, models.Tag.slug).distinct()
    for tag in all_tags:
        if tag.tag not in unique_tags:
            unique_tags.append(tag)
    return render_template('all_tags.html', unique_tags=unique_tags)


@app.route("/tags/<slug>")
def tags(slug):
    """ Renders tags/'tag' search page"""
    entries = models.Tag.select().distinct().where(models.Tag.slug == slug)
    return render_template('tags.html', entries=entries, slug=slug)


@app.errorhandler(404)
def not_found(error):
    """Renders a user friendly page if a 404 occurs"""
    return render_template('404.html'), 404


@app.route('/')
def index():
    """ Index page for stream of posts"""
    entries = models.Entry.select()
    return render_template('index.html', entries=entries)

if __name__ == '__main__':
    # Creates a user
    models.initialize()
    try:
        models.User.create_user(
            username='admin',
            password='password',
        )
    except ValueError:
        pass

    app.run(debug=DEBUG, host=HOST, port=PORT)
