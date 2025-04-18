# Assistente de Estudos com IA

Uma aplicação web que utiliza a API do Google Gemini para gerar planos de estudos personalizados, baseados nos interesses, objetivos e disponibilidade do utilizador.

## 📌 Recursos

- Interface web amigável construída com Flask  
- Geração de planos de estudos personalizados  
- Cronograma semanal detalhado com objetivos e materiais  
- Exportação do plano em PDF  
- Visualização em formato de tabela  
- Possibilidade de impressão formatada  

## ⚙️ Requisitos

- Python 3.7+  
- Flask  
- `google-generativeai` (SDK do Google Gemini)  
- `python-dateutil`  
- Acesso à internet para utilizar a API do Google

```bash
  pip install flask google-generativeai python-dateutil
```

## 🛠️ Instalação

Clone o repositório:

```bash
git clone https://seu-repositorio/assistente-estudos-ia.git
cd assistente-estudos-ia
```

## ▶️ Uso

```bash
python app.py
```
Um navegador web será aberto automaticamente no endereço http://127.0.0.1:5000.
Preencha o formulário com as suas informações:
- Áreas de interesse
- Nível atual (iniciante, intermédio, avançado)
- Objetivos de aprendizagem
- Horas disponíveis por semana
- Data de início
- Data de término (opcional)

🖱️ Clique em "Gerar Plano de Estudos Personalizado".

Após o processamento, o seu plano de estudos personalizado será exibido com:
- Visão geral
- Cronograma semanal detalhado
- Recursos complementares
- Opções para imprimir ou exportar como PDF

## 📁 Estrutura do Projeto
```csharp
assistente-estudos-ia/
├── app.py                  # Arquivo principal da aplicação
├── ai_service.py           # Serviço para interação com a API Gemini
├── config.py               # Configurações da aplicação
├── utils.py                # Funções utilitárias
├── static/                 # Arquivos estáticos
│   ├── style.css           # Estilos CSS
│   └── script.js           # Scripts JavaScript
└── templates/              # Templates HTML
    └── index.html          # Template principal da interface
```
