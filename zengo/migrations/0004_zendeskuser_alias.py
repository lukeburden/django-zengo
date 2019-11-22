from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zengo", "0003_relax_url_maxlength"),
    ]

    operations = [
        migrations.AddField(
            model_name="zendeskuser",
            name="alias",
            field=models.TextField(blank=True, null=True),
        ),
    ]
