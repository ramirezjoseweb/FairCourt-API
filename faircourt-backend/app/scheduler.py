from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.jobs import process_no_shows_job, process_expired_unlock_proposals_job

scheduler = BackgroundScheduler() 

def start_scheduler() -> None: 
    """
    Arranca el scheduler y registra los jobs periódicos
    """
    if scheduler.running: 
        return 
    
    # job que procesa las reservas en no-show cada minuto 
    scheduler.add_job(
        process_no_shows_job,
        trigger = "interval", # interval es un trigger que ejecuta el job cada cierto tiempo 
        minutes=1, # el job se ejecutará cada minuto 
        id="process_no_shows_jobs", # id del job 
        replace_existing=True, # si el job ya existe, se reemplaza 
    )   

    scheduler.add_job(
        process_expired_unlock_proposals_job, 
        trigger="interval", 
        minutes=1, 
        id="process_expired_unlock_proposals_job", 
        replace_existing=True
    )

    scheduler.start() 
    print("[SCHEDULER] Scheduler iniciado. Job process_no_shows y process_expired_unlock_proposals_job cada 1 minuto") 

def shutdown_scheduler() -> None: 
    """
    Detiene el scheduler al apagar la aplicación 
    """
    # si el scheduler está corriendo cuando se apaga la aplicación, lo detenemos 
    if scheduler.running: 
        scheduler.shutdown() 
        print("[SCHEDULER] Scheduler detenido") 