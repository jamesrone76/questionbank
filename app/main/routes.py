from flask import render_template, flash, redirect, url_for, request
from flask import current_app, g
from app import db
from flask_login import current_user, login_required
from app.models import User
from datetime import datetime
from app.main.forms import EditProfileForm, QuestionForm, SearchForm
from app.models import Question
from app.main import bp


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(body=form.question.data, author=current_user)
        db.session.add(question)
        db.session.commit()
        flash('Your question has been added to the bank.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    questions = current_user.questions.order_by(
        Question.timestamp.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    next_url = url_for('main.index', page=questions.next_num) \
        if questions.has_next else None
    prev_url = url_for('main.index', page=questions.prev_num) \
        if questions.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           questions=questions.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    questions = user.questions.order_by(Question.timestamp.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=questions.next_num) \
        if questions.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=questions.prev_num) \
        if questions.has_prev else None
    return render_template('user.html', user=user, questions=questions.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.timestamp.desc()).paginate(
        page, current_app.config['QUESTIONS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=questions.next_num) \
        if questions.has_next else None
    prev_url = url_for('main.explore', page=questions.prev_num) \
        if questions.has_prev else None
    return render_template('index.html', title='Explore',
                           questions=questions.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    questions, total = Question.search(g.search_form.q.data, page,
                                       current_app.config['QUESTIONS_PER_PAGE']
                                       )
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['QUESTIONS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', questions=questions,
                           next_url=next_url, prev_url=prev_url)
