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