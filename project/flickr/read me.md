## 存档格式
1. 账号ID
2. 已下载图片数量（下载完成后自动记录，第一次使用不用填写）
3. 最后下载图片的发布时间（下载完成后自动记录，第一次使用不用填写）

## 账号ID获取步骤
点击任意账号，进入主页
地址类似为**https://www.flickr.com/photos/[abcdefgh]/**，其中[]内的内容就是账号的ID（实际不包括[]）

## 配置参数
1. 为访问非公开或受限制的内容，需要配置浏览器类型，参数：BROWSER_TYPE、IS_AUTO_GET_COOKIE、COOKIE_PATH
如果没有检测到浏览器中的登录信息，在程序执行时会提示是否继续
如需访问受限制的内容，请在账号safe search（https://www.flickr.com/account/prefs/safesearch/?from=privacy）中选择"關閉安全搜尋"
2. 默认使用代理访问（参数IS_PROXY=2时也有效果）
	