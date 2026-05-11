from flask import Flask, render_template, request, send_file, abort
from pypdf import PdfWriter
from PIL import Image

import os
import uuid
import subprocess
import threading
import time
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Usar caminhos absolutos para evitar erros em diferentes ambientes de hospedagem
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def cleanup_files():
    """
    Função que roda em background para limpar arquivos antigos.
    """
    while True:
        try:
            now = time.time()
            # Arquivos com mais de 15 minutos são removidos
            max_age = 900 
            
            for folder in [UPLOAD_FOLDER, CONVERTED_FOLDER]:
                if not os.path.exists(folder):
                    continue
                    
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_age = now - os.path.getmtime(file_path)
                        # Só remove se for mais velho que max_age
                        if file_age > max_age:
                            try:
                                os.remove(file_path)
                                logging.info(f"Limpeza: Arquivo removido {file_path}")
                            except Exception as e:
                                logging.error(f"Erro ao remover {file_path}: {e}")
        except Exception as e:
            logging.error(f"Erro no loop de limpeza: {e}")
        
        time.sleep(300) # Verifica a cada 5 minutos

# Inicia a thread de limpeza
cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/merge-pdf-page')
def merge_pdf_page():
    return render_template('merge_pdf.html')

@app.route('/compress-pdf-page')
def compress_pdf_page():
    return render_template('compress_pdf.html')

@app.route('/word-to-pdf-page')
def word_to_pdf_page():
    return render_template('word_to_pdf.html')

@app.route('/image-to-pdf-page')
def image_to_pdf_page():
    return render_template('image_to_pdf.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    try:
        files = request.files.getlist('pdfs')
        if not files or files[0].filename == '':
            return "Nenhum PDF enviado.", 400

        merger = PdfWriter()
        uploaded_files = []

        for file in files:
            if file.filename.lower().endswith('.pdf'):
                filename = f"{uuid.uuid4()}.pdf"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                uploaded_files.append(filepath)
                merger.append(filepath)

        if not uploaded_files:
            return "Nenhum PDF válido enviado.", 400

        output_filename = f"merged_{uuid.uuid4()}.pdf"
        output_path = os.path.join(CONVERTED_FOLDER, output_filename)
        
        merger.write(output_path)
        merger.close()

        if not os.path.exists(output_path):
            logging.error(f"Falha ao criar arquivo de saída: {output_path}")
            return "Erro ao gerar o arquivo final.", 500

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Erro em merge_pdf: {e}")
        return f"Erro interno: {str(e)}", 500

@app.route('/compress-pdf', methods=['POST'])
def compress_pdf():
    try:
        file = request.files.get('pdf')
        if not file or file.filename == '':
            return "Nenhum PDF enviado.", 400

        input_filename = f"{uuid.uuid4()}.pdf"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)

        output_filename = f"compressed_{uuid.uuid4()}.pdf"
        output_path = os.path.join(CONVERTED_FOLDER, output_filename)

        # Comando Ghostscript
        command = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
            f'-sOutputFile={output_path}', input_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Ghostscript erro: {result.stderr}")
            return "Erro na compressão do PDF. Verifique se o Ghostscript está instalado.", 500
        
        print("Arquivo Comprimido!")

        if not os.path.exists(output_path):
            return "Arquivo comprimido não foi gerado.", 500
        
        print(f"Arquivo Comprimido Salvo em: {output_path}")

        return send_file(output_path, as_attachment=True)
    
    except FileNotFoundError:
        # Ocorre se o 'gs' (Ghostscript) não estiver instalado no PATH do sistema
        logging.error("Ghostscript não encontrado. Certifique-se de que o 'gs' está instalado.")
        return "Erro de configuração: Ghostscript não instalado no servidor.", 500

    except subprocess.CalledProcessError as e:
        # Ocorre quando o Ghostscript retorna um erro (ex: PDF corrompido)
        logging.error(f"Erro no processamento do Ghostscript: {e.stderr}")
        return f"Erro ao processar o PDF: o arquivo pode estar corrompido.", 422

    except subprocess.TimeoutExpired:
        # Útil se você definir um parâmetro 'timeout' no subprocess.run
        logging.error("A compressão do PDF demorou demais e foi cancelada.")
        return "O processamento excedeu o tempo limite.", 504

    except OSError as e:
        # Erros de sistema, como falta de permissão de escrita ou disco cheio
        logging.error(f"Erro de sistema/disco: {e}")
        return "Erro interno ao manipular arquivos no servidor.", 500

    except Exception as e:
        logging.error(f"Erro em compress_pdf: {e}")
        return f"Erro interno: {str(e)}", 500

