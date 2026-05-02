from apscheduler.schedulers.background import BackgroundScheduler
from database.connection import SessionLocal
from database.models import Agendamento, Cliente
from datetime import datetime, timedelta

def verificar_lembretes():
    # Aqui vai a lógica de buscar agendamentos no banco
    # e comparar com a hora atual para os gatilhos: 24h, 2h, etc.
    print(f"[{datetime.now()}] Verificando lembretes automáticos...")
    # Exemplo: session = SessionLocal() ...

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    # Roda a verificação a cada 30 minutos
    scheduler.add_job(verificar_lembretes, 'interval', minutes=30)
    scheduler.start()
    return scheduler