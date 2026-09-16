from flask import jsonify, render_template, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from app import app, dao, socketio
from app.decorators import login_required, socket_auth_required
from app.services import chat_service


@app.get("/chat")
@login_required
def chat_view():
    return render_template("chat/index.html")


@app.get("/api/chat/conversations")
@login_required
def api_conversations():
    data = chat_service.get_user_conversations(current_user.id)
    return jsonify(data)


@app.get("/api/chat/<int:conversation_id>/messages")
@login_required
def api_messages(conversation_id):
    data, error = chat_service.get_conversation_messages(conversation_id, current_user.id)
    if error:
        return jsonify({"error": error}), 403
    return jsonify(data)


@app.get("/api/chat/users/search")
@login_required
def api_search_users():
    keyword = request.args.get("keyword", "").strip()
    users = dao.search_users(keyword, current_user.id)
    return jsonify([{"id": u.id, "name": f"{u.first_name} {u.last_name}", "avatar": u.avatar} for u in users])


@app.post("/api/chat/private/<int:user_id>")
@login_required
def api_create_private(user_id):
    conv, error = chat_service.create_private_conversation(current_user.id, user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"conversation_id": conv.id})


@app.get("/api/chat/<int:conversation_id>/search")
@login_required
def api_search_message(conversation_id):
    keyword = request.args.get("keyword", "").strip()
    messages, error = chat_service.search_messages(conversation_id, current_user.id, keyword)
    if error:
        return jsonify({"error": error}), 403
    return jsonify([{"id": m.id, "content": m.content} for m in messages])


@app.get("/api/chat/unread")
@login_required
def api_unread():
    return jsonify({"count": chat_service.count_unread(current_user.id)})


@socketio.on("join")
@socket_auth_required
def handle_join(data):
    if not isinstance(data, dict):
        return
    conversation_id = data.get("conversation_id")
    if not conversation_id or not dao.is_member(conversation_id, current_user.id):
        return
    join_room(f"conversation_{conversation_id}")


@socketio.on("leave")
@socket_auth_required
def handle_leave(data):
    if not isinstance(data, dict):
        return
    conversation_id = data.get("conversation_id")
    if conversation_id:
        leave_room(f"conversation_{conversation_id}")


@socketio.on("send_message")
@socket_auth_required
def handle_send_message(data):
    if not isinstance(data, dict):
        return
    conversation_id = data.get("conversation_id")
    content = data.get("content")
    if not conversation_id or not content or not dao.is_member(conversation_id, current_user.id):
        return

    message = dao.send_message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=content,
        attachment=data.get("attachment"),
    )
    if not message:
        return

    emit(
        "new_message",
        {
            "id": message.id,
            "conversation_id": conversation_id,
            "content": message.content,
            "attachment": message.attachment,
            "sender_id": message.sender_id,
            "created_date": message.created_date.isoformat(),
        },
        room=f"conversation_{conversation_id}",
    )


@socketio.on("edit_message")
@socket_auth_required
def handle_edit(data):
    if not isinstance(data, dict):
        return
    message_id = data.get("message_id")
    content = data.get("content")
    if not message_id or not content:
        return

    message = dao.get_message(message_id)
    if not message or message.sender_id != current_user.id:
        return

    message = dao.edit_message(message.id, content)
    if not message:
        return

    emit(
        "message_edited",
        {"id": message.id, "content": message.content, "edited": True},
        room=f"conversation_{message.conversation_id}",
    )


@socketio.on("delete_message")
@socket_auth_required
def handle_delete(data):
    if not isinstance(data, dict):
        return
    message_id = data.get("message_id")
    if not message_id:
        return

    message = dao.get_message(message_id)
    if not message or message.sender_id != current_user.id:
        return

    conversation_id = message.conversation_id
    dao.delete_message(message.id)
    emit("message_deleted", {"id": message.id}, room=f"conversation_{conversation_id}")


@socketio.on("react_message")
@socket_auth_required
def handle_reaction(data):
    if not isinstance(data, dict):
        return
    message_id = data.get("message_id")
    emoji = data.get("emoji")
    if not message_id or not emoji:
        return

    message = dao.get_message(message_id)
    if not message or not dao.is_member(message.conversation_id, current_user.id):
        return

    dao.react_message(message.id, current_user.id, emoji)
    reactions = dao.get_message_reactions(message.id)
    emit(
        "message_reacted",
        {"message_id": message.id, "reactions": [{"user_id": r.user_id, "emoji": r.emoji} for r in reactions]},
        room=f"conversation_{message.conversation_id}",
    )


@socketio.on("remove_reaction")
@socket_auth_required
def handle_remove_reaction(data):
    if not isinstance(data, dict):
        return
    message_id = data.get("message_id")
    if not message_id:
        return

    message = dao.get_message(message_id)
    if not message or not dao.is_member(message.conversation_id, current_user.id):
        return

    dao.remove_reaction(message.id, current_user.id)
    reactions = dao.get_message_reactions(message.id)
    emit(
        "message_reacted",
        {"message_id": message.id, "reactions": [{"user_id": r.user_id, "emoji": r.emoji} for r in reactions]},
        room=f"conversation_{message.conversation_id}",
    )


@socketio.on("read_conversation")
@socket_auth_required
def handle_read(data):
    if not isinstance(data, dict):
        return
    conversation_id = data.get("conversation_id")
    if not conversation_id or not dao.is_member(conversation_id, current_user.id):
        return

    dao.update_last_read(conversation_id, current_user.id)
    emit(
        "conversation_read",
        {"conversation_id": conversation_id, "user_id": current_user.id},
        room=f"conversation_{conversation_id}",
    )
