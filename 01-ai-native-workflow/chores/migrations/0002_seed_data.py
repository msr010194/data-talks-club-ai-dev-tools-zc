from django.db import migrations


def seed_data(apps, schema_editor):
    Person = apps.get_model('chores', 'Person')
    Chore = apps.get_model('chores', 'Chore')

    for name in ['Person 1', 'Person 2', 'Person 3', 'Person 4']:
        Person.objects.get_or_create(name=name)

    for name in [
        'Trash & recycling',
        'Dishes',
        'Vacuuming',
        'Bathroom cleaning',
        'Laundry',
        'Kitchen cleaning',
        'Grocery shopping',
        'Tidying common areas',
    ]:
        Chore.objects.get_or_create(name=name)


def remove_data(apps, schema_editor):
    Person = apps.get_model('chores', 'Person')
    Chore = apps.get_model('chores', 'Chore')
    Person.objects.all().delete()
    Chore.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chores', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_data),
    ]
