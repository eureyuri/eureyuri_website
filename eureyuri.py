# https://charlesleifer.com/blog/how-to-make-a-flask-blog-in-one-hour-or-less/
# https://qiita.com/colorrabbit/items/18db3c97734f32ebdfde
# https://devcenter.heroku.com/articles/getting-started-with-python#define-config-vars
# https://about.gitlab.com/handbook/markdown-guide/


from flask import Flask, render_template, abort, flash, Markup, redirect, request, Response, session, url_for
from flask_security import login_required
from flask_bcrypt import Bcrypt
import sys

# blog
import datetime
import functools
import os
import re
import urllib
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from peewee import *
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from playhouse.postgres_ext import *
from dotenv import load_dotenv


load_dotenv()
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
APP_DIR = os.path.dirname(os.path.realpath(__file__))

try:
    if (sys.argv[1] is "l"):
        DATABASE = 'sqliteext:///%s' % os.path.join(APP_DIR, 'blog.db')
except Exception as e:
    DATABASE = os.environ['DATABASE_URL']

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]  # Used by Flask to encrypt session cookie.
SITE_WIDTH = 800


app = Flask(__name__)
app.config.from_object(__name__)
bcrypt = Bcrypt(app)

flask_db = FlaskDB(app)
database = flask_db.database

oembed_providers = bootstrap_basic(OEmbedCache())


class Entry(flask_db.Model):
    title = CharField()
    slug = CharField(unique=True)
    content = TextField()
    published = BooleanField(index=True)
    timestamp = DateTimeField(default=datetime.datetime.now, index=True)

    @property
    def html_content(self):
        """
        Generate HTML representation of the markdown-formatted blog entry,
        and also convert any media URLs into rich media objects such as video
        players or images.
        """
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.content, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH'])
        return Markup(oembed_content)

    def save(self, *args, **kwargs):
        # Generate a URL-friendly representation of the entry's title.
        if not self.slug:
            self.slug = re.sub(r'[^\w]+', '-', self.title.lower()).strip('-')
        ret = super(Entry, self).save(*args, **kwargs)

        # Store search content.
        # self.update_search_index()
        return ret

    # def update_search_index(self):
    #     # Create a row in the FTSEntry table with the post content. This will
    #     # allow us to use SQLite's awesome full-text search extension to
    #     # search our entries.
    #     exists = (FTSEntry
    #               .select(FTSEntry.docid)
    #               .where(FTSEntry.docid == self.id)
    #               .exists())
    #     content = '\n'.join((self.title, self.content))
    #     if exists:
    #         (FTSEntry
    #          .update({FTSEntry.content: content})
    #          .where(FTSEntry.docid == self.id)
    #          .execute())
    #     else:
    #         FTSEntry.insert({
    #             FTSEntry.docid: self.id,
    #             FTSEntry.content: content}).execute()

    @classmethod
    def public(cls):
        return Entry.select().where(Entry.published == True)

    @classmethod
    def drafts(cls):
        return Entry.select().where(Entry.published == False)

    # @classmethod
    # def search(cls, query):
    #     words = [word.strip() for word in query.split() if word.strip()]
    #     if not words:
    #         # Return an empty query.
    #         return Entry.noop()
    #     else:
    #         search = ' '.join(words)
    #
    #     # Query the full-text search index for entries matching the given
    #     # search query, then join the actual Entry data on the matching
    #     # search result.
    #     return (Entry
    #             .select(Entry, FTSEntry.rank().alias('score'))
    #             .join(FTSEntry, on=(Entry.id == FTSEntry.docid))
    #             .where(
    #                 FTSEntry.match(search) &
    #                 (Entry.published == True))
    #             .order_by(SQL('score')))


# class FTSEntry(FTSModel):
#     content = TextField()
#
#     class Meta:
#         database = database


@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return render_template("notfound.html")


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/about', methods=["GET"])
def about():
    return render_template("about.html")


@app.route('/interests', methods=["GET"])
def interests():
    return render_template("interests.html")


def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner

@app.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        pw_hash = bcrypt.generate_password_hash(password)
        if bcrypt.check_password_hash(pw_hash, app.config['ADMIN_PASSWORD']):
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            return redirect(next_url or url_for('blog'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)

@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')

@app.route('/blog/')
def blog():
    # search_query = request.args.get('q')
    # if search_query:
    #     query = Entry.search(search_query)
    # else:
    query = Entry.public().order_by(Entry.timestamp.desc())

    # The `object_list` helper will take a base query and then handle
    # paginating the results if there are more than 20. For more info see
    # the docs:
    # http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#object_list
    return object_list(
        'blog.html',
        query,
        search="",
        check_bounds=False)


def _create_or_edit(entry, template):
    if request.method == 'POST':
        entry.title = request.form.get('title') or ''
        entry.content = request.form.get('content') or ''
        entry.published = request.form.get('published') or False
        if not (entry.title and entry.content):
            flash('Title and Content are required.', 'danger')
        else:
            # Wrap the call to save in a transaction so we can roll it back
            # cleanly in the event of an integrity error.
            try:
                with database.atomic():
                    entry.save()
            except IntegrityError:
                flash('Error: this title is already in use.', 'danger')
            else:
                flash('Entry saved successfully.', 'success')
                if entry.published:
                    return redirect(url_for('detail', slug=entry.slug))
                else:
                    return redirect(url_for('edit', slug=entry.slug))

    return render_template(template, entry=entry)

@app.route('/blog/create/', methods=['GET', 'POST'])
@login_required
def create():
    return _create_or_edit(Entry(title='', content=''), 'create.html')

@app.route('/blog/drafts/')
@login_required
def drafts():
    query = Entry.drafts().order_by(Entry.timestamp.desc())
    return object_list('blog.html', query, check_bounds=False)

@app.route('/blog/<slug>/')
def detail(slug):
    if session.get('logged_in'):
        query = Entry.select()
    else:
        query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('detail.html', entry=entry)

@app.route('/blog/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(Entry, Entry.slug == slug)
    return _create_or_edit(entry, 'edit.html')

@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    # We'll use this template filter in the pagination include. This filter
    # will take the current URL and allow us to preserve the arguments in the
    # querystring while replacing any that we need to overwrite. For instance
    # if your URL is /?q=search+query&page=2 and we want to preserve the search
    # term but make a link to page 3, this filter will allow us to do that.
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)


def main():
    database.create_tables([Entry])
    app.run(debug=True)


if __name__ == '__main__':
    main()
