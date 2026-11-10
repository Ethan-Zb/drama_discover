# 短剧平台部署教程：环境文件、Supervisor 与前端

当前前端是 Django 模板 + CSS/JS，无需 npm 或构建 dist。上传完整项目，通过 Gunicorn 渲染页面，Nginx 提供静态文件并代理请求。
已包含 53 个平台导航、中英文切换、国家分类和运营后台；自动全网搜索短剧尚未实现。

本文以 Linux、`/data/services/drama_discover` 项目目录、`/data/services/drama_discover/.venv` 新建环境示例（已有 venv 可沿用，并填写实际 Gunicorn 路径）、`root` 应用用户（按你的要求）、`example.com` 域名为例。请统一替换。

## 1 上传项目和配置

上传本地 `C:\Users\admin\Downloads\short_drama_platform_windows\short_drama_platform` 内容到 `/data/services/drama_discover`，保留模板、static、locale 下的 .mo、各应用 migrations 和 platforms/data。
Windows 的虚拟环境不能复制到 Linux。不要上传真实开发环境文件，也不要把项目目录作为 Nginx 静态根目录。

本次已更新本地项目的配置加载代码。如果服务器使用旧版代码，将本包 `project-update/` 内文件按相同路径覆盖到服务器项目，先备份原文件；同一份新版代码支持各环境。
将本包 `.env.*.example` 及 `deploy/` 复制到项目目录。已有数据应备份并迁移数据库和 media，勿重复执行初始化/演示数据脚本。

```bash
# Debian/Ubuntu 示例；其他发行版用对应包管理器安装 python3-venv、Supervisor、Nginx
sudo apt-get update
sudo apt-get install python3-venv supervisor nginx
sudo install -d /data/services/drama_discover /data/services/drama_discover/.venv
python3 -m venv /data/services/drama_discover/.venv
/data/services/drama_discover/.venv/bin/pip install -r /data/services/drama_discover/requirements-production.txt
```

本次使用 root 运行应用和管理命令。Nginx 的实际用户（Ubuntu 通常 www-data）需对 staticfiles/media 有目录遍历和文件读取权限，可用组或 ACL 授予；不要开放 .env 的读取权限。

## 2 按环境加载 .env

| 进程 APP_ENV | 读取文件 | 文件缺失 |
|---|---|---|
| development（默认） | .env.development | 回退旧 .env；两者都无则用开发默认值 |
| testing | .env.testing | 明确报错 |
| production | .env.production | 明确报错 |

一次只加载一个文件，不合并开发与生产配置；系统已有环境变量优先于文件。相对路径以含 manage.py 的项目目录为准，不依赖启动目录。
可在进程设置 `DJANGO_ENV_FILE=/etc/short-drama/production.env` 指定其他文件，仍需设置 APP_ENV；指定文件必须存在。
APP_ENV 和 DJANGO_SETTINGS_MODULE 必须在启动进程时设置，不要指望在 .env 内切换设置模块。

```bash
cd /data/services/drama_discover
# 首次创建；已有文件请直接编辑，勿覆盖
cp -n .env.production.example .env.production
sudo chmod 600 .env.production
nano .env.production
```

填入真实 DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT；新库示例名称不代表已有数据已经迁移。
DJANGO_SECRET_KEY 替换为随机密钥（至少 32 字符），可用以下命令生成并保存在服务器。已上线项目应保留原有安全密钥，否则现有登录会话失效。

