from datetime import datetime, timedelta
from dateutil.parser import parse
import os

def validate_dates(start_date, end_date):
    """
    Valida se as datas são válidas para um plano de estudos
    
    Args:
        start_date (str): Data de início no formato YYYY-MM-DD
        end_date (str): Data de fim no formato YYYY-MM-DD
        
    Returns:
        tuple: (válido, mensagem de erro)
    """
    if not end_date:
        return True, None
        
    try:
        start = parse(start_date)
        end = parse(end_date)
        
        if end <= start:
            return False, "A data final deve ser posterior à data de início"
            
        duration_weeks = (end - start).days // 7
        if duration_weeks < 1:
            return False, "O período deve ser de pelo menos 1 semana"
            
        return True, None
    except Exception as e:
        return False, f"Erro ao processar datas: {str(e)}"

def calculate_week_dates(start_date, week_number):
    """
    Calcula as datas de início e fim de uma semana específica
    
    Args:
        start_date (str): Data de início do plano no formato YYYY-MM-DD
        week_number (int): Número da semana
        
    Returns:
        tuple: (data_inicio_semana, data_fim_semana) no formato DD/MM/YYYY
    """
    start = parse(start_date)
    week_start = start + timedelta(weeks=week_number-1)
    week_end = week_start + timedelta(days=6)
    
    return (
        week_start.strftime('%d/%m/%Y'),
        week_end.strftime('%d/%m/%Y')
    )

def format_date(date_str, input_format="%Y-%m-%d", output_format="%d/%m/%Y"):
    """
    Converte uma data de um formato para outro
    
    Args:
        date_str (str): String de data para converter
        input_format (str): Formato de entrada
        output_format (str): Formato de saída
        
    Returns:
        str: Data formatada
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except:
        return date_str
    