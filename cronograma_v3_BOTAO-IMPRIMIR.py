# Importações necessárias
import google.generativeai as genai
from flask import Flask, render_template_string, request
import webbrowser
from threading import Timer
from datetime import datetime, timedelta
import json
from dateutil.parser import parse
import os

# 1. Configuração da API do Google Gemini
try:
    # Inicializa a API com sua chave
    genai.configure(api_key='AIzaSyD812nnS5nJzQm7eoX3y0Qc3GsR0vtkhHI')
    
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

# 2. Configuração do aplicativo Flask
app = Flask(__name__)

# 3. Template HTML (interface do usuário)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assistente de Estudos Inteligente</title>
    <style>
        /* Estilos modernos e responsivos */
        :root {
            --primary: #4285F4;
            --secondary: #34A853;
            --accent: #EA4335;
            --light: #f8f9fa;
            --dark: #202124;
        }
        body {
            font-family: 'Roboto', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: var(--dark);
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h1 {
            color: var(--primary);
            text-align: center;
            margin-bottom: 30px;
            font-weight: 500;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--dark);
        }
        input, select, textarea {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid #dfe1e5;
            border-radius: 8px;
            font-size: 16px;
            transition: border 0.3s;
        }
        input:focus, select:focus, textarea:focus {
            border-color: var(--primary);
            outline: none;
            box-shadow: 0 0 0 2px rgba(66,133,244,0.2);
        }
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            transition: background 0.3s;
        }
        button:hover {
            background-color: #3367d6;
        }
        .result-container {
            margin-top: 40px;
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .loading {
            text-align: center;
            padding: 30px;
            display: none;
        }
        .error-message {
            color: var(--accent);
            background-color: #fce8e6;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid var(--accent);
        }
        .success-message {
            color: var(--secondary);
            background-color: #e6f4ea;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid var(--secondary);
        }
        .recommendation-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary);
        }
        .resource-item {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .model-status {
            font-size: 14px;
            color: #5f6368;
            text-align: right;
            margin-top: 10px;
        }
        .week-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid var(--secondary);
        }
        .week-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .date-range {
            color: #5f6368;
            font-size: 0.9em;
        }
        .material-list {
            margin-top: 10px;
            padding-left: 20px;
        }
        .material-item {
            margin-bottom: 8px;
        }
        .progress-bar {
            height: 10px;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 15px 0;
            overflow: hidden;
        }
        .progress {
            height: 100%;
            background-color: var(--secondary);
            width: 0%;
            transition: width 0.5s ease;
        }
        .timeline {
            margin: 30px 0;
        }
        /* Estilos para impressão */
        @media print {
            body {
                background-color: white;
                padding: 0;
                font-size: 12pt;
            }
            .container {
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }
            button, #studyForm, #loading {
                display: none !important;
            }
            .recommendation-card {
                page-break-inside: avoid;
                margin-bottom: 15px;
            }
            h1 {
                color: black !important;
                font-size: 18pt;
            }
            h2 {
                font-size: 16pt;
            }
            .success-message {
                border-left: none;
                background-color: transparent !important;
                color: black !important;
                padding: 5px 0;
            }
            .resource-item {
                padding: 3px 0;
            }
        }
        /* Estilos para a tabela de cronograma */
        .study-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        .study-table thead tr {
            background-color: var(--primary);
            color: white;
            text-align: left;
        }

        .study-table th,
        .study-table td {
            padding: 12px 15px;
            border: 1px solid #ddd;
        }

        .study-table tbody tr {
            border-bottom: 1px solid #dddddd;
        }

        .study-table tbody tr:nth-of-type(even) {
            background-color: #f3f3f3;
        }

        .study-table tbody tr:last-of-type {
            border-bottom: 2px solid var(--primary);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Assistente de Estudos com IA</h1>

        <!-- Formulário para captura de dados do usuário -->
        <form id="studyForm" method="POST">
            <div class="form-group">
                <label for="interests">Áreas de Interesse:</label>
                <input type="text" id="interests" name="interests" 
                       placeholder="Ex: programação Python, machine learning, marketing digital" required>
            </div>
            
            <div class="form-group">
                <label for="level">Seu Nível Atual:</label>
                <select id="level" name="level" required>
                    <option value="" disabled selected>Selecione seu nível</option>
                    <option value="Iniciante">Iniciante</option>
                    <option value="Intermediário">Intermediário</option>
                    <option value="Avançado">Avançado</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="goals">Seus Objetivos:</label>
                <textarea id="goals" name="goals" 
                          placeholder="Ex: Quero me tornar um cientista de dados em 6 meses..." required></textarea>
            </div>
            
            <div class="form-group">
                <label for="time">Horas Disponíveis por Semana:</label>
                <input type="number" id="time" name="time" min="5" max="80" 
                       placeholder="Ex: 15" required>
            </div>
            
            <div class="form-group">
                <label for="start_date">Data de Início:</label>
                <input type="date" id="start_date" name="start_date" required>
            </div>
            
            <div class="form-group">
                <label for="end_date">Data de Término (opcional):</label>
                <input type="date" id="end_date" name="end_date">
                <small style="color: #5f6368;">Se não informado, será calculado automaticamente</small>
            </div>
            
            <button type="submit">Gerar Plano de Estudos Personalizado</button>
        </form>
        
        <!-- Indicador de carregamento -->
        <div id="loading" class="loading">
            <p>🔍 Analisando seus dados e criando recomendações personalizadas...</p>
            <div class="progress-bar">
                <div class="progress" style="width: 100%; animation: pulse 2s infinite;">
                </div>
            </div>
        </div>

        <!-- Área de resultados -->
        <div id="result">
            {% if error %}
                <div class="error-message">
                    <h3>⚠️ Ocorreu um erro</h3>
                    <p>{{ error }}</p>
                    {% if model_status %}
                        <div class="model-status">Status do modelo: {{ model_status }}</div>
                    {% endif %}
                </div>
            {% endif %}
            
            {% if recommendation %}
                <div class="result-container">
                    <div class="success-message">
                        <h3>🎉 Plano de Estudos Gerado!</h3>
                        <p>Gerado em: {{ date }}</p>
                        <p>Duração: {{ recommendation.duration_weeks }} semanas ({{ recommendation.total_hours }} horas totais)</p>
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress" style="width: {{ recommendation.progress }}%"></div>
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>📌 Visão Geral</h2>
                        <p>{{ recommendation.overview }}</p>
                    </div>
                    
                    <!-- Cronograma semanal detalhado -->
                    <div class="timeline">
                        <h2>📅 Cronograma Semanal</h2>
                        {% for week in recommendation.weekly_schedule %}
                            <div class="week-card">
                                <div class="week-header">
                                    <h3>Semana {{ week.week_number }}: {{ week.focus }}</h3>
                                    <span class="date-range">{{ week.start_date }} a {{ week.end_date }}</span>
                                </div>
                                <div>
                                    <h4>Objetivos:</h4>
                                    <ul>
                                        {% for goal in week.goals %}
                                            <li>{{ goal }}</li>
                                        {% endfor %}
                                    </ul>
                                    
                                    <h4>Tópicos para Estudar:</h4>
                                    <ul>
                                        {% for topic in week.topics %}
                                            <li>{{ topic }}</li>
                                        {% endfor %}
                                    </ul>
                                    
                                    <h4>Materiais Recomendados:</h4>
                                    <div class="material-list">
                                        {% for material in week.materials %}
                                            <div class="material-item">📚 {{ material }}</div>
                                        {% endfor %}
                                    </div>
                                    
                                    <h4>Dicas:</h4>
                                    <ul>
                                        {% for tip in week.tips %}
                                            <li>💡 {{ tip }}</li>
                                        {% endfor %}
                                    </ul>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>📚 Recursos Complementares</h2>
                        <ul>
                            {% for resource in recommendation.additional_resources %}
                                <li style="margin-bottom: 10px;">🔗 {{ resource }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                
                <!-- Cronograma em formato de tabela para visualização alternativa -->
                <div class="study-table-container">
                    <h2>📅 Cronograma de Estudos Semanal</h2>
                    <table class="study-table">
                        <thead>
                            <tr>
                                <th>Semana</th>
                                <th>Período</th>
                                <th>Foco Principal</th>
                                <th>Tópicos</th>
                                <th>Horas Sugeridas</th>
                                <th>Materiais</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for week in recommendation.weekly_schedule %}
                            <tr>
                                <td>{{ week.week_number }}</td>
                                <td>{{ week.start_date }} a {{ week.end_date }}</td>
                                <td>{{ week.focus }}</td>
                                <td>
                                    <ul style="margin: 0; padding-left: 20px;">
                                        {% for topic in week.topics %}
                                        <li>{{ topic }}</li>
                                        {% endfor %}
                                    </ul>
                                </td>
                                <td>{{ week.suggested_hours }}h</td>
                                <td>
                                    <ul style="margin: 0; padding-left: 20px;">
                                        {% for material in week.materials %}
                                        <li>{{ material }}</li>
                                        {% endfor %}
                                    </ul>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <!-- Botões de impressão -->
                <div style="text-align: center; margin-top: 20px;" class="no-print">
                    <button onclick="printFullPlan()" style="background-color: var(--secondary); width: auto; padding: 10px 20px; margin-right: 10px;">
                        🖨️ Imprimir Plano Completo (Retrato)
                    </button>
                    
                    <button onclick="printTableOnly()" style="background-color: var(--primary); width: auto; padding: 10px 20px;">
                        📋 Imprimir Apenas Tabela (Paisagem)
                    </button>
                    
                    <button onclick="exportToPDF()" style="background-color: #EA4335; width: auto; padding: 10px 20px; margin-left: 10px;">
                        💾 Exportar como PDF
                    </button>
                </div>
            {% endif %}
        </div>
    </div>

    <!-- Scripts para interatividade do formulário -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script>
        // Mostra o loading ao enviar o formulário
        document.getElementById('studyForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
        });
        
        // Define a data de início padrão como hoje
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('start_date').value = today;
        });

        // Função para imprimir o plano completo em retrato
        function printFullPlan() {
            const originalTitle = document.title;
            document.title = "Plano de Estudos Completo - " + originalTitle;
            
            const css = `
                @page {
                    size: portrait;
                }
                body {
                    -webkit-print-color-adjust: exact;
                }
                .study-table {
                    display: table !important;
                }
                .no-print, .print-table-only {
                    display: none !important;
                }
            `;
            
            printWithStyles(css);
            document.title = originalTitle;
        }

        // Função para imprimir apenas a tabela em paisagem
        function printTableOnly() {
            const originalTitle = document.title;
            document.title = "Cronograma de Estudos - " + originalTitle;
            
            const css = `
                @page {
                    size: landscape;
                    margin: 0.5cm;
                }
                body {
                    visibility: hidden;
                    margin: 0;
                    padding: 0;
                }
                .study-table-container {
                    visibility: visible;
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 100%;
                }
                .study-table {
                    width: 100% !important;
                    font-size: 10pt;
                    border-collapse: collapse;
                }
                .study-table th,
                .study-table td {
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                }
                .study-table thead tr {
                    background-color: #4285F4 !important;
                    color: white !important;
                    -webkit-print-color-adjust: exact;
                }
                .no-print {
                    display: none !important;
                }
            `;
            
            // Primeiro esconda tudo
            document.body.querySelectorAll('*').forEach(el => {
                if (!el.closest('.study-table-container')) {
                    el.style.visibility = 'hidden';
                    el.style.position = 'absolute';
                }
            });
            
            // Depois mostre apenas a tabela
            const tableContainer = document.querySelector('.study-table-container');
            if (tableContainer) {
                tableContainer.style.visibility = 'visible';
                tableContainer.style.position = 'relative';
            }
            
            printWithStyles(css);
            document.title = originalTitle;
            
            // Restaura a visibilidade após a impressão
            setTimeout(() => {
                document.body.querySelectorAll('*').forEach(el => {
                    el.style.visibility = '';
                    el.style.position = '';
                });
            }, 1500);
        }

        // Função auxiliar para impressão com estilos personalizados
        function printWithStyles(css) {
            const style = document.createElement('style');
            style.type = 'text/css';
            style.media = 'print';
            style.innerHTML = css;
            
            document.head.appendChild(style);
            window.print();
            
            // Remove o estilo após a impressão
            setTimeout(() => {
                if (style.parentNode) {
                    document.head.removeChild(style);
                }
            }, 1500);
        }

        // Função para exportar como PDF
        function exportToPDF() {
            // Esconde elementos que não devem aparecer no PDF
            const elementsToHide = [
                '#studyForm', 
                '#loading', 
                '.no-print',
                '.error-message'
            ];
            
            // Aplica estilo de ocultação
            elementsToHide.forEach(selector => {
                const el = document.querySelector(selector);
                if (el) el.style.display = 'none';
            });

            // Cria elemento temporário com apenas o conteúdo desejado
            const contentToPrint = document.querySelector('.result-container').cloneNode(true);
            const tableToPrint = document.querySelector('.study-table-container').cloneNode(true);
            
            const printContainer = document.createElement('div');
            printContainer.style.padding = '20px';
            printContainer.appendChild(contentToPrint);
            printContainer.appendChild(tableToPrint);
            
            // Configurações do PDF
            const opt = {
                margin: 10,
                filename: 'plano_estudos_completo_' + new Date().toISOString().slice(0, 10) + '.pdf',
                image: { 
                    type: 'jpeg', 
                    quality: 0.98 
                },
                html2canvas: { 
                    scale: 2,
                    scrollY: 0,
                    ignoreElements: (element) => {
                        return element.classList.contains('no-print');
                    }
                },
                jsPDF: { 
                    unit: 'mm', 
                    format: 'a4', 
                    orientation: 'portrait'
                },
                pagebreak: {
                    mode: ['avoid-all', 'css', 'legacy']
                }
            };

            // Mostra mensagem de carregamento
            const loading = document.createElement('div');
            loading.innerHTML = '<p style="text-align: center; font-weight: bold; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.2);">Gerando PDF, por favor aguarde...</p>';
            document.body.appendChild(loading);

            // Gera o PDF
            html2pdf()
                .set(opt)
                .from(printContainer)
                .save()
                .then(() => {
                    document.body.removeChild(loading);
                    // Restaura elementos ocultados
                    elementsToHide.forEach(selector => {
                        const el = document.querySelector(selector);
                        if (el) el.style.display = '';
                    });
                })
                .catch(err => {
                    console.error('Erro ao gerar PDF:', err);
                    document.body.removeChild(loading);
                    // Restaura elementos ocultados mesmo em caso de erro
                    elementsToHide.forEach(selector => {
                        const el = document.querySelector(selector);
                        if (el) el.style.display = '';
                    });
                    alert('Erro ao gerar PDF. Verifique o console para detalhes.');
                });
        }

    </script>