```bash
/data/services/drama_discover/.venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

密钥和含 #、空格的密码请在 .env 中用单引号包裹。生产强制 DEBUG=False，要求显式域名、密钥及数据库连接身份；缺少配置不会退回开发库。
DJANGO_ALLOWED_HOSTS 填所有实际域名（无协议），DJANGO_CSRF_TRUSTED_ORIGINS 填带协议来源。多站点每个域名还需在后台“站点”中登记并启用；只改 Nginx 不会创建业务站点。
初次 HTTP 验证时设 `DJANGO_HTTPS=0`；证书和 Nginx HTTPS 完成后改为 1 并重启服务。正式通过 Nginx 访问，Gunicorn 只监听本机；代理必须覆盖 X-Forwarded-Proto。

管理命令也必须显式选择同一环境：

```bash
env APP_ENV=production DJANGO_SETTINGS_MODULE=config.settings /data/services/drama_discover/.venv/bin/python /data/services/drama_discover/manage.py check
env APP_ENV=production DJANGO_SETTINGS_MODULE=config.settings /data/services/drama_discover/.venv/bin/python /data/services/drama_discover/manage.py migrate
env APP_ENV=production DJANGO_SETTINGS_MODULE=config.settings /data/services/drama_discover/.venv/bin/python /data/services/drama_discover/manage.py collectstatic --noinput
# 首次建站需要管理员时执行
env APP_ENV=production /data/services/drama_discover/.venv/bin/python /data/services/drama_discover/manage.py createsuperuser
```

Windows 本地开发继续默认运行即可；原 .env 仍兼容。有 .env.development 时优先读取它。

```powershell
$env:APP_ENV = 'development'
python manage.py runserver
# 连接独立测试环境（先创建 .env.testing 及独立测试库）
$env:APP_ENV = 'testing'
python manage.py check
```

testing 是一套独立运行环境；项目自动测试仍可用 `python manage.py test --settings=config.test_settings` 的内存 SQLite，避免接触业务库。
旧命令 `config.production_settings` 仍兼容，但必须同时设置 APP_ENV=production。

## 3 按现有服务器方式接入 Supervisor（root）

主配置参考你提供的 beautycrush_backend/docs/supervisord.conf：
- /etc/supervisord.conf：共享主配置，socket /var/run/supervisor.sock。
- /data/supervisor_ini/*.ini：各项目配置；本项目使用 drama_discover.ini。
- /data/supervisor_log/：Supervisor 和项目日志。
- 应用按你的要求使用 root；启动入口采用服务器上已找到的 /usr/local/bin/gunicorn。

已有主配置时保留原有项目和设置，只确认 [include] 包含 /data/supervisor_ini/*.ini。不要直接覆盖正管理其他项目的全局配置。本包 supervisord.conf 是完整主配置参考，适用于首次搭建或逐项合并。
移除你之前在主配置中手工加入的整个 [program:short-drama] 段（包括 user=shortdrama 等该段旧配置），只保留一份新 ini；同时检查旧 include 目录是否仍加载同名程序，避免 8000 被重复占用。

先验证实际 Gunicorn 能加载本项目及其依赖，命令不启动监听：

```bash
cd /data/services/drama_discover
APP_ENV=production DJANGO_SETTINGS_MODULE=config.settings /usr/local/bin/gunicorn --check-config config.wsgi:application
```

若提示缺少 Django/PyMySQL 等模块，说明全局 Gunicorn 与当前激活的 venv 属于不同环境。使用当前项目 Python 安装完整依赖：

```bash
python -m pip install -r requirements-production.txt
python -c 'import sys; from pathlib import Path; print(Path(sys.executable).parent / "gunicorn")'
```

将输出的实际 Gunicorn 绝对路径填到 drama_discover.ini 的 command 起始位置，再用该路径执行 --check-config。Supervisor 不会自动激活终端里的 venv；本包不再假定服务器存在 .venv/bin/gunicorn。

```bash
mkdir -p /data/supervisor_ini /data/supervisor_log
# 将部署包的 deploy/supervisor/drama_discover.ini 上传到项目同名路径后执行
cp /data/services/drama_discover/deploy/supervisor/drama_discover.ini /data/supervisor_ini/drama_discover.ini
supervisorctl -c /etc/supervisord.conf reread
supervisorctl -c /etc/supervisord.conf update
supervisorctl -c /etc/supervisord.conf status short-drama
```

如果 supervisord 尚未运行，先确认主配置、日志目录及 ini 准备好，再执行一次 `supervisord -c /etc/supervisord.conf`，然后查询 status。已有实例运行时无需再启动；出现连接错误先核对当前守护进程使用的主配置和 socket。
原服务器如已通过系统服务启动 Supervisor，沿用它负责开机启动。本包不再增加第二个 Supervisor systemd 实例。

## 4 常用 supervisorctl 命令

```bash
supervisorctl -c /etc/supervisord.conf status short-drama
supervisorctl -c /etc/supervisord.conf restart short-drama
supervisorctl -c /etc/supervisord.conf stop short-drama
supervisorctl -c /etc/supervisord.conf start short-drama
supervisorctl -c /etc/supervisord.conf tail -100 short-drama stderr
tail -n 100 /data/supervisor_log/drama_discover_error.log
```

修改 .env.production 后 restart 即可。修改 ini 后执行 reread 和 update；单独 restart 不会重读 Supervisor 配置。
如果同名变量已在进程环境中定义，仍以进程值优先。若修改父进程继承的系统环境，需重启 Supervisor 本身（会影响其管理的其他应用，应安排窗口）。

## 5 前端 Nginx 与 HTTPS

本包保留 `nginx-http.conf`、`nginx-https.conf`、`nginx-locations.conf`。将 example.com、项目路径和证书路径替换为真实值。
动态页面通过 127.0.0.1:8000 代理；/static/ 指向 collectstatic 生成的 staticfiles，/media/ 指向 media。不要配置 SPA 的 /index.html 回退，也不要缓存后台、语言切换及带 Cookie 的页面。

Ubuntu 示例（其他发行版使用其 include 的 conf.d 目录）：

```bash
sudo install -d /etc/nginx/snippets
sudo install -m 644 /data/services/drama_discover/nginx-locations.conf /etc/nginx/snippets/short-drama-locations.conf
sudo install -m 644 /data/services/drama_discover/nginx-http.conf /etc/nginx/sites-available/short-drama
# 首次创建链接；已存在则检查其目标后编辑配置
sudo ln -s /etc/nginx/sites-available/short-drama /etc/nginx/sites-enabled/short-drama
sudo nginx -t
sudo systemctl reload nginx
```

上面两个源文件先从部署包复制到项目目录。确保 DNS 指向服务器、公网 80/443 已开放；TLS 按服务器现有 Certbot/证书方案申请。
证书就绪后用 nginx-https.conf 更新站点配置，检查证书真实路径，nginx -t 通过再 reload。
最后 `.env.production` 设置 DJANGO_HTTPS=1，supervisorctl restart short-drama。正式站点浏览器访问 https://你的域名，不直接访问 8000。

## 6 验收和排查

- 首页：平台导航、国家和国内/海外筛选、中英文切换、切换后刷新及外部平台跳转。
- /cms/、/admin/：登录正常；实际域名在站点配置中启用，且位于 DJANGO_ALLOWED_HOSTS。
- 样式 404：检查 collectstatic、Nginx alias 的末尾 /、目录遍历权限。
- Unknown or inactive site：补齐后台站点的域名登记，不是在域名字段填完整 URL。
- 502：检查 supervisorctl status、/data/supervisor_log/drama_discover_error.log、8000 端口是否监听及是否被重复启动占用。
- FATAL/BACKOFF：检查 .env.production 是否存在、占位密钥是否已替换、DB 连接和 Gunicorn 实际路径及其 Python 依赖。
- supervisorctl 无法连接：检查 supervisord 是否运行、-c 是否指向同一配置、/var/run/supervisor.sock 是否存在；不要直接删其他实例的 socket。
- 跳转循环：检查 Nginx 覆盖 X-Forwarded-Proto，Django 只由可信本机代理访问。
- 数据为空：核对生产 DB 是否确实包含原数据及站点关联；不会从本地开发库自动同步。

更新代码后：同环境执行 migrate（有迁移时）、collectstatic（静态文件变化时），再 supervisorctl restart short-drama。更新前保留数据库备份及旧代码便于回滚。

配置依据：[Supervisor 配置](https://www.supervisord.org/configuration.html)、[Supervisor 运行与控制](https://www.supervisord.org/running.html)、[python-dotenv 加载规则](https://bbc2.github.io/python-dotenv/)、[Django 部署检查](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)。
