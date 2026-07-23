import os
import re
import json
import secrets
import sqlite3
import mimetypes
import uuid
from html import escape
from functools import wraps
from datetime import datetime, timezone, timedelta

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


mimetypes.add_type("image/webp", ".webp")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "slowhorse.sqlite3")
DRIVER_DIR = os.path.join(BASE_DIR, "source", "driver")
DRIVER_STANDINGS_FILE = os.path.join(DRIVER_DIR, "drivers.md")
RACE_RESULTS_FILE = os.path.join(BASE_DIR, "source", "results", "race_results_2026.md")
RACE_RESULTS_JSON_FILE = os.path.join(BASE_DIR, "source", "results", "race_results_2026.json")
RACE_IMAGE_DIR = os.path.join(BASE_DIR, "source", "results", "img")
MUSIC_DIR = os.path.join(BASE_DIR, "source", "music")
DISCUSSION_UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "replies")
MEME_FILE = os.path.join(BASE_DIR, "meme", "meme.md")
HONOR_FILE = os.path.join(BASE_DIR, "meme", "honor.md")
PRINCIPLE_FILE = os.path.join(BASE_DIR, "source", "principle", "principle.md")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff]{2,24}$")
BEIJING_TZ = timezone(timedelta(hours=8))
INITIAL_POINTS = 1000
MIN_STAKE = 20
MAX_STAKE = 200
MIN_ANSWER_BET = 20
MAX_ANSWER_BET = 200
ALLOWED_REPLY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MUSIC_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a"}

TEAM_ACCENTS = {
    "Mercedes": "#00d2be",
    "Ferrari": "#e10600",
    "McLaren": "#ff8c1a",
    "Red Bull": "#2f65ff",
    "Red Bull Racing": "#2f65ff",
    "Racing Bulls": "#6c7cff",
    "Alpine": "#ff87bc",
    "Williams": "#00a3ff",
    "Haas": "#f0f0f0",
    "Haas F1 Team": "#f0f0f0",
    "Audi": "#39ff14",
    "Aston Martin": "#006f62",
    "Cadillac": "#d6b36a",
}

FAN_DRIVERS = [
    {"code": "PIA", "number": "81", "team_class": "mclaren"},
    {"code": "NOR", "number": "1", "team_class": "mclaren"},
    {"code": "VER", "number": "3", "team_class": "redbull"},
    {"code": "HAD", "number": "6", "team_class": "redbull"},
    {"code": "LEC", "number": "16", "team_class": "ferrari"},
    {"code": "HAM", "number": "44", "team_class": "ferrari"},
    {"code": "ANT", "number": "12", "team_class": "mercedes"},
    {"code": "RUS", "number": "63", "team_class": "mercedes"},
    {"code": "ALO", "number": "14", "team_class": "aston"},
    {"code": "STR", "number": "18", "team_class": "aston"},
    {"code": "GAS", "number": "10", "team_class": "alpine"},
    {"code": "COL", "number": "43", "team_class": "alpine"},
    {"code": "SAI", "number": "55", "team_class": "williams"},
    {"code": "ALB", "number": "23", "team_class": "williams"},
    {"code": "HUL", "number": "27", "team_class": "audi"},
    {"code": "BOR", "number": "5", "team_class": "audi"},
    {"code": "PER", "number": "11", "team_class": "cadillac"},
    {"code": "BOT", "number": "77", "team_class": "cadillac"},
    {"code": "OCO", "number": "31", "team_class": "haas"},
    {"code": "BEA", "number": "87", "team_class": "haas"},
    {"code": "LAW", "number": "30", "team_class": "racingbulls"},
    {"code": "LIN", "number": "41", "team_class": "racingbulls"},
]

RACE_CHINESE_NAMES = {
    "Australia": "澳大利亚大奖赛",
    "China": "中国大奖赛",
    "Japan": "日本大奖赛",
    "Miami": "迈阿密大奖赛",
    "Canada": "加拿大大奖赛",
    "Monaco": "摩纳哥大奖赛",
    "Barcelona-Catalunya": "巴塞罗那-加泰罗尼亚大奖赛",
    "Austria": "奥地利大奖赛",
    "Great Britain": "英国大奖赛",
    "Belgium": "比利时大奖赛",
    "Hungary": "匈牙利大奖赛",
    "Netherlands": "荷兰大奖赛",
    "Italy": "意大利大奖赛",
    "Spain": "西班牙大奖赛",
    "Azerbaijan": "阿塞拜疆大奖赛",
    "Singapore": "新加坡大奖赛",
    "United States": "美国大奖赛",
    "Mexico": "墨西哥大奖赛",
    "Brazil": "巴西大奖赛",
    "Las Vegas": "拉斯维加斯大奖赛",
    "Qatar": "卡塔尔大奖赛",
    "Abu Dhabi": "阿布扎比大奖赛",
}

