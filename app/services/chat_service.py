from app import dao


def get_user_conversations(user_id):
    conversations = dao.get_conversations(user_id)
    data = []
    for c in conversations:
        other_user = dao.get_other_member(c.id, user_id)
        latest_msg = dao.get_latest_message(c.id)
        other_user_data = None
        if other_user:
            full_name = f"{other_user.first_name or ''} {other_user.last_name or ''}".strip() or other_user.username
            other_user_data = {
                "id": other_user.id,
                "username": other_user.username,
                "name": full_name,
                "full_name": full_name,
                "avatar": other_user.avatar,
            }
        display_title = (
            (c.title or "Nhóm học tập")
            if c.is_group
            else (other_user_data["name"] if other_user_data else "Cuộc trò chuyện")
        )
        display_avatar = (
            (c.image or "/static/images/default-avatar.png")
            if c.is_group
            else (
                other_user_data["avatar"]
                if other_user_data and other_user_data["avatar"]
                else "/static/images/default-avatar.png"
            )
        )
        data.append(
            {
                "id": c.id,
                "title": display_title,
                "avatar": display_avatar,
                "is_group": c.is_group,
                "other_user": other_user_data,
                "last_message": latest_msg.content if latest_msg else "",
                "updated_at": c.updated_date.isoformat() if c.updated_date else None,
                "updated_date": c.updated_date.isoformat() if c.updated_date else None,
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
        sender = m.sender
        sender_name = (
            f"{sender.first_name or ''} {sender.last_name or ''}".strip() or sender.username if sender else "Người dùng"
        )
        data.append(
            {
                "id": m.id,
                "content": m.content,
                "attachment": m.attachment,
                "sender_id": m.sender_id,
                "sender_name": sender_name,
                "sender_avatar": sender.avatar if sender else None,
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
