# Generated by Django 2.2.18 on 2021-02-11 01:37

import datetime
from django.db import migrations, models
import django.db.models.deletion
import recurrence.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0023_faultsreviewnotice'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceEventSchedulingNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.IntegerField(choices=[(0, 'Notify About All Service Event Schedule Due Dates'), (10, 'Notify About Scheduled Service Events Currently Due & Overdue'), (20, 'Notify About Scheduled Service Events Currently Due & Overdue, and Upcoming Due Dates'), (30, 'Notify About Scheduled Service Events Upcoming Due Dates Only')], verbose_name='Notification Type')),
                ('send_empty', models.BooleanField(default=False, help_text="Check to send notices even if there's no QC to currently notify about", verbose_name='Send Empty Notices')),
                ('recurrences', recurrence.fields.RecurrenceField(default='', help_text='Define the schedule this notification should be sent on.', verbose_name='Recurrences')),
                ('time', models.TimeField(choices=[(datetime.time(0, 0), '00:00'), (datetime.time(0, 15), '00:15'), (datetime.time(0, 30), '00:30'), (datetime.time(0, 45), '00:45'), (datetime.time(1, 0), '01:00'), (datetime.time(1, 15), '01:15'), (datetime.time(1, 30), '01:30'), (datetime.time(1, 45), '01:45'), (datetime.time(2, 0), '02:00'), (datetime.time(2, 15), '02:15'), (datetime.time(2, 30), '02:30'), (datetime.time(2, 45), '02:45'), (datetime.time(3, 0), '03:00'), (datetime.time(3, 15), '03:15'), (datetime.time(3, 30), '03:30'), (datetime.time(3, 45), '03:45'), (datetime.time(4, 0), '04:00'), (datetime.time(4, 15), '04:15'), (datetime.time(4, 30), '04:30'), (datetime.time(4, 45), '04:45'), (datetime.time(5, 0), '05:00'), (datetime.time(5, 15), '05:15'), (datetime.time(5, 30), '05:30'), (datetime.time(5, 45), '05:45'), (datetime.time(6, 0), '06:00'), (datetime.time(6, 15), '06:15'), (datetime.time(6, 30), '06:30'), (datetime.time(6, 45), '06:45'), (datetime.time(7, 0), '07:00'), (datetime.time(7, 15), '07:15'), (datetime.time(7, 30), '07:30'), (datetime.time(7, 45), '07:45'), (datetime.time(8, 0), '08:00'), (datetime.time(8, 15), '08:15'), (datetime.time(8, 30), '08:30'), (datetime.time(8, 45), '08:45'), (datetime.time(9, 0), '09:00'), (datetime.time(9, 15), '09:15'), (datetime.time(9, 30), '09:30'), (datetime.time(9, 45), '09:45'), (datetime.time(10, 0), '10:00'), (datetime.time(10, 15), '10:15'), (datetime.time(10, 30), '10:30'), (datetime.time(10, 45), '10:45'), (datetime.time(11, 0), '11:00'), (datetime.time(11, 15), '11:15'), (datetime.time(11, 30), '11:30'), (datetime.time(11, 45), '11:45'), (datetime.time(12, 0), '12:00'), (datetime.time(12, 15), '12:15'), (datetime.time(12, 30), '12:30'), (datetime.time(12, 45), '12:45'), (datetime.time(13, 0), '13:00'), (datetime.time(13, 15), '13:15'), (datetime.time(13, 30), '13:30'), (datetime.time(13, 45), '13:45'), (datetime.time(14, 0), '14:00'), (datetime.time(14, 15), '14:15'), (datetime.time(14, 30), '14:30'), (datetime.time(14, 45), '14:45'), (datetime.time(15, 0), '15:00'), (datetime.time(15, 15), '15:15'), (datetime.time(15, 30), '15:30'), (datetime.time(15, 45), '15:45'), (datetime.time(16, 0), '16:00'), (datetime.time(16, 15), '16:15'), (datetime.time(16, 30), '16:30'), (datetime.time(16, 45), '16:45'), (datetime.time(17, 0), '17:00'), (datetime.time(17, 15), '17:15'), (datetime.time(17, 30), '17:30'), (datetime.time(17, 45), '17:45'), (datetime.time(18, 0), '18:00'), (datetime.time(18, 15), '18:15'), (datetime.time(18, 30), '18:30'), (datetime.time(18, 45), '18:45'), (datetime.time(19, 0), '19:00'), (datetime.time(19, 15), '19:15'), (datetime.time(19, 30), '19:30'), (datetime.time(19, 45), '19:45'), (datetime.time(20, 0), '20:00'), (datetime.time(20, 15), '20:15'), (datetime.time(20, 30), '20:30'), (datetime.time(20, 45), '20:45'), (datetime.time(21, 0), '21:00'), (datetime.time(21, 15), '21:15'), (datetime.time(21, 30), '21:30'), (datetime.time(21, 45), '21:45'), (datetime.time(22, 0), '22:00'), (datetime.time(22, 15), '22:15'), (datetime.time(22, 30), '22:30'), (datetime.time(22, 45), '22:45'), (datetime.time(23, 0), '23:00'), (datetime.time(23, 15), '23:15'), (datetime.time(23, 30), '23:30'), (datetime.time(23, 45), '23:45')], help_text='Set the time of day this notice should be sent (00:00-23:59).', verbose_name='Time of day')),
                ('future_days', models.PositiveIntegerField(blank=True, help_text='How many days in the future should notices about upcoming QC due dates include. A value of zero will only include test lists due today.', null=True, verbose_name='Future Days')),
                ('last_sent', models.DateTimeField(editable=False, null=True)),
                ('recipients', models.ForeignKey(help_text='Choose the group of recipients who should receive these notifications', on_delete=django.db.models.deletion.PROTECT, to='notifications.RecipientGroup', verbose_name='Recipients')),
                ('units', models.ForeignKey(blank=True, help_text='Select which group of Units this notification should be limited to. Leave blank to include all units', null=True, on_delete=django.db.models.deletion.PROTECT, to='notifications.UnitGroup', verbose_name='Unit Group filter')),
            ],
            options={
                'verbose_name': 'Service Event Scheduling Notice',
            },
        ),
    ]
