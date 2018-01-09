## 存档格式
1. 账号ID
2. 最后下载的图片或视频所在日志的ID（下载完成后自动记录，第一次使用不用填写）

## 账号ID获取步骤
点击任意账号，进入主页
地址类似为**http://[abcdef].tumblr.com**，其中[]中的字母+数字（实际不包括[]）就是账号的ID

## 配置参数
1. 可配置是否单独下载图片和视频，参数：IS_DOWNLOAD_IMAGE、IS_DOWNLOAD_VIDEO
2. 默认使用代理访问（参数IS_PROXY=2时也有效果）
3. 为访问开启了safe mode的账号内容，需要配置浏览器类型，参数：BROWSER_TYPE、IS_AUTO_GET_COOKIE、COOKIE_PATH
如果没有检测到浏览器中的登录信息，在程序执行时会提示是否继续
如需访问safe mode的内容，请在账号safe search（https://www.tumblr.com/settings/account）中关闭"安全模式"

## 应用配置（**/config.ini**）
1. 参数：USER_AGENT
浏览器的user agent，用以访问有敏感内容而开启了安全模式的账号
2. 参数：IS_STEP_ERROR_403_AND_404
是否将被删除或者没有权限的图片或视频下载结果作为错误日志
