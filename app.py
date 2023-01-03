from flask import Flask, request, g, session, redirect, url_for, render_template
from flask import render_template_string, jsonify
from flask_github import GitHub
import json
import requests

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URI = 'sqlite:////tmp/github-flask.db'
SECRET_KEY = 'development key'
DEBUG = True

# Set these values
GITHUB_CLIENT_ID = 'e1d2aa8102db9a9bdb2f'
GITHUB_CLIENT_SECRET = os.environ['githubclientsec']

# setup flask
app = Flask(__name__)
app.config.from_object(__name__)

# setup github-flask
github = GitHub(app)

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/')
def index():
    if g.user:
        userss =(github.get('/user'))
        avatar = userss["avatar_url"]
        name = userss["name"]
        #homepage can be inserted here
        t = 'homepagee.html'
        render_template('homepagee.html',avatar=avatar,name=name)

    else:
        #login page can be inserted here
        #t = 'Hello! <a href="{{ url_for("login") }}">Login with github</a>'
        return render_template('index.html')

    return render_template(t,avatar=avatar,name=name)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token

    # Not necessary to get these details here
    # but it helps humans to identify users easily.
    g.user = user
    github_user = github.get('/user')
    user.github_id = github_user['id']
    user.github_login = github_user['login']

    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        #login form can be inserted here
        return github.authorize()
    else:
        return 'Already logged in'


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user')
def user(): #this function is used to get user's details
    #we can put th profile section here
    userss =(github.get('/user'))
    repos= github.get('/user/repos')
    repolist = []
    for repo in repos:
        repolist.append(repo['name'])
    avatar = userss["avatar_url"]
    name = userss["name"]
    email = userss["email"]
    bio = userss["bio"]
    pubic_repos = userss["public_repos"]
    followers = userss["followers"]
    following = userss["following"]
    no_repos = userss["public_repos"]
    
    return render_template('desktop___1.html', 
                            avatar=avatar,
                            name=name,
                            bio=bio,
                            followers= followers,
                            following=following,
                            public_repos=pubic_repos,
                            email=email, 
                            repolist=repolist,
                            repos=repos,
                            no_repos=no_repos)
    #return jsonify(github.get('/user'))

@app.route('/user/<username>')
def anyuser(username):
    userss =(github.get(f'/user/{username}'))
    repos= github.get(f'/user/{username}/repos')
    repolist = []
    for repo in repos:
        repolist.append(repo['name'])
    avatar = userss["avatar_url"]
    name = userss["name"]
    email = userss["email"]
    bio = userss["bio"]
    pubic_repos = userss["public_repos"]
    followers = userss["followers"]
    following = userss["following"]
    no_repos = userss["public_repos"]
    
    return render_template('anyprofile.html', 
                            avatar=avatar,
                            name=name,
                            bio=bio,
                            followers= followers,
                            following=following,
                            public_repos=pubic_repos,
                            email=email, 
                            repolist=repolist,
                            repos=repos,
                            no_repos=no_repos)
    #return jsonify(github.get('/users/{}'.format(username)))


@app.route('/user/followers')
def followers():
    followersjson = (github.get('/user/followers'))

    #followerslist,img =[],[]
    dict = {}
    for follower in followersjson:
        #followerslist.append(follower['login'])
        #img.append(follower['avatar_url'])
        dict[follower['login']] = [follower['avatar_url'],follower['html_url']]
    return render_template('followers.html',
                            followersdict=dict,
                            followersjson=followersjson,
                            url_for=url_for,
                            anyuser=anyuser)
    
@app.route('/user/following')
def following():
    followingjson = (github.get('/user/following'))
    followingdict = {}
    for following in followingjson:
        #followinglist.append(following['login'])
        followingdict[following['login']] = [following['avatar_url'],following['html_url']]
    return render_template('following.html', followingjson=followingjson,followingdict=followingdict)



@app.route('/repo')
def repo():
    return jsonify(github.get('/repos/rpj09/FRIDAY-virtual-assistant'))


if __name__ == '__main__':
    init_db()
    #app.run(debug=True)
    app.run(host="0.0.0.0",port=8000)