# 平台导航 V1

首页 `/` 是免费海外短剧平台导航，不要求先录入短剧或购买会员。官网、Google Play、App Store 分别标明；点击后经本站 `/platform-go/<id>/?target=website|android|ios` 记录一次点击，再用 HTTP 302 前往后台保存的对应地址。`utm_campaign` 可记录推广活动。

后台：`/cms/platforms/` 编辑平台名称、入口、依据、核实状态和排序；`/cms/` 查看各站点的平台点击、目标类型和推广活动。普通员工访问概览需增加 `analytics.view_platformclick` 权限，超级用户自动具备。

“已核实”在导航功能中指入口身份与官网/商店条目核对，不代表取得影片版权、商业转售授权、平台背书或用户安全保证。普通网站导航不要求伪造内容授权。具体短剧内容及其发布仍使用原有授权来源审核流程。

目录数据使用 2026-11-10 核对的 Apple 官方公开接口元数据、Google Play 应用条目和开发者公开网站，逐条依据保存在 verification_url/source_note。公开收录 50 个独立官方商店身份，保留旧目录重复/身份不明确记录在后台并停用。它是编辑目录，不是有收入、下载量或市场份额依据的全球 Top 50。数据文件：platforms/data/navigation_links_20261110.json。

核实方式：`python manage.py sync_platform_navigation` 只读预览；`python manage.py sync_platform_navigation --apply` 更新空白或与目录一致的入口，保留用户自定义 URL 和已停用状态。别运行旧 seed_platforms 命令重置已审查条目。

可用性会随国家、设备和平台变更。官网未必能直接播放全部剧集，商店入口只提供官方 App 页面；本站导航免费，对方订阅、付费剧集或地区限制由对方决定。不抓取视频、不代替目标平台登录、不代理播放、不承诺付费解锁。
