from django.db import migrations
import konst.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("zengo", "0005_ticket_priority"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="priority",
            field=konst.models.fields.ConstantChoiceCharField(
                blank=True,
                null=True,
                choices=[
                    ("urgent", "urgent"),
                    ("high", "high"),
                    ("normal", "normal"),
                    ("low", "low"),
                ],
                max_length=8,
            ),
        ),
    ]
