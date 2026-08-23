from django.db import migrations


def poblar_datos_iniciales(apps, schema_editor):
    Anuncio = apps.get_model('TuTallerApp', 'Anuncio')
    TarifaAnuncio = apps.get_model('TuTallerApp', 'TarifaAnuncio')

    Anuncio.objects.filter(categoria='banner').update(ubicaciones=['banner'])
    Anuncio.objects.exclude(categoria='banner').update(ubicaciones=['perfil'])

    TarifaAnuncio.objects.bulk_create([
        TarifaAnuncio(ubicaciones=['perfil'], monto=30000, activa=True),
        TarifaAnuncio(ubicaciones=['banner'], monto=0, activa=True),
        TarifaAnuncio(ubicaciones=['banner', 'perfil'], monto=0, activa=True),
    ])


def revertir_datos_iniciales(apps, schema_editor):
    TarifaAnuncio = apps.get_model('TuTallerApp', 'TarifaAnuncio')
    TarifaAnuncio.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('TuTallerApp', '0008_tarifaanuncio_anuncio_ubicaciones'),
    ]

    operations = [
        migrations.RunPython(poblar_datos_iniciales, revertir_datos_iniciales),
    ]
