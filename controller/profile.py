# controller responsible for manipulating user's profile
from common import endsWithList
from flask import Blueprint, request, session, render_template
from model import User, AllReport

profile = Blueprint('profile', __name__)


@profile.route('/profile', methods=['GET'])
def get_profile():
    if session.get('isLogin') != 'true':
        return 'permission-denied'

    try:
        result = User.find_by_id(session.get('user_id'))
        msg_count = AllReport.count_report_by_auth(session.get('username'))
        return render_template('profile.html', user=result[0], msg_count=msg_count)
    except IOError as e:
        print(e)
        return 'fail'


@profile.route('/profile/avatar', methods=['POST'])
def upload_avatar():
    if session.get('isLogin') != 'true':
        return 'permission-denied'

    img = request.files['avatar']
    if img is None:
        return 'invalid'
    filename = f'user{session.get("user_id")}_' + img.filename
    if not endsWithList(filename, ['png', 'jpg', 'jpeg', 'gif']):
        return 'invalid'

    try:
        img.save('./static/img/' + filename)
        User.change_avatar(session.get('user_id'), filename)
        session['avatar'] = filename  # update session, or avatar on the nav bar won't change
        return 'success'
    except IOError as e:
        print(e)
        return 'fail'


@profile.route('/profile', methods=['PUT'])
def change_profile():
    if session.get('isLogin') != 'true':
        return 'permission-denied'

    # action -> nickname, password
    action = request.form.get('action')

    if action == 'nickname':
        new_nickname = request.form.get('nickname')
        if new_nickname is not None:
            try:
                User.change_nickname(session.get('user_id'), new_nickname)
                session['nickname'] = new_nickname
                return 'success'
            except IOError as e:
                print(e)
                return 'fail'
    elif action == 'password':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        try:
            result = User.find_by_id(session.get('user_id'))
            if len(result) == 1 and result[0].password == old_password \
                    and new_password is not None and len(new_password) == 32:
                User.change_password(session.get('user_id'), new_password)
                return 'success'
            else:
                return 'wrong'
        except IOError as e:
            print(e)
            return 'fail'
    return 'invalid'
