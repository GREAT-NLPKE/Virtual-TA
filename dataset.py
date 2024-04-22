import sqlite3

def initialize_database(db_name):
    """
    初始化数据库，创建必要的表

    :param db_name: 数据库文件的名称
    """
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 创建一个表来存储消息信息，如果表已存在则忽略
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        name TEXT,
        content TEXT,
        time DATETIME,
        type TEXT,
        reply TEXT
    )
    ''')
    conn.commit()
    return conn,cursor


def load_messages_from_database(messages_info,cursor):
    """
    从数据库加载所有消息并存储到全局列表中
    """
    # 确保查询也包括了 reply 字段
    cursor.execute('SELECT name, content, time, type, reply FROM messages')
    rows = cursor.fetchall()
    for row in rows:
        message_dict = {
            'name': row[0],
            'content': row[1],
            'time': row[2],
            'type': row[3],
            'reply': row[4]  # 添加 reply 字段
        }
        messages_info.append(message_dict)
    print(f"Loaded {len(messages_info)} messages from the database.")

