# 慢马争霸赛

一个基于 Flask 和 SQLite 的 F1 主题社区网站，包含车手资料、大赛日历、竞猜奖池、讨论区、个人页、登录荣誉、粉丝团标签和主页音乐播放。

## 当前功能

- 用户注册、登录、退出。
- 密码使用 Werkzeug `scrypt` 哈希保存。
- 表单带 CSRF 校验。
- 主页视频背景、下一站倒计时、底部滚动飘带、背景音乐播放和静音控制。
- 车手页展示 22 位车手资料和图片。
- 大赛页读取 2026 赛历、赛道图和已完赛成绩。
- 竞猜页支持出题、答题投注、奖池结算、排行榜和规则展开查看。
- 讨论区支持发帖、回复和图片上传。
- 个人页展示积分、登录荣誉、站内统计、积分记录。
- 个人页可选择一个车手粉丝团，选择后会在用户名之前显示车手标签。

## 本地启动

```powershell
cd D:\PythonProject\guessFormula
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_APP="app.py"
flask upgrade-db
flask run --host 127.0.0.1 --port 5003
```

访问：

```text
http://127.0.0.1:5003/
```

如果是第一次创建全新数据库，可以用：

```powershell
flask init-db
```

如果数据库已经存在，优先使用：

```powershell
flask upgrade-db
```

## 主要页面

- `/`：主页。
- `/drivers`：车手页。
- `/races`：大赛日历和成绩。
- `/predict`：竞猜页，需要登录。
- `/discussion`：讨论区，需要登录。
- `/profile`：个人页，需要登录。
- `/login`：登录。
- `/register`：注册。

## 竞猜规则

- 出题需要投入积分，进入本题奖池。
- 答题也需要投注积分，投注后立即扣除，并进入本题奖池。
- 出题人也可以答自己的题，但同样需要额外投注。
- 每人每题只能答一次，提交后不能修改。
- 正赛开始后停止答题。
- 正赛开始后，出题人可以揭晓答案并结算。
- 当前总奖池等于“出题积分 + 所有答题投注”。
- 有人答对时，答对者按各自投注额比例瓜分总奖池。
- 没人答对时，总奖池全部归出题人。
- 当前出题积分范围是 20 到 200。
- 当前答题投注范围是 20 到 200。

竞猜页会从 `source/principle/principle.md` 读取游戏规则，并以可展开面板展示。

## 粉丝团功能

个人页可以选择一个车手粉丝团。保存后，`users.fan_driver` 会记录车手三字码，例如 `VER`、`NOR`、`HAM`。

用户名展示位置会自动带上车手标签，包括：

- 顶部导航。
- 个人页。
- 竞猜排行榜。
- 竞猜题出题人。
- 讨论区帖子列表。
- 帖子详情和回复。

车手标签样式来自 `meme/tempt.html` 的设计，并整理进了 `static/style.css`。

## 数据和资源

- `app.py`：Flask 主应用。
- `wsgi.py`：生产环境 WSGI 入口。
- `schema.sql`：全新数据库建表脚本。
- `slowhorse.sqlite3`：当前使用的 SQLite 数据库。
- `templates/`：Jinja2 页面模板。
- `static/style.css`：全站样式。
- `static/home/`：主页视频和封面。
- `static/uploads/replies/`：讨论区回复图片上传目录。
- `source/driver/`：车手数据和车手图片。
- `source/results/`：2026 赛历、成绩和赛道图。
- `source/music/`：主页循环播放音乐。
- `source/principle/principle.md`：竞猜规则文案。
- `meme/meme.md`：讨论区背景弹幕文案。
- `meme/honor.md`：登录荣誉称号文案。
- `meme/tempt.html`：粉丝团车手标签参考样式。

## 数据库维护

初始化数据库会清空旧数据：

```powershell
flask init-db
```

升级数据库会保留现有数据，并补齐新增字段或表：

```powershell
flask upgrade-db
```

目前升级脚本会处理：

- `users.points`
- `users.login_days`
- `users.last_login_award_date`
- `users.fan_driver`
- 竞猜相关表
- 讨论区相关表
- `answers.bet`

## 环境变量

开发环境可以直接运行。生产环境建议设置：

```text
SECRET_KEY=强随机字符串
DATABASE=/path/to/slowhorse.sqlite3
```

`SECRET_KEY` 不要使用默认开发值。

## PythonAnywhere 部署

1. 上传项目到 PythonAnywhere，例如：

```text
/home/你的用户名/guessFormula
```

2. 创建虚拟环境并安装依赖：

```bash
cd ~/guessFormula
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask upgrade-db
```

3. 新建 Manual configuration 的 Flask Web App。

4. WSGI 文件可使用：

```python
import sys

path = "/home/你的用户名/guessFormula"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

5. 在 Web 页面配置虚拟环境路径：

```text
/home/你的用户名/guessFormula/.venv
```

6. 设置 `SECRET_KEY` 环境变量后 Reload 网站。

## 注意事项

- 本站积分仅用于娱乐和站内互动，不涉及现金、奖品或任何形式的赌博。
- `/predict`、`/discussion` 和 `/profile` 都需要登录访问。
- 上传图片限制为 5MB，支持 `jpg`、`png`、`webp` 和 `gif`。
- 浏览器可能会拦截自动播放音乐，需要用户先点击一次播放按钮。
