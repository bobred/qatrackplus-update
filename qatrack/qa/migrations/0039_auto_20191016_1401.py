# Generated by Django 2.1.11 on 2019-10-16 18:01

from django.db import migrations, models
import django.db.models.deletion

import qatrack.qa.models


class Migration(migrations.Migration):

    dependencies = [
        ('qa', '0038_testinstance_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoReviewRuleSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Give this rule set a unique descriptive name.', max_length=255, unique=True, verbose_name='Name')),
                ('is_default', models.BooleanField(default=False, help_text='Check this option if you want this to be the default rule set for tests', verbose_name='Default')),
                ('rules', models.ManyToManyField(help_text='Select the auto review rules to include in this rule set.', to='qa.AutoReviewRule', verbose_name='Rules')),
            ],
        ),
        migrations.AddField(
            model_name='test',
            name='autoreviewruleset',
            field=models.ForeignKey(blank=True, default=qatrack.qa.models.default_autoreviewruleset, help_text='Choose the Auto Review Rule Set to use for this Test. Leave blank to disable Auto Review for this Test.', null=True, on_delete=django.db.models.deletion.PROTECT, to='qa.AutoReviewRuleSet', verbose_name='Auto Review Rules'),
        ),
    ]