RACE_CHINESE_NAMES.update(
    {
        "Australia": "澳大利亚大奖赛",
        "China": "中国大奖赛",
        "Japan": "日本大奖赛",
        "Miami": "迈阿密大奖赛",
        "Canada": "加拿大大奖赛",
        "Monaco": "摩纳哥大奖赛",
        "Barcelona-Catalunya": "西班牙大奖赛",
        "Austria": "奥地利大奖赛",
        "Great Britain": "英国大奖赛",
        "Belgium": "比利时大奖赛",
        "Hungary": "匈牙利大奖赛",
        "Netherlands": "荷兰大奖赛",
        "Italy": "意大利大奖赛",
        "Spain": "西班牙大奖赛",
        "Azerbaijan": "阿塞拜疆大奖赛",
        "Singapore": "新加坡大奖赛",
        "United States": "美国大奖赛",
        "Mexico": "墨西哥城大奖赛",
        "Brazil": "圣保罗大奖赛",
        "Las Vegas": "拉斯维加斯大奖赛",
        "Qatar": "卡塔尔大奖赛",
        "Abu Dhabi": "阿布扎比大奖赛",
    }
)


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-secret"),
        DATABASE=os.environ.get("DATABASE", DATABASE),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 2,
        TEMPLATES_AUTO_RELOAD=True,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    os.makedirs(DISCUSSION_UPLOAD_DIR, exist_ok=True)

    @app.before_request
    def load_logged_in_user():
        g.csrf_token = session.setdefault("csrf_token", secrets.token_urlsafe(32))
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            g.user = query_db(
                """
                select id, username, fan_driver, points, login_days, last_login_award_date, created_at
                from users
                where id = ?
                """,
                (user_id,),
                one=True,
            )

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.context_processor
    def inject_global_template_data():
        return {"music_tracks": list_music_tracks(), "fan_driver_by_code": fan_driver_by_code()}

    @app.route("/")
    def index():
        return render_template("index.html", next_race=next_upcoming_race())

    @app.route("/drivers")
    def drivers():
        drivers_data = build_driver_cards()
        return render_template("drivers.html", drivers=drivers_data, standings=drivers_data)

    @app.route("/races")
    def races():
        races_data = build_race_cards()
        completed_count = sum(1 for race in races_data if race["is_completed"])
        return render_template(
            "races.html",
            races=races_data,
            completed_count=completed_count,
            now=now_beijing(),
        )

    @app.route("/predict")
    @login_required
    def predict_page():
        tab = request.args.get("tab", "answer")
        question_filter = request.args.get("filter", "all")
        race = next_upcoming_race()
        questions = filter_questions(list_questions(), question_filter)
        leaderboard = query_db(
            "select username, fan_driver, points from users order by points desc, username asc limit 50"
        )
        return render_template(
            "predict.html",
            tab=tab,
            question_filter=question_filter,
            race=race,
            questions=questions,
            leaderboard=leaderboard,
            min_stake=MIN_STAKE,
            max_stake=MAX_STAKE,
            min_answer_bet=MIN_ANSWER_BET,
            max_answer_bet=MAX_ANSWER_BET,
            principle_html=render_principle_html(),
            now=now_beijing(),
        )

    @app.route("/discussion")
    @login_required
    def discussion():
        posts = list_discussion_posts()
        return render_template("discussion.html", posts=posts, memes=list_meme_lines())

    @app.route("/profile")
    @login_required
    def profile():
        profile_data = build_profile_data(g.user["id"])
        honor_award = session.pop("honor_award", None)
        return render_template(
            "profile.html",
            profile=profile_data,
            honor_award=honor_award,
            fan_drivers=FAN_DRIVERS,
        )

    @app.route("/profile/fan", methods=("POST",))
    @login_required
    def update_fan_driver():
        validate_csrf()
        fan_driver = request.form.get("fan_driver", "").strip().upper()
        if fan_driver not in fan_driver_by_code():
            flash("请选择有效车手粉丝团。", "error")
            return redirect(url_for("profile"))

        execute_db("update users set fan_driver = ? where id = ?", (fan_driver, g.user["id"]))
        flash("粉丝团已更新。", "success")
        return redirect(url_for("profile"))

    @app.route("/discussion/new", methods=("POST",))
    @login_required
    def create_discussion_post():
        validate_csrf()
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        error = validate_post_input(title, body)
        if error:
            flash(error, "error")
            return redirect(url_for("discussion"))

        execute_db(
            """
            insert into discussion_posts (user_id, title, body)
            values (?, ?, ?)
            """,
            (g.user["id"], title, body),
        )
        flash("帖子已发布。", "success")
        return redirect(url_for("discussion"))

    @app.route("/discussion/<int:post_id>")
    @login_required
    def discussion_post(post_id):
        post = get_discussion_post(post_id)
        if post is None:
            abort(404)
        replies = list_discussion_replies(post_id)
        return render_template("discussion_post.html", post=post, replies=replies, memes=list_meme_lines())

    @app.route("/discussion/<int:post_id>/reply", methods=("POST",))
    @login_required
    def create_discussion_reply(post_id):
        validate_csrf()
        post = get_discussion_post(post_id)
        if post is None:
            abort(404)

        body = request.form.get("body", "").strip()
        image = request.files.get("image")
        image_path, error = save_reply_image(image)
        if error:
            flash(error, "error")
            return redirect(url_for("discussion_post", post_id=post_id))
        if not body and not image_path:
            flash("回复内容和图片至少需要填写一项。", "error")
            return redirect(url_for("discussion_post", post_id=post_id))
        if len(body) > 2000:
            flash("回复内容不能超过 2000 个字符。", "error")
            return redirect(url_for("discussion_post", post_id=post_id))

        execute_db(
            """
            insert into discussion_replies (post_id, user_id, body, image_path)
            values (?, ?, ?, ?)
            """,
            (post_id, g.user["id"], body, image_path),
        )
        flash("回复已发布。", "success")
        return redirect(url_for("discussion_post", post_id=post_id))

    @app.route("/predict/create", methods=("POST",))
    @login_required
    def create_question():
        validate_csrf()
        race = next_upcoming_race()
        if race is None:
            flash("当前没有可出题的未来正赛。", "error")
            return redirect(url_for("predict_page", tab="create"))
        if not race_is_open(race):
            flash("本场正赛已开始，不能再出题。", "error")
            return redirect(url_for("predict_page", tab="create"))

        title = request.form.get("title", "").strip()
        stake_text = request.form.get("stake", "").strip()
        option_values = [value.strip() for value in request.form.getlist("options") if value.strip()]
        error = validate_question_input(title, stake_text, option_values)
        if error:
            flash(error, "error")
            return redirect(url_for("predict_page", tab="create"))

        stake = int(stake_text)
        user = query_db("select points from users where id = ?", (g.user["id"],), one=True)
        if user["points"] < stake:
            flash("积分不足，无法出题。", "error")
            return redirect(url_for("predict_page", tab="create"))

        db = get_db()
        cur = db.execute(
            """
            insert into questions
                (creator_id, race_round, race_name, race_start_at, title, stake)
            values (?, ?, ?, ?, ?, ?)
            """,
            (g.user["id"], race["round"], race["name"], race["start_at"], title, stake),
        )
        question_id = cur.lastrowid
        for index, label in enumerate(option_values, start=1):
            db.execute(
                "insert into question_options (question_id, label, position) values (?, ?, ?)",
                (question_id, label, index),
            )
        add_points_transaction(g.user["id"], question_id, -stake, "create_question", commit=False)
        db.commit()
        flash("出题成功，积分已进入本题奖池。", "success")
        return redirect(url_for("predict_page", tab="answer"))

    @app.route("/predict/answer/<int:question_id>", methods=("POST",))
    @login_required
    def submit_answer(question_id):
        validate_csrf()
        question = get_question(question_id)
        if question is None:
            abort(404)
        if not question_is_answerable(question):
            flash("本题已截止或不可答题。", "error")
            return redirect(url_for("predict_page", tab="answer"))

        option_id = int(request.form.get("option_id", "0") or 0)
        bet_text = request.form.get("bet", "").strip()
        error = validate_answer_bet(bet_text)
        if error:
            flash(error, "error")
            return redirect(url_for("predict_page", tab="answer"))
        bet = int(bet_text)
        option = query_db(
            "select id from question_options where id = ? and question_id = ?",
            (option_id, question_id),
            one=True,
        )
        if option is None:
            flash("请选择有效选项。", "error")
            return redirect(url_for("predict_page", tab="answer"))
        if query_db(
            "select id from answers where question_id = ? and user_id = ?",
            (question_id, g.user["id"]),
            one=True,
        ):
            flash("你已经提交过答案，不能修改。", "error")
            return redirect(url_for("predict_page", tab="answer"))

        user = query_db("select points from users where id = ?", (g.user["id"],), one=True)
        if user["points"] < bet:
            flash("积分不足，无法投注。", "error")
            return redirect(url_for("predict_page", tab="answer"))

        db = get_db()
        db.execute(
            "insert into answers (question_id, user_id, option_id, bet) values (?, ?, ?, ?)",
            (question_id, g.user["id"], option_id, bet),
        )
        add_points_transaction(g.user["id"], question_id, -bet, "answer_bet", commit=False)
        db.commit()
        flash("答案已提交。", "success")
        return redirect(url_for("predict_page", tab="answer"))

    @app.route("/predict/settle/<int:question_id>", methods=("POST",))
    @login_required
    def settle_question_route(question_id):
        validate_csrf()
        question = get_question(question_id)
        if question is None:
            abort(404)
        if question["creator_id"] != g.user["id"]:
            flash("只有出题者可以揭晓本题。", "error")
            return redirect(url_for("predict_page", tab="answer"))
        if parse_beijing_dt(question["race_start_at"]) > now_beijing():
            flash("正赛开始前不能揭晓答案。", "error")
            return redirect(url_for("predict_page", tab="answer"))
        if question["status"] == "settled":
            flash("本题已经结算。", "error")
            return redirect(url_for("predict_page", tab="answer"))

        option_id = int(request.form.get("correct_option_id", "0") or 0)
        option = query_db(
            "select id from question_options where id = ? and question_id = ?",
            (option_id, question_id),
            one=True,
        )
        if option is None:
            flash("请选择有效正确答案。", "error")
            return redirect(url_for("predict_page", tab="answer"))

        settle_question(question, option_id)
        flash("答案已揭晓，奖池已结算。", "success")
        return redirect(url_for("predict_page", tab="leaderboard"))

    @app.route("/drivers/<slug>")
    def driver_detail(slug):
        driver = next((item for item in build_driver_cards() if item["slug"] == slug), None)
        if driver is None:
            abort(404)

        return redirect(url_for("drivers"))

    @app.route("/media/home/<path:filename>")
    def home_media(filename):
        return send_from_directory(os.path.join(BASE_DIR, "source", "home"), filename)

    @app.route("/media/driver/<path:filename>")
    def driver_media(filename):
        return send_from_directory(DRIVER_DIR, filename)

    @app.route("/media/race/<path:filename>")
    def race_media(filename):
        return send_from_directory(RACE_IMAGE_DIR, filename)

    @app.route("/media/music/<path:filename>")
    def music_media(filename):
        return send_from_directory(MUSIC_DIR, filename)

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if request.method == "POST":
            validate_csrf()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            accept_terms = request.form.get("accept_terms") == "on"
            error = validate_registration(username, password, confirm_password, accept_terms)

            if error is None:
                execute_db(
                    "insert into users (username, password_hash, points) values (?, ?, ?)",
                    (username, generate_password_hash(password, method="scrypt"), INITIAL_POINTS),
                )
                flash("注册成功，请登录。", "success")
                return redirect(url_for("login"))

            flash(error, "error")

        return render_template("auth.html", mode="register")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            validate_csrf()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = query_db("select * from users where username = ?", (username,), one=True)

            if user is None or not check_password_hash(user["password_hash"], password):
                flash("用户名或密码不正确。", "error")
            else:
                session.clear()
                session.permanent = True
                session["user_id"] = user["id"]
                session["csrf_token"] = secrets.token_urlsafe(32)
                honor_award = award_daily_login(user["id"])
                if honor_award:
                    session["honor_award"] = honor_award
                flash("已登录。", "success")
                return redirect(resolve_login_redirect())

        return render_template("auth.html", mode="login")

    @app.route("/logout", methods=("POST",))
    @login_required
    def logout():
        validate_csrf()
        session.clear()
        flash("已退出登录。", "success")
        return redirect(url_for("index"))

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Initialized the database.")

    @app.cli.command("upgrade-db")
    def upgrade_db_command():
        upgrade_db()
        print("Upgraded the database.")

    return app


