from app import dao


def get_user_conversations(user_id):
    conversations = dao.get_conversations(user_id)
    data = []
    for c in conversations:
        other_user = dao.get_other_member(c.id, user_id)
        latest_msg = dao.get_latest_message(c.id)
        data.append(
            {
                "id": c.id,
                "title": other_user.username if other_user else "Cuộc trò chuyện",
                "avatar": other_user.avatar if other_user else "/static/images/default-avatar.png",
                "last_message": latest_msg.content if latest_msg else "",
                "updated_at": c.updated_date.isoformat() if c.updated_date else None,
            }
        )
    return data


def get_conversation_messages(conversation_id, user_id):
    if not dao.is_member(conversation_id, user_id):
        return None, "Forbidden"

    messages = dao.get_messages(conversation_id)
    data = []
    for m in messages:
        reactions = dao.get_message_reactions(m.id)
        data.append(
            {
                "id": m.id,
                "content": m.content,
                "attachment": m.attachment,
                "sender_id": m.sender_id,
                "is_edited": m.is_edited,
                "created_date": m.created_date.isoformat() if m.created_date else None,
                "reactions": [{"user_id": r.user_id, "emoji": r.emoji} for r in reactions],
            }
        )
    dao.update_last_read(conversation_id, user_id)
    return data, None


def create_private_conversation(user1_id, user2_id):
    if user1_id == user2_id:
        return None, "Bạn không thể nhắn tin với chính mình."
    conv = dao.create_private_conversation(user1_id, user2_id)
    if not conv:
        return None, "Không thể tạo cuộc trò chuyện."
    return conv, None


def search_messages(conversation_id, user_id, keyword):
    if not dao.is_member(conversation_id, user_id):
        return None, "Forbidden"
    return dao.search_messages(conversation_id, keyword), None


def count_unread(user_id):
    return dao.count_unread(user_id)
