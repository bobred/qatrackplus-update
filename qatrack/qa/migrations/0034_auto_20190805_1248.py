# Generated by Django 2.1.11 on 2019-08-05 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qa', '0033_test_formatting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='type',
            field=models.CharField(choices=[('boolean', 'Boolean'), ('simple', 'Simple Numerical'), ('multchoice', 'Multiple Choice'), ('constant', 'Constant'), ('composite', 'Composite'), ('date', 'Date'), ('datetime', 'Date & Time'), ('string', 'String'), ('scomposite', 'String Composite'), ('upload', 'File Upload')], default='simple', help_text='Indicate if this test is a Boolean,Simple Numerical,Multiple Choice,Constant,Composite,Date,Date & Time,String,String Composite,File Upload', max_length=10),
        ),
        migrations.AlterField(
            model_name='testinstance',
            name='string_value',
            field=models.TextField(blank=True, null=True),
        ),
    ]