@app.route('/word-to-pdf', methods=['POST'])
def word_to_pdf():
    try:
        file = request.files.get('document')
        if not file or file.filename == '':
            return "Nenhum arquivo enviado.", 400

        allowed = ('.doc', '.docx', '.odt')
        if not file.filename.lower().endswith(allowed):
            return "Formato inválido.", 400

        input_filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)

        # LibreOffice
        process = subprocess.run([
            'libreoffice', '--headless', '--convert-to', 'pdf',
            '--outdir', CONVERTED_FOLDER, input_path
        ], capture_output=True, text=True)

        if process.returncode != 0:
            logging.error(f"LibreOffice erro: {process.stderr}")
            return "Erro na conversão. Verifique se o LibreOffice está instalado.", 500

        # O LibreOffice gera o PDF com o mesmo nome base do input
        pdf_filename = os.path.splitext(input_filename)[0] + '.pdf'
        output_path = os.path.join(CONVERTED_FOLDER, pdf_filename)

        if not os.path.exists(output_path):
            logging.error(f"Arquivo não encontrado após conversão: {output_path}")
            return "Erro: O arquivo PDF não foi gerado.", 500

        return send_file(output_path, as_attachment=True)
    
    except FileNotFoundError:
        # Ocorre se o 'gs' (Ghostscript) não estiver instalado no PATH do sistema
        logging.error("LibreOffice não encontrado. Certifique-se de que o 'gs' está instalado.")
        return "Erro de configuração: LibreOffice não instalado no servidor.", 500

    except subprocess.CalledProcessError as e:
        # Ocorre quando o Ghostscript retorna um erro (ex: PDF corrompido)
        logging.error(f"Erro no processamento do LibreOffice: {e.stderr}")
        return f"Erro ao processar o PDF: o arquivo pode estar corrompido.", 422

    except subprocess.TimeoutExpired:
        # Útil se você definir um parâmetro 'timeout' no subprocess.run
        logging.error("A compressão do PDF demorou demais e foi cancelada.")
        return "O processamento excedeu o tempo limite.", 504

    except OSError as e:
        # Erros de sistema, como falta de permissão de escrita ou disco cheio
        logging.error(f"Erro de sistema/disco: {e}")
        return "Erro interno ao manipular arquivos no servidor.", 500
    
    except Exception as e:
        logging.error(f"Erro em word_to_pdf: {e}")
        return f"Erro interno: {str(e)}", 500

@app.route('/image-to-pdf', methods=['POST'])
def image_to_pdf():
    try:
        files = request.files.getlist('images')
        if not files or files[0].filename == '':
            return "Nenhuma imagem enviada.", 400

        image_list = []
        for file in files:
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                img = Image.open(filepath).convert('RGB')
                image_list.append(img)

        if not image_list:
            return "Nenhuma imagem válida.", 400

        output_filename = f"images_{uuid.uuid4()}.pdf"
        output_path = os.path.join(CONVERTED_FOLDER, output_filename)

        image_list[0].save(output_path, save_all=True, append_images=image_list[1:])

        if not os.path.exists(output_path):
            return "Erro ao gerar PDF de imagens.", 500

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Erro em image_to_pdf: {e}")
        return f"Erro interno: {str(e)}", 500

if __name__ == '__main__':
    # Em produção, use um servidor WSGI como Gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
