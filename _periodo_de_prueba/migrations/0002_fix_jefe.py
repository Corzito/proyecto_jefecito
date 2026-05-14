from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('_periodo_de_prueba', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE _periodo_de_prueba_colaborador 
                DROP COLUMN IF EXISTS jefe_inmediato_id;
                
                ALTER TABLE _periodo_de_prueba_colaborador 
                ADD COLUMN IF NOT EXISTS jefe_inmediato VARCHAR(200) NOT NULL DEFAULT '';
                
                ALTER TABLE _periodo_de_prueba_colaborador 
                ADD COLUMN IF NOT EXISTS correo_jefe VARCHAR(254) NULL;
                
                ALTER TABLE _periodo_de_prueba_colaborador 
                ADD COLUMN IF NOT EXISTS alerta_jefe_enviada BOOLEAN NOT NULL DEFAULT FALSE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]