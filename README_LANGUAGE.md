# 中英文与国家分类

前台导航、搜索、短剧列表/详情界面、按钮和广告标识支持中文/English。右上角中文 / EN 使用 Django 内置的 POST set_language、CSRF 和站内返回校验；选择保存在当前域名的 django_language Cookie，有效期一年。无选择时根据浏览器语言，最终回退为简体中文。切换保留当前路径、查询条件及推广参数；启用 JavaScript 时同时保留页面锚点。

平台品牌名、站点名及后台录入的原创简介/广告文字保留原文，不会自动生成译文或改写自定义内容。自建运营后台保持既有中文界面；Django Admin 使用 Django 内置的语言支持。

“服务区域”独立于“来源国家/地区”：海外平台可能由中国主体运营，不能仅凭来源国别认定为国内产品。现有目录的 country 字段作为来源国别元数据进行规范化筛选；Unknown、混合或无法归一的值显示待核实。country 不是已验证的公司注册地址，也不是可观看地区保证；market 另行展示服务市场。编辑可以在平台管理中维护两者及服务区域，不能凭网站语言推断国别。

国内参考三款：红果短剧、红果漫剧、河马剧场。参考 QuestMobile 2026 年 9 月独立短剧 App 月活规模（包括漫剧）的媒体报道；不是实时排名，不包含微信小程序和综合视频平台。依据和官方 Apple 入口保存在 platforms/data/domestic_navigation_20261110.json。红果漫剧单独标明为漫剧。`python manage.py sync_domestic_navigation` 预览；添加 `--apply` 导入，已有同名记录及自定义 slug/入口保持原状；名称和 slug 指向不同记录时整次回滚，等待人工核对。

翻译源码：locale/zh_Hans/LC_MESSAGES/django.po；运行 `python scripts/compile_translations.py` 生成标准 django.mo，然后重启服务。当前工具支持项目使用的单数消息及多行字符串，不支持 msgctxt/复数语法；运行时不依赖第三方翻译服务或额外库。

现有 URL 保持不变，语言通过 Cookie 切换。目前不为每种语言建立单独可索引 URL；若后续希望分别运营中英文 SEO 内容，应另外配置语言 URL、对应原创内容、canonical 与 hreflang。
