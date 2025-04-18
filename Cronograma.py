# Importações necessárias
import google.generativeai as genai
from flask import Flask, render_template_string, request
import webbrowser
from threading import Timer
from datetime import datetime
import json

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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Assistente de Estudos com IA</h1>
        
        <form id="studyForm" method="POST">
            <div class="form-group">
                <label for="interests">Áreas de Interesse:</label>
                <input type="text" id="interests" name="interests" 
                       placeholder="Ex: programação Python, machine learning, marketing digital" required>
            </div>
            
            <div class="form-group">
                <label for="level">Seu Nível Atual:</label>
                <select id="level" name="level" required>
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
            
            <button type="submit">Gerar Plano de Estudos Personalizado</button>
        </form>
        
        <div id="loading" class="loading">
            <p>🔍 Analisando seus dados e criando recomendações personalizadas...</p>
        </div>
        
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
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>📌 Visão Geral</h2>
                        <p>{{ recommendation.overview }}</p>
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>📚 Matérias Recomendadas</h2>
                        {% for subject in recommendation.subjects %}
                            <div style="margin-bottom: 25px;">
                                <h3>{{ subject.name }}</h3>
                                <p>{{ subject.description }}</p>
                                <p><strong>Nível:</strong> {{ subject.level }}</p>
                                <h4>Recursos Recomendados:</h4>
                                <ul style="list-style-type: none; padding-left: 0;">
                                    {% for resource in subject.resources %}
                                        <li class="resource-item">📌 {{ resource }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        {% endfor %}
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>🛣️ Rota de Aprendizado</h2>
                        <ol>
                            {% for step in recommendation.learning_path %}
                                <li style="margin-bottom: 10px;">{{ step }}</li>
                            {% endfor %}
                        </ol>
                    </div>
                    
                    <div class="recommendation-card">
                        <h2>💡 Dicas de Estudo</h2>
                        <ul>
                            {% for tip in recommendation.tips %}
                                <li style="margin-bottom: 10px;">✨ {{ tip }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>

    <script>
        // Mostra o loading ao enviar o formulário
        document.getElementById('studyForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
        });
    </script>
</body>
</html>
"""

# 4. Função para gerar recomendações
def generate_recommendation(interests, level, goals, time):
    try:
        if not model:
            return None, "Serviço de IA indisponível no momento", "Modelo não configurado"
        
        # Prompt estruturado para obter melhores resultados
        prompt = f"""
        Atue como um conselheiro educacional especializado em criar planos de estudo personalizados. 
        Com base nas seguintes informações do usuário:

        **Áreas de Interesse**: {interests}
        **Nível Atual**: {level}
        **Objetivos**: {goals}
        **Disponibilidade Semanal**: {time} horas

        Gere um plano de estudos completo contendo:

        1. VISÃO GERAL: Um resumo do plano (1 parágrafo)
        2. MATÉRIAS: 3-5 matérias principais para focar (cada uma com):
           - Nome
           - Descrição (1-2 frases)
           - Nível recomendado
           - 3 recursos específicos (cursos, livros, plataformas)
        3. ROTA DE APRENDIZADO: Passo-a-passo em 4-6 etapas
        4. DICAS: 3-5 estratégias de estudo personalizadas

        Formate a resposta como JSON válido, seguindo este exemplo:

        {{
            "overview": "texto",
            "subjects": [
                {{
                    "name": "nome",
                    "description": "descrição",
                    "level": "nível",
                    "resources": ["recurso1", "recurso2", "recurso3"]
                }}
            ],
            "learning_path": ["passo1", "passo2"],
            "tips": ["dica1", "dica2"]
        }}

        Seja específico nos recursos recomendados, incluindo:
        - Nomes exatos de cursos (com plataforma: Coursera, Udemy, etc.)
        - Livros (com autores quando possível)
        - Ferramentas úteis
        """
        
        # Envia o prompt para o modelo Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            try:
                # Limpa a resposta removendo markdown
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(json_str), None, None
            except json.JSONDecodeError:
                # Fallback para resposta não-JSON
                return {
                    "overview": response.text,
                    "subjects": [],
                    "learning_path": [],
                    "tips": []
                }, None, None
        else:
            return None, "A IA não retornou uma resposta válida", "Resposta vazia"
            
    except Exception as e:
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
        
        # Gera recomendações
        recommendation, error, model_status = generate_recommendation(
            interests, level, goals, time
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