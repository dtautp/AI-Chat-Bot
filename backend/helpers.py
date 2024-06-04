from datetime import datetime, timezone, timedelta
import uuid

def format_datetime(fecha_timestamp):
    # Convertir el timestamp a un objeto de zona horaria universal (UTC)
    created_datetime = datetime.fromtimestamp(fecha_timestamp, tz=timezone.utc)
    # Verificar si la fecha y hora están en UTC
    if created_datetime.tzinfo != timezone.utc:
        # Convertir a zona horaria UTC si no está en UTC
        created_datetime = created_datetime.astimezone(timezone.utc)
    # Restar 5 horas
    created_datetime_minus_5_hours = created_datetime - timedelta(hours=5)
    # Formatear la fecha y hora en año-mes-día hora:minuto
    formatted_date_time = created_datetime_minus_5_hours.strftime('%Y-%m-%d %H:%M')

    return formatted_date_time

def generate_id():
    return str(uuid.uuid4())