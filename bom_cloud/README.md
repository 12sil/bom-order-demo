# 智造BOM：免费线上比赛展示版

本包专门用于 Streamlit Community Cloud，不包含本机业务 CSV、产品附件、账号或密钥。作品架构和小程序预留页面已删除。

## 上传到 GitHub

1. 解压下载包，进入 bom_cloud 文件夹。
2. 登录 GitHub，打开 https://github.com/new 。
3. 仓库名填写 bom-order-demo。可选 Public（源码公开）或 Private（源码不公开，部署时须授予 Streamlit 访问权限）。
4. 勾选添加 README，点击 Create repository。
5. 在仓库页面点击 Add file → Upload files。
6. 上传 bom_cloud 文件夹里面的文件及子文件夹，不要直接上传 ZIP。
7. 点击 Commit changes。完成后仓库首页应该直接有 app.py、requirements.txt、packages.txt、core、views、assets、samples。

## 在 Streamlit 发布

1. 打开 https://share.streamlit.io/ ，点击 Create app。
2. 选择已有应用（Yup, I have an app）。
3. Repository：你的用户名/bom-order-demo。
4. Branch：main（如果 GitHub 实际分支不同，填写实际分支）。
5. Main file path：app.py。如果上传后多了一层 bom_cloud 文件夹，填写 bom_cloud/app.py；建议将内容直接放在仓库根目录。
6. Advanced settings 中选择 Python 3.12。本版无需填写 API 密钥。
7. 点击 Deploy，等待安装依赖并生成网址。
8. 发布成功后检查所有页面，再上传 samples/客户订单样例.png 体验识别入单。

如果仓库未显示，先确认 Streamlit 已获得对应仓库访问权限。若显示报错，保存部署日志，不要付费或重复创建多个应用。

## 展示边界

- 只有虚构演示空间，没有正式业务入口。
- 不同浏览器会话分开操作，避免相互覆盖。
- 演示修改仍使用 CSV，但在临时目录保存；新会话、刷新或服务重启后可能重新开始。不能当作真实业务数据长期存储服务。
- 本版只使用 RapidOCR，不调用收费大模型 API。
- 样例图片为虚构订单，日期固定；后续比赛日期改变时，可自行准备新的清晰虚构订单。
- 上传图片和 PDF 会送至运行网站的服务器处理，请勿上传真实客户资料。
- 源码的公开与网站能否公开访问是两件事；请在平台访问设置中确认评委能打开网站。
- 目前完成本地页面启动、会话隔离和真实 OCR 检查，尚未在免费云服务器验证部署。

## 官方参考

https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

