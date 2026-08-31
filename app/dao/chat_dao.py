from datetime import datetime

from app import db
from app.models import Conversation, ConversationMember, Message, MessageReaction, User


def get_conversations(user_id):
    return (
        Conversation.query.join(ConversationMember)
        .filter(ConversationMember.user_id == user_id)
        .order_by(Conversation.updated_date.desc())
        .all()
    )


def get_other_member(conversation_id, current_user_id):
    member = ConversationMember.query.filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id != current_user_id,
    ).first()
    return User.query.get(member.user_id) if member else None


def get_latest_message(conversation_id):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_date.desc()).first()


def get_messages(conversation_id):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_date.asc()).all()


def is_member(conversation_id, user_id):
    return (
        ConversationMember.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
        ).first()
        is not None
    )


def create_private_conversation(user1_id, user2_id):
    convs1 = db.session.query(ConversationMember.conversation_id).filter_by(user_id=user1_id)
    convs2 = db.session.query(ConversationMember.conversation_id).filter_by(user_id=user2_id)
    common = convs1.intersect(convs2).all()

    for (c_id,) in common:
        c = Conversation.query.get(c_id)
        if c and not c.is_group:
            return c

    conv = Conversation(is_group=False)
    db.session.add(conv)
    db.session.flush()

    db.session.add(ConversationMember(conversation_id=conv.id, user_id=user1_id))
    db.session.add(ConversationMember(conversation_id=conv.id, user_id=user2_id))
    db.session.commit()
    return conv


def send_message(conversation_id, sender_id, content, attachment=None):
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        attachment=attachment,
    )
    db.session.add(msg)
    conv = Conversation.query.get(conversation_id)
    if conv:
        conv.updated_date = datetime.now()
    db.session.commit()
    return msg


def get_message(message_id):
    return Message.query.get(message_id)


def edit_message(message_id, content):
    msg = Message.query.get(message_id)
    if msg:
        msg.content = content
        msg.is_edited = True
        db.session.commit()
    return msg


def delete_message(message_id):
    msg = Message.query.get(message_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        return True
    return False


def react_message(message_id, user_id, emoji):
    r = MessageReaction.query.filter_by(message_id=message_id, user_id=user_id).first()
    if r:
        r.emoji = emoji
    else:
        db.session.add(MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji))
    db.session.commit()


def remove_reaction(message_id, user_id):
    r = MessageReaction.query.filter_by(message_id=message_id, user_id=user_id).first()
    if r:
        db.session.delete(r)
        db.session.commit()


def get_message_reactions(message_id):
    return MessageReaction.query.filter_by(message_id=message_id).all()


def update_last_read(conversation_id, user_id):
    m = ConversationMember.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()
    if m:
        m.last_read = datetime.now()
        db.session.commit()


def search_messages(conversation_id, keyword):
    return (
        Message.query.filter(
            Message.conversation_id == conversation_id,
            Message.content.ilike(f"%{keyword}%"),
        )
        .order_by(Message.created_date.desc())
        .limit(20)
        .all()
    )


def count_unread(user_id):
    total = 0
    members = ConversationMember.query.filter_by(user_id=user_id).all()
    for m in members:
        q = Message.query.filter(
            Message.conversation_id == m.conversation_id,
            Message.sender_id != user_id,
        )
        if m.last_read:
            q = q.filter(Message.created_date > m.last_read)
        total += q.count()
    return total
