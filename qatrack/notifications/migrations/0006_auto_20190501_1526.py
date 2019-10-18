# Generated by Django 2.1.8 on 2019-05-01 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qa', '0033_test_formatting'),
        ('notifications', '0005_remove_notificationsubscription_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationsubscription',
            name='test_lists',
            field=models.ManyToManyField(blank=True, help_text='Select which Test Lists should be included in this notification. Leave blank to include all Test Lists', to='qa.TestList'),
        ),
        migrations.AlterField(
            model_name='notificationsubscription',
            name='units',
            field=models.ManyToManyField(blank=True, help_text='Select which Units should be included in this notification. Leave blank to include all units', to='units.Unit'),
        ),
        migrations.AlterField(
            model_name='notificationsubscription',
            name='warning_level',
            field=models.IntegerField(choices=[(0, 'Notify when Test List completed'), (10, 'Notify on Tolerance or Action'), (20, 'Notify on Test at Action level only')], verbose_name='Notification level'),
        ),
    ]
