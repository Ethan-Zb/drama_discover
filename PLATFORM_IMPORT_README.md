# 海外短剧平台 50 条初始化数据导入

本补丁新增 `platforms` Django App，独立保存平台目录，不会删除或覆盖现有短剧、分类、观看链接数据。

## 导入步骤（Windows / PyCharm Terminal）

先进入包含 `manage.py` 的项目根目录，并激活虚拟环境：

```powershell
.venv\Scripts\activate
```

把本补丁中的 `platforms` 文件夹复制到项目根目录；用补丁中的 `config/settings.py` 替换原文件（若你后来改过 settings.py，至少手动把 `"platforms",` 加入 `INSTALLED_APPS`，不要覆盖自己的其他设置）。

执行：

```powershell
python manage.py makemigrations platforms
python manage.py migrate
python manage.py seed_platforms
```

验证数量：

```powershell
python manage.py shell -c "from platforms.models import Platform; print('平台数量：', Platform.objects.count()); print(list(Platform.objects.values_list('rank','name','status')[:10]))"
```

打开后台：`http://127.0.0.1:8000/admin/`，在“短剧平台”中查看和编辑。

## 重要说明

- 该命令可重复执行；按 slug 更新同一条记录，不会重复插入这 50 条种子数据。
- 这是一份“海外短剧平台发现目录”的初始候选名单，不是声称严格审计过的全球 Top 50 排名。行业榜单会因下载量、收入、地区、统计周期而变化。
- 数据默认状态为“待核实”，不自动公开展示；请先核实官方域名、iOS/Android 商店链接、平台归属及目标市场。
- 官方网站、应用商店链接和 Logo 地址故意留空，避免猜测或把非官方页面误录为官方入口。
- 名单参考：Sensor Tower《State of Short Drama Apps 2026》、Mintegral/Insightrackr《2026 Global Non-Gaming App Trends Report》、Vertical Observer 2026 排名汇总、Vertical Clap 全球平台目录，以及 2025 年中国应用出海报告。以上来源使用的统计口径不同，不能把列表顺序理解为统一市场份额排名。

参考链接：
- https://sensortower.com/blog/state-of-short-drama-apps-2026-report
- https://verticalobserver.com/data/rankings/
- https://index.verticalclap.com/en/index/
- https://assets-official.mintegral.com/v3/file-link/2026/02/05/Mintegral%20x%20Insightrackr%20-%202026%20Global%20Non-Gaming%20App%20Trends%20Report.pdf
