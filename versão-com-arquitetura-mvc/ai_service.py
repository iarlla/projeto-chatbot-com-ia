# Importações necessárias
import google.generativeai as genai
import json
from datetime import timedelta
from dateutil.parser import parse
from config import API_KEY
import os

# Configuração da API do Google Gemini
try:
    # Inicializa a API com sua chave
    genai.configure(api_key=API_KEY)
    
    # Lista de modelos para tentar (em ordem de preferência)
    MODEL_PREFERENCES = [
        'gemini-1.5-flash',  # Modelo mais novo e rápido (recomendado)
        'gemini-1.5-pro',    # Modelo avançado
        'gemini-pro'         # Modelo básico (legado)
    ]
    
    # Tenta conectar com cada modelo até encontrar um disponível
    model = None
    for model_name in MODEL_PREFERENCES:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✅ Modelo conectado: {model_name}")
            break
        except Exception as e:
            print(f"⚠️ Modelo {model_name} indisponível: {str(e)}")
    
    if not model:
        raise Exception("❌ Nenhum modelo compatível encontrado")

except Exception as e:
    print(f"❌ Falha na configuração: {str(e)}")
    model = None

# Função para gerar recomendações personalizadas usando a API Gemini
def generate_recommendation(interests, level, goals, time, start_date, end_date=None):
    try:
        if not model:
            return None, "Serviço de IA indisponível no momento", "Modelo não configurado"
        
        # Calcula a duração se a data final for fornecida
        duration_info = ""
        if end_date:
            try:
                start = parse(start_date)
                end = parse(end_date)
                if end <= start:
                    return None, "A data final deve ser após a data de início", "Datas inválidas"
                
                duration_weeks = (end - start).days // 7
                if duration_weeks < 1:
                    return None, "O período deve ser de pelo menos 1 semana", "Período muito curto"
                
                duration_info = f"O plano deve durar exatamente {duration_weeks} semanas (de {start_date} a {end_date})."
            except Exception as e:
                return None, f"Erro ao processar datas: {str(e)}", "Erro de data"

        # Prompt estruturado para obter melhores resultados
        prompt = f"""
        Atue como um conselheiro educacional especializado em criar planos de estudo personalizados. 
        Com base nas seguintes informações do usuário:

        **Áreas de Interesse**: {interests}
        **Nível Atual**: {level}
        **Objetivos**: {goals}
        **Disponibilidade Semanal**: {time} horas
        **Data de Início**: {start_date}
        {f"**Data Final**: {end_date}" if end_date else ""}

        Gere um plano de estudos SEMANAL completo contendo:

        1. VISÃO GERAL: Um resumo do plano (1 parágrafo)
        2. CRONOGRAMA SEMANAL: Lista de semanas com:
           - Número da semana
           - Foco principal
           - Período (data de início e fim da semana)
           - Objetivos específicos (3-5 itens)
           - Tópicos para estudar (3-5 itens)
           - Horas sugeridas (distribuição proporcional do tempo total)
           - Materiais recomendados (cursos, livros, vídeos - com fontes)
           - Dicas específicas para aquela semana
        3. RECURSOS COMPLEMENTARES: Lista de materiais extras
        4. DURAÇÃO TOTAL: Número de semanas e horas totais
        5. PROGRESSO ATUAL: 0% (sempre começa em 0)

        {duration_info if duration_info else "Calcule uma duração adequada baseada nos objetivos e horas disponíveis."}

        Seja específico nos recursos recomendados, incluindo:
        - Nomes exatos de cursos (com plataforma: Coursera, Udemy, etc.)
        - Livros (com autores quando possível)
        - Ferramentas úteis
        - Links quando relevante

        Distribua as horas semanais de forma inteligente, considerando:
        - Complexidade dos tópicos
        - Carga cognitiva
        - Necessidade de prática
        - Tempo para revisão

        Formate a resposta como JSON válido, seguindo este exemplo:

        {{
            "overview": "texto",
            "weekly_schedule": [
                {{
                    "week_number": 1,
                    "focus": "Introdução ao Tema X",
                    "start_date": "DD/MM/AAAA",
                    "end_date": "DD/MM/AAAA",
                    "goals": ["goal1", "goal2"],
                    "topics": ["topic1", "topic2"],
                    "suggested_hours": 10,
                    "materials": ["material1", "material2"],
                    "tips": ["dica1", "dica2"]
                }}
            ],
            "additional_resources": ["recurso1", "recurso2"],
            "duration_weeks": 10,
            "total_hours": 150,
            "progress": 0
        }}
        """
        
        # Envia o prompt para o modelo Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            try:
                # Limpa a resposta removendo markdown
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                recommendation = json.loads(json_str)
                
                # Preenche as datas das semanas se não foram fornecidas
                if not end_date:
                    start = parse(start_date)
                    for week in recommendation['weekly_schedule']:
                        week_start = start + timedelta(weeks=week['week_number']-1)
                        week_end = week_start + timedelta(days=6)
                        week['start_date'] = week_start.strftime('%d/%m/%Y')
                        week['end_date'] = week_end.strftime('%d/%m/%Y')
                        # Calcula horas sugeridas se não foram fornecidas no resultado
                        if 'suggested_hours' not in week:
                            total_weeks = recommendation['duration_weeks']
                            total_hours = recommendation['total_hours']
                            week['suggested_hours'] = round(total_hours / total_weeks)

                return recommendation, None, None
            except json.JSONDecodeError:
                # Fallback para resposta não-JSON
                return {
                    "overview": response.text,
                    "weekly_schedule": [],
                    "additional_resources": [],
                    "duration_weeks": 0,
                    "total_hours": 0,
                    "progress": 0
                }, None, None
        else:
            return None, "A IA não retornou uma resposta válida", "Resposta vazia"
            
    except Exception as e:
        # Tratamento de erros específicos
        error_msg = f"Erro ao gerar recomendações: {str(e)}"
        if "404" in str(e):
            error_msg = "O modelo de IA foi atualizado. Atualize o aplicativo."
        return None, error_msg, f"Exceção: {type(e).__name__}"