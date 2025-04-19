# Importações necessárias
from flask import Flask, render_template, request
import webbrowser
from threading import Timer
from datetime import datetime
from ai_service import model, generate_recommendation

# Configuração do aplicativo Flask
app = Flask(__name__)

# Rota principal do Flask - processa as solicitações GET e POST
@app.route('/', methods=['GET', 'POST'])
def home():
    recommendation = None
    error = None
    model_status = None
    date = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    if request.method == 'POST':
        # Obtém dados do formulário enviado pelo usuário
        interests = request.form['interests']
        level = request.form['level']
        goals = request.form['goals']
        time = request.form['time']
        start_date = request.form['start_date']
        end_date = request.form.get('end_date', None)  # Campo opcional
        
        # Gera recomendações personalizadas com base nos dados do usuário
        recommendation, error, model_status = generate_recommendation(
            interests, level, goals, time, start_date, end_date
        )
    
    # Renderiza o template HTML com os resultados ou o formulário vazio
    return render_template('index.html', 
                           recommendation=recommendation,
                           error=error,
                           model_status=model_status,
                           date=date)

# Função para abrir o navegador automaticamente ao iniciar o aplicativo
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Inicialização do aplicativo
if __name__ == '__main__':
    try:
        if model:
            print("\n✅ Aplicativo pronto para uso!")
            print(f"🔗 Acesse: http://127.0.0.1:5000")
            
            # Abre o navegador após 1 segundo
            Timer(1, open_browser).start()
            
            # Inicia o servidor Flask em modo de desenvolvimento
            app.run(debug=True)
        else:
            print("\n❌ Falha ao conectar com os modelos de IA")
            print("Verifique sua chave de API e conexão com a internet")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar o aplicativo: {str(e)}")