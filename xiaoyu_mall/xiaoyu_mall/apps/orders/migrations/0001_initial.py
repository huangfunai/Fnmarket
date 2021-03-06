# Generated by Django 4.0.4 on 2022-05-22 05:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0004_rename_is_delete_address_is_deleted'),
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order_id', models.CharField(max_length=64, primary_key=True, serialize=False, verbose_name='订单号')),
                ('total_count', models.IntegerField(default=1, verbose_name='商品总数')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品总金额')),
                ('freight', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='运费')),
                ('pay_method', models.SmallIntegerField(choices=[(2, '支付宝'), (1, '货到付款')], default=1, verbose_name='支付方式')),
                ('status', models.SmallIntegerField(choices=[(1, '待支付'), (4, '已完成'), (5, '已取消'), (3, '待收货'), (2, '待发货')], default=1, verbose_name='订单状态')),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='users.address', verbose_name='收货地址')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='下单用户')),
            ],
            options={
                'verbose_name': '订单基本信息',
                'verbose_name_plural': '订单基本信息',
                'db_table': 'tb_order_info',
            },
        ),
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('count', models.IntegerField(default=1, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='单价')),
                ('comment', models.TextField(default='', verbose_name='评价信息')),
                ('score', models.SmallIntegerField(choices=[(6, '100 分'), (3, '40 分'), (4, '60 分'), (5, '80 分'), (2, '20 分'), (1, '0 分')], default=5, verbose_name='满意度评分')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='是否匿名评价')),
                ('is_commented', models.BooleanField(default=False, verbose_name='是否评价了')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skus', to='orders.orderinfo', verbose_name='订单')),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='goods.sku', verbose_name='订单商品')),
            ],
            options={
                'verbose_name': '订单商品',
                'verbose_name_plural': '订单商品',
                'db_table': 'tb_order_goods',
            },
        ),
    ]
