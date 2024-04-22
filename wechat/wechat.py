import os
import asyncio
from wechaty import Contact, FileBox, Message, Wechaty, ScanStatus
from wechaty_puppet import MessageType
from api import api_ppocr,api_embed
import datetime
from search import search
from dataset import initialize_database,load_messages_from_database
from process_image import process_image
from judging_room import judging_room

# 定义全局列表用于存储消息信息
messages_info = []
COURSES = ['数图','信号','软考']


def main(
    WECHATY_PUPPET_SERVICE_TOKEN="puppet_padlocal_32f5a1fd70f2499f9fe1bd669fc69753",
    WECHATY_PUPPET_SERVICE_ENDPOINT="58.199.161.165:19541",
):
    os.environ["WECHATY_PUPPET_SERVICE_TOKEN"] = WECHATY_PUPPET_SERVICE_TOKEN
    os.environ["WECHATY_PUPPET_SERVICE_ENDPOINT"] = WECHATY_PUPPET_SERVICE_ENDPOINT

    
    # 连接到 SQLite 数据库
    conn,cursor = initialize_database('messages.db')

    # 从数据库加载消息到全局列表
    load_messages_from_database(messages_info,cursor)
    
        
    async def on_login(user: Contact):
        """
        当机器人登录成功时调用这个函数。
        """
        print(f'{user} 登录成功')    

    async def on_message(msg: Message):
        """
        消息处理函数
        """
        global last_message_time

        #判断属于哪一个群
        if msg.room():#检测是否有有消息在群里发送
       
            me = msg.wechaty.user_self()  # 获取机器人自己的用户信息
            name = await msg.room().alias(me)  # 获取机器人在当前群聊中的昵称（别名）
            # await msg.say(f"大家好，我在这个群的昵称是 '{name}'！")

            #判断群名
            most_similar_course = await judging_room(msg,COURSES, api_embed)

            #检测接收消息的群名是否是软考群
            if most_similar_course == "数图":

                course = "shutu"

                text = None
                prompt = None

                # 获取消息发送者
                sender = msg.talker()
                
                 # 检查发送者名称不是 '测试' 且消息文本中包含 '@'
                if sender.name != name:

                    message_dict = None  # 提前定义并初始化变量
                    
                    # print(f"发送者: {sender.name}")

                    #获取当前系统时间
                    current_time = datetime.datetime.now()
                    # print(f"当前系统时间是: {current_time}")

                    #检查发送的消息是否为文本信息
                    if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
                        # 不将 '@测试' 存储到 text 中
                        if f'@{name}' in msg.text():
                            text = msg.text().replace(f"@{name}"," ")
                            message_dict = {
                                'name': sender.name,
                                'content': text,
                                'time': current_time,
                                'type': 'text',
                                'reply': ''  # 默认为空
                            }

                    #检查发送消息是否为图片信息
                    elif msg.type() == MessageType.MESSAGE_TYPE_IMAGE:
                 
                        try:
                            prompt=await process_image(msg,api_ppocr)  

                        except:
                            prompt=[]
                            prompt = '图片处理失败'

                        message_dict = {
                                'name': sender.name,
                                'content': prompt,
                                'time': current_time,
                                'type': 'image',
                                'reply': ''  # 默认为空
                            }
                   
                    #更新字典
                    if message_dict:
                        messages_info.append(message_dict)
                        
                        # 插入发送消息到数据库
                        sql = "INSERT INTO messages (name, content, time, type, reply) VALUES (?, ?, ?, ?, ?)"
                        val = (message_dict['name'], message_dict['content'], message_dict['time'], message_dict['type'], message_dict['reply'])
                        cursor.execute(sql, val)
                        conn.commit()


                        #回复文本消息
                        if text :
                           # 从数据库中获取该发送者在过去6秒内发送的最后一条图片消息
                            time_limit = (current_time - datetime.timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S.%f")
                            cursor.execute('SELECT content FROM messages WHERE name = ? AND type = ? AND time > ? ORDER BY time DESC LIMIT 1', (sender.name, 'image', time_limit))
                            last_image_message = cursor.fetchone()

                            img_prompt = last_image_message[0] if last_image_message else ""

                           

                            # 如果在过去六秒内有图片消息
                            if img_prompt:
                                output, citation = search(db_name=course, collection_name='book1', input=text, img_prompt=img_prompt)
                            else:
                                output, citation = search(db_name=course, collection_name='book1', input=text)

                            if citation:
                                output += '\n@{0} 您可参考: {1}'.format(sender.name, citation)

                            await msg.say(output)   
                                      
                            # 合并文本和图片消息内容
                            combined_content = f"Text: {text}\nImages: {img_prompt}" 

                            robot_message_dict = {
                                        'name': sender.name,
                                        'content': combined_content,
                                        'time': current_time,
                                        'type': 'combined',
                                        'reply': output  # 默认为空
                                    }
                            
                            # 使用字典值插入数据库
                            sql = "INSERT INTO messages (name, content, time, type, reply) VALUES (?, ?, ?, ?, ?)"
                            val = (robot_message_dict['name'], robot_message_dict['content'], robot_message_dict['time'], robot_message_dict['type'], robot_message_dict['reply'])
                            cursor.execute(sql, val)
                            conn.commit()
                            messages_info.append(message_dict)    
                            # print(f"所有的信息：{messages_info}") 
                        
                        else:
                            pass


    async def start_bot():
        bot = Wechaty()
        bot.on('login',     on_login)
        bot.on('message',   on_message)
        await bot.start()
        

    asyncio.run(start_bot())


import fire
if __name__ == "__main__":
    fire.Fire(main())