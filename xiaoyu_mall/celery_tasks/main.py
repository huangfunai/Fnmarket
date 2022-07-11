from celery import Celery
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
	os.environ['DJANGO_SETTINGS_MODULE'] = 'xiaoyu_mall.settings.dev'
# 创建 celery 实例
celery_app = Celery('xiaoyu')
# 配置指定使用的消息队列,这里使用Redis
celery_app.config_from_object('celery_tasks.config')
# 注册任务
celery_app.autodiscover_tasks(['celery_tasks.email'])

# Celery服务启动指令: celery -A celery_tasks.main worker -l info -P eventlet -c 1000