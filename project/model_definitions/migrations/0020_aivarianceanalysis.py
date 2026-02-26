from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model_definitions', '0019_modeldefinition_definition_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIVarianceAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run_id_current', models.CharField(db_index=True, help_text='Run ID of the current report selected for comparison', max_length=100)),
                ('run_id_prior', models.CharField(db_index=True, help_text='Run ID of the prior/baseline report selected for comparison', max_length=100)),
                ('value_id', models.CharField(db_index=True, help_text='Selected ValueID being compared', max_length=200)),
                ('current_json_snapshot', models.JSONField(default=dict, help_text='Exact JSON used for the current run in this comparison')),
                ('prior_json_snapshot', models.JSONField(default=dict, help_text='Exact JSON used for the prior run in this comparison')),
                ('ai_response_json', models.JSONField(default=dict, help_text='Structured AI output (comparison result and insight)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When this analysis was created')),
            ],
            options={
                'verbose_name': 'AI Variance Analysis',
                'verbose_name_plural': 'AI Variance Analyses',
                'db_table': 'ai_variance_analysis',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aivarianceanalysis',
            index=models.Index(fields=['run_id_current', 'run_id_prior', 'value_id'], name='aiva_run_prior_val_idx'),
        ),
    ]
