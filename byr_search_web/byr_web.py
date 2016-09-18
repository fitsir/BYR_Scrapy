# -*- coding: utf-8 -*-
import os

from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

db = SQLAlchemy(app)
app.secret_key = 'super secret key'
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql://******:******@*.*.*.*:3306/byr?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


class section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.INTEGER, primary_key=True)
    url = db.Column(db.VARCHAR(60))
    name = db.Column(db.VARCHAR(50))


class article_list(db.Model):
    __tablename__ = 'article_list'
    id = db.Column(db.INTEGER, primary_key=True)
    uptime = db.Column(db.DATE)
    hot = db.Column(db.INTEGER)
    author = db.Column(db.VARCHAR(50))
    title = db.Column(db.VARCHAR(100))
    url = db.Column(db.VARCHAR(80), unique=True)


class article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.INTEGER, primary_key=True)
    url = db.Column(db.VARCHAR(80))
    text = db.Column(db.TEXT)


@app.route('/')
def index():
    return render_template('show_entries.html')


@app.route('/', methods=['POST'])
def search():
    key = request.form['key'].strip()
    selected = request.form['select'].strip()
    print(key)
    print('start searching...')
    if key is not '':
        if selected == 'author':
            results = article_list.query.filter_by(author=key).all()
        elif selected == 'title':
            results = article_list.query.filter(
                article_list.title.like("%%%s%%" % key)).all()
        elif selected == 'text':
            results = article.query.filter(
                article.title.like("%%%s%%" % key)).all()
        elif selected == 'uptime':
            results = article_list.query.filter(
                article_list.uptime.like("%%%s%%" % key)).all()
        else:
            results = None
        if results is not None:
            lenth = len(results)
#             texts = []
#             for result in results:
#                 text = article.query.filter_by(url=result.url).first()
#                 texts.append(text)
#             paras = zip(results, texts)
            paras = results
            print('search done')
            return render_template('show_entries.html', paras=paras, key_word=key, lenth=lenth)

    return render_template('show_entries.html')


@app.errorhandler(404)
def page_not_found(error):
    return redirect('/')


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
