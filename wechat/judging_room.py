import numpy as np

async def judging_room(msg, COURSES, api_embed):
    # 获取消息所在的房间
    room = msg.room()
    if room:
        room_name = await room.topic()  # 读取群名
        print(f'Message in group: {room_name}')
        room_name = str(room_name)
        embedding_group = api_embed(room_name)

        vector1 = np.array(embedding_group)  # 转为数组

        embedding_course = api_embed(COURSES)

        max_similarity = -1  # 初始化最大相似度
        most_similar_index = -1  # 初始化最相似列表的索引

        # 遍历 embedding_course 并计算每个子列表与 vector1 的余弦相似度
        for index, sub_list in enumerate(embedding_course):
            vector2 = np.array(sub_list)
            similarity = cosine_similarity(vector1, vector2)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_index = index

        most_similar_course = COURSES[most_similar_index]
        print(f"相似度最高的课程: {most_similar_course} 其相似度为: {max_similarity}")

        return most_similar_course
    else:
        print("Message is not in a room.")
        return None, -1

# 假设的 cosine_similarity 函数实现
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)