def validate_registration(username, password, confirm_password, accept_terms):
    if not USERNAME_RE.fullmatch(username):
        return "用户名需为 2 到 24 个中文、字母、数字或下划线。"
    if len(password) < 8:
        return "密码至少需要 8 位。"
    if password != confirm_password:
        return "两次输入的密码不一致。"
    if not accept_terms:
        return "请确认本站仅用于娱乐积分，不涉及现金、奖品或任何形式的赌博。"
    if query_db("select id from users where username = ?", (username,), one=True):
        return "这个用户名已被注册。"
    return None


def validate_csrf():
    token = request.form.get("csrf_token", "")
    if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
        abort(400)


def validate_post_input(title, body):
    if len(title) < 3 or len(title) > 80:
        return "标题需为 3 到 80 个字符。"
    if len(body) < 1 or len(body) > 5000:
        return "正文需为 1 到 5000 个字符。"
    return None


def save_reply_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None

    original = secure_filename(file_storage.filename)
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_REPLY_IMAGE_EXTENSIONS:
        return None, "回复图片仅支持 jpg、png、webp 或 gif。"

    filename = f"{uuid.uuid4().hex}{ext}"
    target = os.path.join(DISCUSSION_UPLOAD_DIR, filename)
    file_storage.save(target)
    return f"uploads/replies/{filename}", None


