import os
import uuid

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
import pandas as pd
import numpy as np
import tempfile
from .calc import get_cal_res
from .auth import login_required
from .db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)

@bp.route('/cal_result', methods=['GET', 'POST'])
def result():
    result = None
    if request.method == 'POST':
        print(request.form)
        alpha = float(request.form['alpha'])
        pp_S = float(request.form['pp_S'])
        pp_Q = float(request.form['pp_Q'])
        pp_K = float(request.form['pp_K'])
        print(pp_S,pp_Q,pp_K)
        file = request.files['df']
        if file:
            # 获取当前用户的用户名
            username = g.user['username']
            # 获取脚本所在的目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # 创建存放文件的目录
            dir_path = os.path.join(base_dir, 'files', username)
            os.makedirs(dir_path, exist_ok=True)

            # 生成随机文件名
            filename = str(uuid.uuid4()) + '.xlsx'
            file_path = os.path.join(dir_path, filename)

            # 保存文件
            file.save(file_path)
            # 使用pandas读取Excel文件
            df = pd.read_excel(file_path)
            # print(df)
            df.fillna(0, inplace=True)
            print(df.shape)
        P_v = [float(x) for x in request.form['P_v'].split(',')]
        P = np.array(P_v).reshape(len(P_v), 1)

        # 传入你的函数
        df_成分,chengben = get_cal_res(alpha, pp_S, pp_Q, pp_K, df, P)
    return render_template('blog/result.html', result=chengben,df=df_成分)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
