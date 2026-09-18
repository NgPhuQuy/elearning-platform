import uuid

import pytest

from app import dao, db, socketio
from app.dao import chat_dao
from app.index import app as flask_app
from app.models import Conversation, ConversationMember, User


@pytest.fixture
def chat_users():
    flask_app.config.update(TESTING=True)
    suffix = uuid.uuid4().hex[:6]
    u1_username = f"chat_u1_{suffix}"
    u2_username = f"chat_u2_{suffix}"
    password = "ChatPassword123"

    with flask_app.app_context():
        user1 = User(
            username=u1_username,
            password=dao.hash_password(password),
            email=f"{u1_username}@test.com",
            first_name="Alice",
            last_name="Nguyen",
            phone=f"09{uuid.uuid4().int % 100000000:08d}",
        )
        user2 = User(
            username=u2_username,
            password=dao.hash_password(password),
            email=f"{u2_username}@test.com",
            first_name="Bob",
            last_name="Tran",
            phone=f"09{uuid.uuid4().int % 100000000:08d}",
        )
        db.session.add_all([user1, user2])
        db.session.commit()
        user1_id = user1.id
        user2_id = user2.id

    yield {
        "u1": {"id": user1_id, "username": u1_username, "password": password, "name": "Alice Nguyen"},
        "u2": {"id": user2_id, "username": u2_username, "password": password, "name": "Bob Tran"},
    }

    # Cleanup
    with flask_app.app_context():
        memberships = ConversationMember.query.filter(ConversationMember.user_id.in_([user1_id, user2_id])).all()
        conv_ids = {m.conversation_id for m in memberships}
        for cid in conv_ids:
            conv = db.session.get(Conversation, cid)
            if conv:
                db.session.delete(conv)
        for uid in [user1_id, user2_id]:
            u = db.session.get(User, uid)
            if u:
                db.session.delete(u)
        db.session.commit()


def test_chat_page_renders_with_valid_current_user_id(chat_users):
    with flask_app.test_client() as client:
        # Login user 1
        res_login = client.post(
            "/login",
            data={"username": chat_users["u1"]["username"], "password": chat_users["u1"]["password"]},
        )
        assert res_login.status_code == 200

        # Access /chat
        res_chat = client.get("/chat")
        assert res_chat.status_code == 200
        html = res_chat.get_data(as_text=True)

        # Must have valid integer user ID without syntax error
        expected_line = f"window.CURRENT_USER_ID = {chat_users['u1']['id']};"
        assert expected_line in html
        assert "window.CURRENT_USER_ID = ;" not in html


def test_search_users_endpoints(chat_users):
    with flask_app.test_client() as client:
        client.post(
            "/login",
            data={"username": chat_users["u1"]["username"], "password": chat_users["u1"]["password"]},
        )

        # 1. Test /api/users/search (called by chat.js)
        res1 = client.get(f"/api/users/search?keyword={chat_users['u2']['username']}")
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert len(data1) >= 1
        assert data1[0]["id"] == chat_users["u2"]["id"]
        assert data1[0]["username"] == chat_users["u2"]["username"]
        assert "name" in data1[0]
        assert "full_name" in data1[0]

        # 2. Test /api/chat/users/search
        res2 = client.get("/api/chat/users/search?keyword=Bob")
        assert res2.status_code == 200
        data2 = res2.get_json()
        assert any(u["id"] == chat_users["u2"]["id"] for u in data2)


def test_create_conversation_and_messages_flow(chat_users):
    with flask_app.test_client() as client:
        client.post(
            "/login",
            data={"username": chat_users["u1"]["username"], "password": chat_users["u1"]["password"]},
        )

        # 1. Create private conversation with user 2
        res_create = client.post(f"/api/chat/private/{chat_users['u2']['id']}")
        assert res_create.status_code == 200
        conv_id = res_create.get_json()["conversation_id"]
        assert conv_id is not None

        # 2. Get user conversations: should include other_user object and updated_date
        res_convs = client.get("/api/chat/conversations")
        assert res_convs.status_code == 200
        convs = res_convs.get_json()
        found = [c for c in convs if c["id"] == conv_id]
        assert len(found) == 1
        assert found[0]["other_user"] is not None
        assert found[0]["other_user"]["id"] == chat_users["u2"]["id"]
        assert found[0]["other_user"]["username"] == chat_users["u2"]["username"]
        assert found[0]["is_group"] is False
        assert "updated_date" in found[0]

        # 3. Add message directly
        with flask_app.app_context():
            chat_dao.send_message(
                conversation_id=conv_id,
                sender_id=chat_users["u1"]["id"],
                content="Xin chao socket",
            )

        # 4. Get messages: verify sender_name is populated
        res_msgs = client.get(f"/api/chat/{conv_id}/messages")
        assert res_msgs.status_code == 200
        msgs = res_msgs.get_json()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Xin chao socket"
        assert msgs[0]["sender_name"] == "Alice Nguyen"
        assert msgs[0]["sender_id"] == chat_users["u1"]["id"]

        # 5. Search message
        res_search = client.get(f"/api/chat/{conv_id}/search?keyword=socket")
        assert res_search.status_code == 200
        results = res_search.get_json()
        assert len(results) == 1
        assert results[0]["id"] == msgs[0]["id"]


def test_socketio_message_emission(chat_users):
    with flask_app.test_client() as client1:
        client1.post(
            "/login",
            data={"username": chat_users["u1"]["username"], "password": chat_users["u1"]["password"]},
        )
        res_create = client1.post(f"/api/chat/private/{chat_users['u2']['id']}")
        conv_id = res_create.get_json()["conversation_id"]

        sio_client = socketio.test_client(flask_app, flask_test_client=client1)
        assert sio_client.is_connected()

        # Join room
        sio_client.emit("join", {"conversation_id": conv_id})

        # Send message
        sio_client.emit(
            "send_message",
            {"conversation_id": conv_id, "content": "Hello real-time chat"},
        )

        received = sio_client.get_received()
        new_msg_events = [e for e in received if e["name"] == "new_message"]
        assert len(new_msg_events) == 1
        payload = new_msg_events[0]["args"][0]
        assert payload["conversation_id"] == conv_id
        assert payload["content"] == "Hello real-time chat"
        assert payload["sender_name"] == "Alice Nguyen"
        assert payload["sender_id"] == chat_users["u1"]["id"]

        # Test edit message
        msg_id = payload["id"]
        sio_client.emit("edit_message", {"message_id": msg_id, "content": "Updated content"})
        received_edit = sio_client.get_received()
        edit_events = [e for e in received_edit if e["name"] == "message_edited"]
        assert len(edit_events) == 1
        assert edit_events[0]["args"][0]["content"] == "Updated content"

        # Test delete message
        sio_client.emit("delete_message", {"message_id": msg_id})
        received_del = sio_client.get_received()
        del_events = [e for e in received_del if e["name"] == "message_deleted"]
        assert len(del_events) == 1
        assert del_events[0]["args"][0]["id"] == msg_id

        sio_client.disconnect()
