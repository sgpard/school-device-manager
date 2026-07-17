from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

# Boa prática para o GitHub: tenta pegar do sistema operacional, senão usa uma padrão de segurança
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'chave_secreta_extensao_desenvolvimento')

def ligar_banco():
    return sqlite3.connect('escola.db')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        login_user = request.form['login']
        senha_user = request.form['senha']
        
        conn = ligar_banco()
        conn.row_factory = sqlite3.Row  # Garante acesso por nome de coluna
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM usuarios_admin WHERE login = ?", (login_user,))
        user = cursor.fetchone()
        conn.close()
        
        # Validação de senha usando a função de segurança
        if user and check_password_hash(user['senha'], senha_user):
            session['user_id'] = user['id']
            session['user_nome'] = user['nome']
            return redirect(url_for('dashboard'))
        else:
            erro = "Usuário ou senha incorretos. Tente novamente!"
        
    return render_template('login.html', erro=erro)

@app.route('/logout')
def logout():
    session.clear()  # Limpeza de memória de login
    flash("Sessão encerrada com segurança.")
    return redirect(url_for('login'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    conn = ligar_banco()
    cursor = conn.cursor()
    
    # Verificação de limite 3 usuários
    cursor.execute("SELECT COUNT(*) FROM usuarios_admin")
    total_usuarios = cursor.fetchone()[0]
    
    if total_usuarios >= 3:
        conn.close()
        # Removido o HTML hardcoded. Agora usa o seu template de erro nativo!
        return render_template('erro.html', mensagem="O sistema já possui o máximo de 3 administradores (1 Diretora e 2 Coordenadoras)."), 403

    if request.method == 'POST':
        nome = request.form['nome']
        login_user = request.form['login']
        senha_limpa = request.form['senha']
        pergunta = request.form['pergunta'] 
        resposta_limpa = request.form['resposta'].lower().strip()
        resposta_criptografada = generate_password_hash(resposta_limpa)

        # Criptografia da senha
        senha_criptografada = generate_password_hash(senha_limpa)
        
        try:
            cursor.execute("""
                INSERT INTO usuarios_admin (nome, login, senha, pergunta_seguranca, resposta_seguranca) 
                VALUES (?, ?, ?, ?, ?)
            """, (nome, login_user, senha_criptografada, pergunta, resposta_criptografada))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso! Faça seu login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:  # Tratamento específico para login duplicado
            conn.close()
            flash("Erro: Este login já existe!")
            return redirect(url_for('registrar'))
        except Exception as e:
            conn.close()
            return render_template('erro.html', mensagem=f"Erro inesperado no banco: {str(e)}"), 500
            
    conn.close()
    return render_template('registrar.html')

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    erro = None
    passo = 1  # Passo 1: Digitar login | Passo 2: Responder pergunta
    user_data = None

    if request.method == 'POST':
        login_user = request.form.get('login')
        
        conn = ligar_banco()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios_admin WHERE login = ?", (login_user,))
        user_data = cursor.fetchone()

        # Se clicou em "Verificar Pergunta"
        if 'btn_verificar_login' in request.form:
            if user_data:
                passo = 2
            else:
                erro = "Usuário não encontrado."
        
        # Se clicou em "Redefinir Senha"
        elif 'btn_redefinir' in request.form:
            resposta_digitada = request.form.get('resposta').lower().strip()
            nova_senha_limpa = request.form.get('nova_senha')
            
            if user_data and check_password_hash(user_data['resposta_seguranca'], resposta_digitada):
                nova_senha_criptografada = generate_password_hash(nova_senha_limpa)
                
                cursor.execute("UPDATE usuarios_admin SET senha = ? WHERE id = ?", (nova_senha_criptografada, user_data['id']))
                conn.commit()
                conn.close()
                flash("Senha alterada com sucesso!")
                return redirect(url_for('login')) 
            else:
                erro = "Resposta incorreta!"
                passo = 2

        conn.close()

    return render_template('recuperar.html', erro=erro, passo=passo, user=user_data)

@app.route('/excluir_conta')
def excluir_conta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    with ligar_banco() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios_admin WHERE id = ?", (user_id,))
    
    session.clear()  # Limpa a sessão após excluir
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = ligar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Consulta SQL que traz dados dinâmicos do dispositivo e movimentação atual
    cursor.execute("""
        SELECT d.*, m.responsavel_retirada, m.data_devolucao_prevista, m.data_saida 
        FROM dispositivos d
        LEFT JOIN movimentacoes m ON d.id = m.id_dispositivo AND m.data_devolucao_real IS NULL
    """)
    dispositivos = cursor.fetchall()
    
    # Cálculo de estatísticas em tempo real
    cursor.execute("SELECT COUNT(*) FROM dispositivos")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE status = 'Disponível'")
    disponiveis = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE status = 'Emprestado'")
    emprestados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE status = 'Manutenção'")
    manutencao = cursor.fetchone()[0]
    
    conn.close()
    
    estatisticas = {
        'total': total,
        'disponiveis': disponiveis,
        'emprestados': emprestados,
        'manutencao': manutencao
    }
    
    return render_template('dashboard.html', dispositivos=dispositivos, estatisticas=estatisticas)

@app.route('/emprestar/<int:id>', methods=['GET', 'POST'])
def emprestar(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        responsavel = request.form['responsavel']
        data_prevista = request.form['data_devolucao_prevista']
        admin_id = session['user_id']

        with ligar_banco() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dispositivos SET status = 'Emprestado' WHERE id = ?", (id,))
            cursor.execute("""
                INSERT INTO movimentacoes (id_dispositivo, responsavel_retirada, data_devolucao_prevista, id_admin)
                VALUES (?, ?, ?, ?)
            """, (id, responsavel, data_prevista, admin_id))
        
        return redirect(url_for('dashboard'))

    conn = ligar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dispositivos WHERE id = ?", (id,))
    dispositivo = cursor.fetchone()
    conn.close()
    
    return render_template('emprestar.html', dispositivo=dispositivo)

@app.route('/devolver/<int:id>')
def devolver(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with ligar_banco() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE dispositivos SET status = 'Disponível' WHERE id = ?", (id,))
        cursor.execute("""
            UPDATE movimentacoes 
            SET data_devolucao_real = CURRENT_TIMESTAMP 
            WHERE id_dispositivo = ? AND data_devolucao_real IS NULL
        """, (id,))
        
    return redirect(url_for('dashboard'))

@app.route('/manutencao/<int:id>')
def manutencao(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with ligar_banco() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE dispositivos SET status = 'Manutenção' WHERE id = ?", (id,))
        
    return redirect(url_for('dashboard'))

@app.route('/retirar_manutencao/<int:id>')
def retirar_manutencao(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with ligar_banco() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE dispositivos SET status = 'Disponível' WHERE id = ?", (id,))
        
    return redirect(url_for('dashboard'))

@app.route('/historico/<int:id>')
def historico(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = ligar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM dispositivos WHERE id = ?", (id,))
    dispositivo = cursor.fetchone()
    
    cursor.execute("""
        SELECT m.*, a.nome as admin_nome 
        FROM movimentacoes m
        LEFT JOIN usuarios_admin a ON m.id_admin = a.id
        WHERE m.id_dispositivo = ?
        ORDER BY m.id DESC
    """, (id,))
    movimentacoes = cursor.fetchall()
    conn.close()
    
    return render_template('historico.html', dispositivo=dispositivo, movimentacoes=movimentacoes)

@app.route('/editar_dispositivo/<int:id>', methods=['GET', 'POST'])
def editar_dispositivo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = ligar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        patrimonio = request.form['patrimonio']
        serial = request.form['serial']
        
        try:
            cursor.execute("""
                UPDATE dispositivos 
                SET tipo = ?, patrimonio = ?, serial = ? 
                WHERE id = ?
            """, (tipo, patrimonio, serial, id))
            conn.commit()
            conn.close()
            flash("Dispositivo updated com sucesso!")
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Erro: Este número de patrimônio já está sendo usado por outro dispositivo!")
            return redirect(url_for('editar_dispositivo', id=id))
            
    cursor.execute("SELECT * FROM dispositivos WHERE id = ?", (id,))
    dispositivo = cursor.fetchone()
    conn.close()
    return render_template('editar_dispositivo.html', dispositivo=dispositivo)

@app.route('/excluir_dispositivo/<int:id>')
def excluir_dispositivo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    with ligar_banco() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE id_dispositivo = ?", (id,))
        tem_historico = cursor.fetchone()[0]
        
        if tem_historico > 0:
            flash("Não é possível excluir! Este dispositivo possui histórico de uso para auditoria.")
        else:
            cursor.execute("DELETE FROM dispositivos WHERE id = ?", (id,))
            flash("Dispositivo removido do inventário com sucesso!")
            
    return redirect(url_for('dashboard'))

@app.route('/adicionar_dispositivo', methods=['GET', 'POST'])
def adicionar_dispositivo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        tipo = request.form['tipo']
        patrimonio = request.form['patrimonio'].strip().upper()
        serial = request.form['serial'].strip()
        
        conn = ligar_banco()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO dispositivos (tipo, patrimonio, serial) 
                VALUES (?, ?, ?)
            """, (tipo, patrimonio, serial if serial else None))
            conn.commit()
            conn.close()
            flash(f"{tipo} {patrimonio} adicionado ao inventário com sucesso!")
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Erro: Já existe um dispositivo cadastrado com este número de patrimônio!")
            return redirect(url_for('adicionar_dispositivo'))
            
    return render_template('adicionar_dispositivo.html')

@app.route('/lote_emprestar_tela', methods=['POST'])
def lote_emprestar_tela():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ids = request.form.getlist('dispositivos_ids')
    if not ids:
        flash("Nenhum item selecionado.")
        return redirect(url_for('dashboard'))
    
    conn = ligar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    placeholders = ','.join('?' for _ in ids)
    cursor.execute(f"SELECT * FROM dispositivos WHERE id IN ({placeholders})", ids)
    dispositivos_selecionados = cursor.fetchall()
    conn.close()
    
    return render_template('lote_emprestar.html', dispositivos=dispositivos_selecionados, ids=ids)

@app.route('/lote_emprestar_confirmar', methods=['POST'])
def lote_emprestar_confirmar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ids = request.form.getlist('ids')
    responsavel = request.form['responsavel'].strip()
    data_prevista = request.form['data_devolucao_prevista']
    admin_id = session['user_id']
    
    if ids:
        with ligar_banco() as conn:
            cursor = conn.cursor()
            for item_id in ids:
                cursor.execute("UPDATE dispositivos SET status = 'Emprestado' WHERE id = ?", (item_id,))
                cursor.execute("""
                    INSERT INTO movimentacoes (id_dispositivo, responsavel_retirada, data_devolucao_prevista, id_admin)
                    VALUES (?, ?, ?, ?)
                """, (item_id, responsavel, data_prevista, admin_id))
        
        flash(f"Sucesso! Empréstimo em lote realizado para {len(ids)} dispositivos.")
        
    return redirect(url_for('dashboard'))

@app.route('/lote_devolver', methods=['POST'])
def lote_devolver():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ids = request.form.getlist('dispositivos_ids')
    
    if ids:
        with ligar_banco() as conn:
            cursor = conn.cursor()
            for item_id in ids:
                cursor.execute("UPDATE dispositivos SET status = 'Disponível' WHERE id = ?", (item_id,))
                cursor.execute("""
                    UPDATE movimentacoes 
                    SET data_devolucao_real = CURRENT_TIMESTAMP 
                    WHERE id_dispositivo = ? AND data_devolucao_real IS NULL
                """, (item_id,))
                
        flash(f"Sucesso! {len(ids)} dispositivos foram devolvidos em lote.")
        
    return redirect(url_for('dashboard'))

@app.route('/lote_manutencao', methods=['POST'])
def lote_manutencao():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ids = request.form.getlist('dispositivos_ids')
    
    if ids:
        with ligar_banco() as conn:
            cursor = conn.cursor()
            for item_id in ids:
                cursor.execute("UPDATE dispositivos SET status = 'Manutenção' WHERE id = ?", (item_id,))
                
        flash(f"Sucesso! {len(ids)} dispositivos foram enviados para a manutenção.")
        
    return redirect(url_for('dashboard'))

@app.errorhandler(Exception)
def trata_erro_geral(e):
    mensagem_erro = str(e)
    return render_template('erro.html', mensagem=mensagem_erro), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)