def list_music_tracks():
    if not os.path.exists(MUSIC_DIR):
        return []

    tracks = []
    for filename in sorted(os.listdir(MUSIC_DIR)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_MUSIC_EXTENSIONS:
            continue
        tracks.append(
            {
                "name": os.path.splitext(filename)[0],
                "url": url_for("music_media", filename=filename),
            }
        )
    return tracks


def load_principle_text():
    if not os.path.exists(PRINCIPLE_FILE):
        return ""
    with open(PRINCIPLE_FILE, encoding="utf-8") as file:
        return file.read().strip()


def fan_driver_by_code():
    return {driver["code"]: driver for driver in FAN_DRIVERS}


def render_principle_html():
    text = load_principle_text()
    if not text:
        return ""

    html = []
    list_type = None
    in_code = False
    code_lines = []

    def close_list():
        nonlocal list_type
        if list_type:
            html.append(f"</{list_type}>")
            list_type = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if line.startswith("```"):
            if in_code:
                html.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line:
            close_list()
            continue

        if line.startswith("# "):
            close_list()
            html.append(f"<h2>{escape(line[2:].strip())}</h2>")
        elif line.startswith("## "):
            close_list()
            html.append(f"<h3>{escape(line[3:].strip())}</h3>")
        elif re.match(r"^\d+\.\s+", line):
            if list_type != "ol":
                close_list()
                html.append("<ol>")
                list_type = "ol"
            html.append(f"<li>{escape(re.sub(r'^\\d+\\.\\s+', '', line))}</li>")
        elif line.startswith("- "):
            if list_type != "ul":
                close_list()
                html.append("<ul>")
                list_type = "ul"
            html.append(f"<li>{escape(line[2:].strip())}</li>")
        else:
            close_list()
            html.append(f"<p>{escape(line)}</p>")

    if in_code:
        html.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
    close_list()
    return "\n".join(html)


def list_discussion_posts():
    return query_db(
        """
        select discussion_posts.*,
               users.username,
               users.fan_driver,
               (select count(*) from discussion_replies where post_id = discussion_posts.id) as reply_count,
               coalesce(
                   (select max(created_at) from discussion_replies where post_id = discussion_posts.id),
                   discussion_posts.created_at
               ) as last_activity_at
        from discussion_posts
        join users on users.id = discussion_posts.user_id
        order by last_activity_at desc
        """
    )


def get_discussion_post(post_id):
    return query_db(
        """
        select discussion_posts.*, users.username, users.fan_driver
        from discussion_posts
        join users on users.id = discussion_posts.user_id
        where discussion_posts.id = ?
        """,
        (post_id,),
        one=True,
    )


def list_discussion_replies(post_id):
    return query_db(
        """
        select discussion_replies.*, users.username, users.fan_driver
        from discussion_replies
        join users on users.id = discussion_replies.user_id
        where discussion_replies.post_id = ?
        order by discussion_replies.created_at asc
        """,
        (post_id,),
    )


def list_meme_lines():
    if not os.path.exists(MEME_FILE):
        return []

    memes = []
    with open(MEME_FILE, encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if text.startswith("-"):
                text = text[1:].strip()
            if text:
                memes.append(text)
    return memes


def list_honors():
    if not os.path.exists(HONOR_FILE):
        return []

    honors = []
    with open(HONOR_FILE, encoding="utf-8") as file:
        for line in file:
            text = line.strip().lstrip("-").strip()
            if text:
                honors.append(text)
    return honors


def honor_for_days(login_days):
    honors = list_honors()
    if not honors or login_days <= 0:
        return None
    return honors[min(login_days, len(honors)) - 1]


def award_daily_login(user_id):
    today = now_beijing().date().isoformat()
    user = query_db(
        "select login_days, last_login_award_date from users where id = ?",
        (user_id,),
        one=True,
    )
    if user is None or user["last_login_award_date"] == today:
        return None

    login_days = int(user["login_days"] or 0) + 1
    execute_db(
        "update users set login_days = ?, last_login_award_date = ? where id = ?",
        (login_days, today, user_id),
    )
    honor = honor_for_days(login_days)
    return {"day": login_days, "honor": honor} if honor else None


def build_honor_progress(login_days):
    honors = list_honors()
    return [
        {
            "day": index,
            "name": honor,
            "unlocked": login_days >= index,
            "current": login_days >= index and index == min(login_days, len(honors)),
        }
        for index, honor in enumerate(honors, start=1)
    ]


def build_profile_data(user_id):
    user = query_db(
        """
        select id, username, fan_driver, points, login_days, last_login_award_date, created_at
        from users
        where id = ?
        """,
        (user_id,),
        one=True,
    )
    created_questions = query_db("select count(*) as total from questions where creator_id = ?", (user_id,), one=True)
    answers = query_db("select count(*) as total from answers where user_id = ?", (user_id,), one=True)
    correct_answers = query_db(
        "select count(*) as total from answers where user_id = ? and is_correct = 1",
        (user_id,),
        one=True,
    )
    posts = query_db("select count(*) as total from discussion_posts where user_id = ?", (user_id,), one=True)
    replies = query_db("select count(*) as total from discussion_replies where user_id = ?", (user_id,), one=True)
    transactions = query_db(
        """
        select amount, reason, created_at
        from point_transactions
        where user_id = ?
        order by created_at desc
        limit 8
        """,
        (user_id,),
    )
    login_days = int(user["login_days"] or 0)
    return {
        "user": user,
        "current_honor": honor_for_days(login_days),
        "honor_progress": build_honor_progress(login_days),
        "stats": {
            "created_questions": created_questions["total"],
            "answers": answers["total"],
            "correct_answers": correct_answers["total"],
            "posts": posts["total"],
            "replies": replies["total"],
        },
        "transactions": transactions,
    }


def now_beijing():
    return datetime.now(BEIJING_TZ)


def parse_beijing_dt(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=BEIJING_TZ)


def race_map_filename(round_number, race_name):
    safe_name = race_name.replace(" ", "_")
    filename = f"{round_number:02d}_{safe_name}.webp"
    return filename if os.path.exists(os.path.join(RACE_IMAGE_DIR, filename)) else None


def parse_races():
    if not os.path.exists(RACE_RESULTS_FILE):
        return []

    races = []
    current = None
    round_pattern = re.compile(r"^## Round (\d+): (.+) \((\d{4}-\d{2}-\d{2})\)")
    with open(RACE_RESULTS_FILE, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            round_match = round_pattern.match(line)
            if round_match:
                current = {
                    "round": int(round_match.group(1)),
                    "name": round_match.group(2),
                    "date": round_match.group(3),
                }
                current["name_cn"] = RACE_CHINESE_NAMES.get(current["name"], current["name"])
                current["map_image"] = race_map_filename(current["round"], current["name"])
                races.append(current)
                continue
            if current and line.startswith("Race time China:"):
                value = line.split(":", 1)[1].strip()
                current["start_at"] = value
                current["start_dt"] = parse_beijing_dt(value)
    return [race for race in races if "start_at" in race]


def next_upcoming_race():
    current = now_beijing()
    future_races = [race for race in parse_races() if race["start_dt"] > current]
    return min(future_races, key=lambda race: race["start_dt"]) if future_races else None


def race_is_open(race):
    return race is not None and race["start_dt"] > now_beijing()


def load_race_results_json():
    if not os.path.exists(RACE_RESULTS_JSON_FILE):
        return []
    with open(RACE_RESULTS_JSON_FILE, encoding="utf-8") as file:
        data = json.load(file)
    return data.get("races", [])


def build_race_cards():
    current = now_beijing()
    races = []
    for item in load_race_results_json():
        start_at = item.get("race_start_china", "")
        try:
            start_dt = parse_beijing_dt(start_at)
        except ValueError:
            continue

        name = item.get("race", "")
        results = item.get("results") or []
        is_started = start_dt <= current
        is_completed = bool(results)
        winner = results[0] if results else None
        races.append(
            {
                "round": item.get("round"),
                "name": name,
                "name_cn": RACE_CHINESE_NAMES.get(name, name),
                "start_at": start_dt.strftime("%Y-%m-%d %H:%M"),
                "start_dt": start_dt,
                "map_image": race_map_filename(item.get("round"), name),
                "race_page_url": item.get("race_page_url"),
                "result_page_url": item.get("result_page_url"),
                "results": results,
                "winner": winner,
                "is_started": is_started,
                "is_completed": is_completed,
                "can_open": is_started and is_completed,
            }
        )
    return sorted(races, key=lambda race: race["round"])


def validate_question_input(title, stake_text, options):
    if len(title) < 5 or len(title) > 120:
        return "题目需为 5 到 120 个字符。"
    if not stake_text.isdigit():
        return "出题积分必须是整数。"
    stake = int(stake_text)
    if stake < MIN_STAKE or stake > MAX_STAKE:
        return f"出题积分必须在 {MIN_STAKE} 到 {MAX_STAKE} 之间。"
    if len(options) < 2 or len(options) > 8:
        return "选项数量必须为 2 到 8 个。"
    normalized = [option.casefold() for option in options]
    if len(normalized) != len(set(normalized)):
        return "选项不能重复。"
    if any(len(option) > 80 for option in options):
        return "单个选项不能超过 80 个字符。"
    return None


def validate_answer_bet(bet_text):
    if not bet_text.isdigit():
        return "投注积分必须是整数。"
    bet = int(bet_text)
    if bet < MIN_ANSWER_BET or bet > MAX_ANSWER_BET:
        return f"投注积分必须在 {MIN_ANSWER_BET} 到 {MAX_ANSWER_BET} 之间。"
    return None


def add_points_transaction(user_id, question_id, amount, reason, commit=True):
    db = get_db()
    db.execute("update users set points = points + ? where id = ?", (amount, user_id))
    db.execute(
        """
        insert into point_transactions (user_id, question_id, amount, reason)
        values (?, ?, ?, ?)
        """,
        (user_id, question_id, amount, reason),
    )
    if commit:
        db.commit()


def get_question(question_id):
    return query_db(
        """
        select questions.*, users.username as creator_name, users.fan_driver as creator_fan_driver
        from questions
        join users on users.id = questions.creator_id
        where questions.id = ?
        """,
        (question_id,),
        one=True,
    )


def question_is_answerable(question):
    return question["status"] == "open" and parse_beijing_dt(question["race_start_at"]) > now_beijing()


def question_bucket(item):
    if item["status"] == "settled":
        return "settled"
    if item["user_answer_option_id"]:
        return "submitted"
    if item["is_answerable"]:
        return "open"
    return "pending"


def filter_questions(questions, question_filter):
    if question_filter == "all":
        return questions
    valid_filters = {"open", "submitted", "pending", "settled"}
    if question_filter not in valid_filters:
        return questions
    return [question for question in questions if question["bucket"] == question_filter]


def list_questions():
    rows = query_db(
        """
        select questions.*, users.username as creator_name, users.fan_driver as creator_fan_driver
        from questions
        join users on users.id = questions.creator_id
        order by questions.created_at desc
        """
    )
    questions = []
    for row in rows:
        item = dict(row)
        options = query_db(
            """
            select question_options.*,
                   (select count(*) from answers where answers.option_id = question_options.id) as answer_count,
                   (select coalesce(sum(bet), 0) from answers where answers.option_id = question_options.id) as bet_total
            from question_options
            where question_id = ?
            order by position asc
            """,
            (row["id"],),
        )
        answer = None
        if g.user:
            answer = query_db(
                "select option_id, bet from answers where question_id = ? and user_id = ?",
                (row["id"], g.user["id"]),
                one=True,
            )
        item["options"] = options
        item["user_answer_option_id"] = answer["option_id"] if answer else None
        item["user_answer_bet"] = answer["bet"] if answer else None
        item["answer_bet_total"] = sum(option["bet_total"] for option in options)
        item["total_pool"] = row["stake"] + item["answer_bet_total"]
        item["is_answerable"] = question_is_answerable(row)
        item["can_settle"] = (
            g.user
            and row["creator_id"] == g.user["id"]
            and row["status"] != "settled"
            and parse_beijing_dt(row["race_start_at"]) <= now_beijing()
        )
        item["bucket"] = question_bucket(item)
        questions.append(item)
    return questions


def settle_question(question, correct_option_id):
    db = get_db()
    answers = query_db("select * from answers where question_id = ?", (question["id"],))
    winners = [answer for answer in answers if answer["option_id"] == correct_option_id]
    total_pool = question["stake"] + sum(answer["bet"] for answer in answers)
    winning_bet_total = sum(answer["bet"] for answer in winners)
    awards = {}
    if winning_bet_total:
        for answer in winners:
            awards[answer["id"]] = total_pool * answer["bet"] // winning_bet_total
        remainder = total_pool - sum(awards.values())
        if remainder:
            remainder_winner = max(winners, key=lambda answer: (answer["bet"], -answer["id"]))
            awards[remainder_winner["id"]] += remainder

    for answer in answers:
        is_correct = 1 if answer["option_id"] == correct_option_id else 0
        award = awards.get(answer["id"], 0)
        db.execute(
            "update answers set is_correct = ?, points_awarded = ? where id = ?",
            (is_correct, award, answer["id"]),
        )
        if award:
            add_points_transaction(answer["user_id"], question["id"], award, "answer_correct", commit=False)

    if not winning_bet_total and total_pool:
        add_points_transaction(question["creator_id"], question["id"], total_pool, "pool_no_winner_return", commit=False)

    db.execute(
        """
        update questions
           set status = 'settled',
               correct_option_id = ?,
               settled_at = current_timestamp
         where id = ?
        """,
        (correct_option_id, question["id"]),
    )
    db.commit()


def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def initials(name):
    return "".join(part[0] for part in name.split()[:2]).upper()


def normalize_name(value):
    aliases = {
        "andrea kimi antonelli": "kimi antonelli",
        "alex albon": "alexander albon",
    }
    key = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return aliases.get(key, key)


def list_driver_images():
    images = []
    if not os.path.exists(DRIVER_DIR):
        return images

    for filename in sorted(os.listdir(DRIVER_DIR)):
        if not filename.lower().endswith(".webp"):
            continue
        parts = os.path.splitext(filename)[0].split("_")
        if len(parts) < 3:
            continue
        images.append(
            {
                "name": parts[0],
                "normalized": normalize_name(parts[0]),
                "team": parts[1],
                "number": parts[2],
                "image": filename,
            }
        )
    return images


def find_driver_image(name, images):
    normalized = normalize_name(name)
    for image in images:
        if image["normalized"] == normalized:
            return image

    last_name = normalized.split()[-1] if normalized else ""
    for image in images:
        image_tokens = image["normalized"].split()
        if image_tokens and image_tokens[-1] == last_name:
            return image
    return None


def parse_driver_standings():
    rows = []
    if not os.path.exists(DRIVER_STANDINGS_FILE):
        return rows

    with open(DRIVER_STANDINGS_FILE, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line.startswith("|") or "---" in line:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) < 4 or not cells[0].isdigit():
                continue
            rows.append(
                {
                    "rank": int(cells[0]),
                    "name": cells[1],
                    "team": cells[2],
                    "points": int(cells[3]),
                }
            )
    return rows


def team_accent(team):
    return TEAM_ACCENTS.get(team, "#d7ff36")


def build_driver_cards():
    images = list_driver_images()
    cards = []
    for row in parse_driver_standings():
        image = find_driver_image(row["name"], images)
        cards.append(
            {
                "rank": row["rank"],
                "name": row["name"],
                "team": row["team"],
                "points": row["points"],
                "number": image["number"] if image else "--",
                "image": image["image"] if image else None,
                "slug": slugify(row["name"]),
                "initials": initials(row["name"]),
                "accent": team_accent(row["team"]),
            }
        )
    return cards


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app_config("DATABASE"))
        g.db.row_factory = sqlite3.Row
    return g.db


def current_app_config(key):
    from flask import current_app

    return current_app.config[key]


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()


def init_db():
    db = get_db()
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as file:
        db.executescript(file.read())
    db.commit()


def column_exists(table, column):
    rows = query_db(f"pragma table_info({table})")
    return any(row["name"] == column for row in rows)


def upgrade_db():
    db = get_db()
    if not column_exists("users", "points"):
        db.execute(f"alter table users add column points integer not null default {INITIAL_POINTS}")
    if not column_exists("users", "login_days"):
        db.execute("alter table users add column login_days integer not null default 0")
    if not column_exists("users", "last_login_award_date"):
        db.execute("alter table users add column last_login_award_date text")
    if not column_exists("users", "fan_driver"):
        db.execute("alter table users add column fan_driver text")

    db.executescript(
        """
        create table if not exists questions (
            id integer primary key autoincrement,
            creator_id integer not null,
            race_round integer not null,
            race_name text not null,
            race_start_at text not null,
            title text not null,
            stake integer not null,
            status text not null default 'open',
            correct_option_id integer,
            settled_at text,
            created_at text not null default current_timestamp,
            foreign key (creator_id) references users (id),
            foreign key (correct_option_id) references question_options (id)
        );

        create table if not exists question_options (
            id integer primary key autoincrement,
            question_id integer not null,
            label text not null,
            position integer not null,
            foreign key (question_id) references questions (id)
        );

        create table if not exists answers (
            id integer primary key autoincrement,
            question_id integer not null,
            user_id integer not null,
            option_id integer not null,
            bet integer not null default 0,
            is_correct integer,
            points_awarded integer not null default 0,
            created_at text not null default current_timestamp,
            foreign key (question_id) references questions (id),
            foreign key (user_id) references users (id),
            foreign key (option_id) references question_options (id),
            unique (question_id, user_id)
        );

        create table if not exists point_transactions (
            id integer primary key autoincrement,
            user_id integer not null,
            question_id integer,
            amount integer not null,
            reason text not null,
            created_at text not null default current_timestamp,
            foreign key (user_id) references users (id),
            foreign key (question_id) references questions (id)
        );

        create table if not exists discussion_posts (
            id integer primary key autoincrement,
            user_id integer not null,
            title text not null,
            body text not null,
            created_at text not null default current_timestamp,
            foreign key (user_id) references users (id)
        );

        create table if not exists discussion_replies (
            id integer primary key autoincrement,
            post_id integer not null,
            user_id integer not null,
            body text,
            image_path text,
            created_at text not null default current_timestamp,
            foreign key (post_id) references discussion_posts (id),
            foreign key (user_id) references users (id)
        );
        """
    )
    if column_exists("answers", "id") and not column_exists("answers", "bet"):
        db.execute("alter table answers add column bet integer not null default 0")
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("请先登录。", "error")
            return redirect(url_for("login", next=login_next_target()))
        return view(**kwargs)

    return wrapped_view


def resolve_login_redirect():
    next_url = request.args.get("next", "").strip()
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for("profile")


def login_next_target():
    return request.full_path.rstrip("?")


app = create_app()
