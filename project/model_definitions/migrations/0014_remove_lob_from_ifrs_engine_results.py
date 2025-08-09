from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model_definitions', '0013_auto_20250807_1235'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ifrsengineresult',
            name='lob',
        ),
    ]