</body>
</html>
"""

# 4. Função para gerar recomendações
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

# 5. Rota principal do Flask
@app.route('/', methods=['GET', 'POST'])
def home():
    recommendation = None
    error = None
    model_status = None
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    if request.method == 'POST':
        # Obtém dados do formulário
        interests = request.form['interests']
        level = request.form['level']
        goals = request.form['goals']
        time = request.form['time']
        start_date = request.form['start_date']
        end_date = request.form.get('end_date', None)  # Campo opcional
        
        # Gera recomendações
        recommendation, error, model_status = generate_recommendation(
            interests, level, goals, time, start_date, end_date
        )
    
    # Renderiza o template com os resultados
    return render_template_string(HTML_TEMPLATE, 
                               recommendation=recommendation,
                               error=error,
                               model_status=model_status,
                               date=date)

# 6. Função para abrir o navegador automaticamente
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# 7. Inicialização do aplicativo
if __name__ == '__main__':
    try:
        if model:
            print("\n✅ Aplicativo pronto para uso!")
            print(f"🔗 Acesse: http://127.0.0.1:5000")
            
            # Abre o navegador após 1 segundo
            Timer(1, open_browser).start()
            
            # Inicia o servidor Flask
            app.run(debug=True)
        else:
            print("\n❌ Falha ao conectar com os modelos de IA")
            print("Verifique sua chave de API e conexão com a internet")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar o aplicativo: {str(e)}")
