import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'admin.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de logs de acesso
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT,
        user_agent TEXT,
        path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de uso de ferramentas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tool_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT,
        ip_address TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de administradores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    ''')
    
    # Criar usuário admin padrão se não existir
    cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        # Senha padrão: admin123 (o usuário deve ser orientado a mudar depois)
        password_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ('admin', password_hash))
    
    conn.commit()
    conn.close()

def log_access(ip, user_agent, path):
    conn = get_db_connection()
    conn.execute('INSERT INTO access_logs (ip_address, user_agent, path) VALUES (?, ?, ?)',
                 (ip, user_agent, path))
    conn.commit()
    conn.close()

def log_tool_usage(tool_name, ip):
    conn = get_db_connection()
    conn.execute('INSERT INTO tool_usage (tool_name, ip_address) VALUES (?, ?)',
                 (tool_name, ip))
    conn.commit()
    conn.close()

def update_admin_password(username, new_password_hash):
    conn = get_db_connection()
    conn.execute('UPDATE admins SET password_hash = ? WHERE username = ?', (new_password_hash, username))
    conn.commit()
    conn.close()

def get_stats(start_date=None, end_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_filter = ""
    params = []
    
    if start_date and end_date:
        date_filter = " WHERE timestamp BETWEEN ? AND ?"
        params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
    
    # Total de acessos
    cursor.execute(f'SELECT COUNT(*) FROM access_logs{date_filter}', params)
    total_accesses = cursor.fetchone()[0]
    
    # Ferramentas mais usadas
    cursor.execute(f'SELECT tool_name, COUNT(*) as count FROM tool_usage{date_filter} GROUP BY tool_name ORDER BY count DESC', params)
    tool_stats = [dict(row) for row in cursor.fetchall()]
    
    # IPs mais frequentes
    cursor.execute(f'SELECT ip_address, COUNT(*) as count FROM access_logs{date_filter} GROUP BY ip_address ORDER BY count DESC LIMIT 10', params)
    top_ips = [dict(row) for row in cursor.fetchall()]
    
    # Acessos recentes (sempre mostra os últimos 50, mas respeita o filtro se houver)
    cursor.execute(f'SELECT * FROM access_logs{date_filter} ORDER BY timestamp DESC LIMIT 50', params)
    recent_accesses = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {
        'total_accesses': total_accesses,
        'tool_stats': tool_stats,
        'top_ips': top_ips,
        'recent_accesses': recent_accesses
    }

if __name__ == '__main__':
    init_db()
    print("Banco de dados inicializado com sucesso.")
