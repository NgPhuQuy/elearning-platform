
document.addEventListener("DOMContentLoaded", function () {
    if (typeof io === "undefined" || !document.getElementById("conversationList")) {
        return;
    }

    const socket = io(window.location.origin, {
        transports: ["websocket", "polling"],
    });




    let conversations = [];
    let activeConversationId = null;

    const conversationList =
        document.getElementById("conversationList");

    const messageList =
        document.getElementById("messageList");

    const messageForm =
        document.getElementById("messageForm");

    const messageInput =
        document.getElementById("messageInput");

    const chatInputContainer =
        document.getElementById("chatInputContainer");

    const chatHeaderEmpty =
        document.getElementById("chatHeaderEmpty");

    const chatHeaderContent =
        document.getElementById("chatHeaderContent");

    const chatHeaderName =
        document.getElementById("chatHeaderName");

    const chatHeaderAvatar =
        document.getElementById("chatHeaderAvatar");

    const chatHeaderStatus =
        document.getElementById("chatHeaderStatus");

    const infoEmpty =
        document.getElementById("infoEmpty");

    const infoContent =
        document.getElementById("infoContent");

    const infoAvatar =
        document.getElementById("infoAvatar");

    const infoName =
        document.getElementById("infoName");

    const infoRole =
        document.getElementById("infoRole");

    initNewChat();
    initMessageSearch();


    function initNewChat() {


const newChatBtn =
    document.getElementById("newChatBtn");

const startChatBtn =
    document.getElementById("startChatBtn");

const usernameInput =
    document.getElementById("chatUsername");

const errorBox =
    document.getElementById("newChatError");

const modalElement =
    document.getElementById("newChatModal");

const searchResults =
    document.getElementById("userSearchResults");

const selectedUserBox =
    document.getElementById("selectedUser");


if (
    !newChatBtn ||
    !startChatBtn ||
    !usernameInput ||
    !errorBox ||
    !modalElement ||
    !searchResults ||
    !selectedUserBox
) {
    return;
}


const newChatModal =
    new bootstrap.Modal(modalElement);


let selectedUser = null;



newChatBtn.addEventListener(
    "click",
    function () {

        usernameInput.value = "";

        searchResults.innerHTML = "";

        selectedUser = null;

        selectedUserBox.innerHTML = "";

        selectedUserBox.classList.add(
            "d-none"
        );

        errorBox.textContent = "";

        errorBox.classList.add(
            "d-none"
        );

        startChatBtn.disabled = true;

        newChatModal.show();

        setTimeout(
            function () {
                usernameInput.focus();
            },
            300
        );

    }
);



let searchTimeout = null;


usernameInput.addEventListener(
    "input",
    function () {

        const keyword =
            usernameInput.value.trim();


        // Reset user đã chọn
        selectedUser = null;

        selectedUserBox.innerHTML = "";

        selectedUserBox.classList.add(
            "d-none"
        );

        startChatBtn.disabled = true;

        errorBox.textContent = "";

        errorBox.classList.add(
            "d-none"
        );


        clearTimeout(searchTimeout);


        if (!keyword) {

            searchResults.innerHTML = "";

            return;

        }


        /*
         * Debounce:
         * Chờ 300ms sau khi người dùng ngừng nhập
         * rồi mới gọi API.
         */

        searchTimeout =
            setTimeout(
                async function () {

                    try {

                        const response =
                            await fetch(
                                `/api/users/search?keyword=${encodeURIComponent(keyword)}`
                            );


                        if (!response.ok) {

                            throw new Error(
                                "Không thể tìm người dùng."
                            );

                        }


                        const users =
                            await response.json();


                        renderUserSearchResults(
                            users
                        );

                    }
                    catch (error) {

                        console.error(
                            "User search error:",
                            error
                        );

                        searchResults.innerHTML = `
                            <div class="text-danger small p-2">
                                Không thể tìm người dùng.
                            </div>
                        `;

                    }

                },
                300
            );

    }
);




function renderUserSearchResults(
    users
) {

    searchResults.innerHTML = "";


    if (!users.length) {

        searchResults.innerHTML = `
            <div class="text-muted small p-2">
                Không tìm thấy người dùng.
            </div>
        `;

        return;

    }


    users.forEach(
        function (user) {

            const item =
                document.createElement(
                    "button"
                );


            item.type =
                "button";


            item.className =
                "list-group-item list-group-item-action";


            const fullName =
                user.full_name ||
                user.username;


            const avatar =
                user.avatar
                    ? `
                        <img
                            src="${escapeHtml(user.avatar)}"
                            class="rounded-circle me-2"
                            width="40"
                            height="40"
                            style="object-fit: cover;"
                        >
                    `
                    : `
                        <span
                            class="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center me-2"
                            style="width:40px;height:40px;"
                        >
                            ${escapeHtml(
                                getInitials(fullName)
                            )}
                        </span>
                    `;


            item.innerHTML = `

                <div class="d-flex align-items-center">

                    ${avatar}

                    <div>

                        <div class="fw-semibold">
                            ${escapeHtml(fullName)}
                        </div>

                        <small class="text-muted">
                            @${escapeHtml(
                                user.username
                            )}
                        </small>

                    </div>

                </div>

            `;


            item.addEventListener(
                "click",
                function () {

                    selectUser(user);

                }
            );


            searchResults.appendChild(
                item
            );

        }
    );

}




function selectUser(user) {

    selectedUser =
        user;


    searchResults.innerHTML =
        "";


    usernameInput.value =
        user.username;


    const fullName =
        user.full_name ||
        user.username;


    const avatar =
        user.avatar
            ? `
                <img
                    src="${escapeHtml(user.avatar)}"
                    class="rounded-circle me-2"
                    width="40"
                    height="40"
                    style="object-fit: cover;"
                >
            `
            : `
                <span
                    class="rounded-circle bg-primary text-white d-inline-flex align-items-center justify-content-center me-2"
                    style="width:40px;height:40px;"
                >
                    ${escapeHtml(
                        getInitials(fullName)
                    )}
                </span>
            `;


    selectedUserBox.innerHTML = `

        <div class="border rounded p-2">

            <div class="d-flex align-items-center">

                ${avatar}

                <div>

                    <div class="fw-semibold">
                        ${escapeHtml(fullName)}
                    </div>

                    <small class="text-muted">
                        @${escapeHtml(
                            user.username
                        )}
                    </small>

                </div>

            </div>

        </div>

    `;


    selectedUserBox.classList.remove(
        "d-none"
    );


    startChatBtn.disabled =
        false;

}




usernameInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key !== "Enter") {
            return;
        }


        event.preventDefault();


        /*
         * Chỉ cho Enter khi đã chọn user.
         */

        if (
            selectedUser &&
            !startChatBtn.disabled
        ) {

            startChatBtn.click();

        }

    }
);




startChatBtn.addEventListener(
    "click",
    async function () {

        if (!selectedUser) {

            showNewChatError(
                "Vui lòng chọn người dùng."
            );

            return;

        }


        // Không cho tự chat
        if (
            Number(selectedUser.id) ===
            Number(window.CURRENT_USER_ID)
        ) {

            showNewChatError(
                "Bạn không thể nhắn tin với chính mình."
            );

            return;

        }


        startChatBtn.disabled =
            true;


        try {

            const conversationResponse =
                await fetch(
                    `/api/chat/private/${selectedUser.id}`,
                    {
                        method: "POST"
                    }
                );


            if (!conversationResponse.ok) {

                const errorData =
                    await conversationResponse
                        .json()
                        .catch(
                            function () {
                                return null;
                            }
                        );


                throw new Error(
                    errorData?.error ||
                    "Không thể tạo cuộc trò chuyện."
                );

            }


            const conversation =
                await conversationResponse.json();


            // Đóng modal
            newChatModal.hide();


            // Load lại danh sách
            await loadConversations();


            // Mở conversation
            await openConversation(
                conversation.conversation_id
            );

        }
        catch (error) {

            console.error(
                "New chat error:",
                error
            );


            showNewChatError(
                error.message ||
                "Có lỗi xảy ra."
            );

        }
        finally {

            startChatBtn.disabled =
                false;

        }

    }
);


function showNewChatError(
    message
) {

    errorBox.textContent =
        message;

    errorBox.classList.remove(
        "d-none"
    );

}
}


    function initMessageSearch() {
        const searchMessageBtn = document.getElementById("searchMessageBtn");
        const searchModalEl = document.getElementById("searchModal");
        const searchKeywordInput = document.getElementById("search-keyword");
        const searchButton = document.getElementById("search-button");
        const searchResultBox = document.getElementById("search-result");

        if (!searchMessageBtn || !searchModalEl) {
            return;
        }

        const searchModal = new bootstrap.Modal(searchModalEl);

        searchMessageBtn.addEventListener("click", function () {
            if (!activeConversationId) {
                alert("Vui lòng chọn một cuộc trò chuyện để tìm kiếm tin nhắn.");
                return;
            }
            if (searchKeywordInput) {
                searchKeywordInput.value = "";
            }
            if (searchResultBox) {
                searchResultBox.innerHTML = "";
            }
            searchModal.show();
            setTimeout(function () {
                if (searchKeywordInput) {
                    searchKeywordInput.focus();
                }
            }, 300);
        });

        async function performMessageSearch() {
            if (!activeConversationId || !searchKeywordInput || !searchResultBox) {
                return;
            }
            const keyword = searchKeywordInput.value.trim();
            if (!keyword) {
                searchResultBox.innerHTML = "";
                return;
            }
            try {
                const response = await fetch(
                    `/api/chat/${activeConversationId}/search?keyword=${encodeURIComponent(keyword)}`
                );
                if (!response.ok) {
                    throw new Error("Không thể tìm kiếm tin nhắn.");
                }
                const results = await response.json();
                renderMessageSearchResults(results);
            } catch (error) {
                console.error("Search message error:", error);
                searchResultBox.innerHTML = `
                    <div class="text-danger small p-2">
                        Không thể tìm kiếm tin nhắn.
                    </div>
                `;
            }
        }

        function renderMessageSearchResults(results) {
            if (!searchResultBox) {
                return;
            }
            searchResultBox.innerHTML = "";

            if (!results.length) {
                searchResultBox.innerHTML = `
                    <div class="text-muted small p-2">
                        Không tìm thấy tin nhắn phù hợp.
                    </div>
                `;
                return;
            }

            results.forEach(function (msg) {
                const item = document.createElement("button");
                item.type = "button";
                item.className = "list-group-item list-group-item-action text-start";
                item.innerHTML = `<div class="text-truncate">${escapeHtml(msg.content)}</div>`;
                item.addEventListener("click", function () {
                    searchModal.hide();
                    const targetEl = document.querySelector(`[data-message-id="${msg.id}"]`);
                    if (targetEl) {
                        targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
                        targetEl.classList.add("bg-warning-subtle");
                        setTimeout(function () {
                            targetEl.classList.remove("bg-warning-subtle");
                        }, 2000);
                    }
                });
                searchResultBox.appendChild(item);
            });
        }

        if (searchButton) {
            searchButton.addEventListener("click", performMessageSearch);
        }

        if (searchKeywordInput) {
            let debounceTimeout = null;
            searchKeywordInput.addEventListener("input", function () {
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(performMessageSearch, 300);
            });
            searchKeywordInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    clearTimeout(debounceTimeout);
                    performMessageSearch();
                }
            });
        }
    }




    async function loadConversations() {

        try {

            const response =
                await fetch(
                    "/api/chat/conversations"
                );


            if (!response.ok) {

                throw new Error(
                    "Không thể tải cuộc trò chuyện."
                );

            }


            conversations =
                await response.json();


            renderConversations();

        }
        catch (error) {

            console.error(
                "Load conversations error:",
                error
            );


            if (conversationList) {

                conversationList.innerHTML = `
                    <div class="chat-empty">
                        Không thể tải cuộc trò chuyện.
                    </div>
                `;

            }

        }

    }



    function renderConversations() {

        if (!conversationList) {
            return;
        }


        if (!conversations.length) {

            conversationList.innerHTML = `
                <div class="chat-empty">

                    <i class="bi bi-chat-dots fs-3"></i>

                    <p class="mt-2">
                        Chưa có cuộc trò chuyện.
                    </p>

                </div>
            `;

            return;
        }


        conversationList.innerHTML = "";


        conversations.forEach(
            function (conversation) {

                const otherUser =
                    conversation.other_user;


                const name =
                    conversation.is_group
                        ? (
                            conversation.title ||
                            "Nhóm học tập"
                        )
                        : otherUser
                            ? otherUser.name
                            : "Người dùng";


                const hasRealAvatar = Boolean(
                    conversation.avatar &&
                    !conversation.avatar.includes("default-avatar")
                );

                const avatarHtml = hasRealAvatar
                    ? `<img src="${escapeHtml(conversation.avatar)}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">`
                    : escapeHtml(getInitials(name));

                const item =
                    document.createElement("div");

                item.className =
                    "conversation-item";

                if (
                    Number(activeConversationId) ===
                    Number(conversation.id)
                ) {
                    item.classList.add(
                        "active"
                    );
                }

                item.dataset.id =
                    conversation.id;

                item.innerHTML = `
                    <div class="conversation-avatar">
                        ${avatarHtml}
                    </div>

                    <div class="conversation-content">
                        <div class="conversation-name-row">
                            <span class="conversation-name">
                                ${escapeHtml(name)}
                            </span>
                            <span class="conversation-time">
                                ${formatTime(
                                    conversation.updated_date || conversation.updated_at
                                )}
                            </span>
                        </div>

                        <p class="conversation-last-message">

                            ${escapeHtml(
                                conversation.last_message ||
                                ""
                            )}

                        </p>

                    </div>

                `;


                item.addEventListener(
                    "click",
                    function () {

                        openConversation(
                            conversation.id
                        );

                    }
                );


                conversationList.appendChild(
                    item
                );

            }
        );

    }


    // =========================================================
    // OPEN CONVERSATION
    // =========================================================

    async function openConversation(
        conversationId
    ) {

        activeConversationId =
            Number(conversationId);


        const conversation =
            conversations.find(
                function (c) {

                    return Number(c.id) ===
                        Number(conversationId);

                }
            );


        if (!conversation) {

            console.error(
                "Conversation not found:",
                conversationId
            );

            return;

        }


        renderConversations();

        updateHeader(
            conversation
        );


        await loadMessages(
            conversationId
        );


        socket.emit(
            "join",
            {
                conversation_id:
                    conversationId
            }
        );

    }



    function updateHeader(
        conversation
    ) {

        const otherUser =
            conversation.other_user;

        const name =
            conversation.is_group
                ? (
                    conversation.title ||
                    "Nhóm học tập"
                )
                : otherUser
                    ? (otherUser.name || otherUser.username)
                    : (conversation.title || "Người dùng");

        const hasRealAvatar = Boolean(
            conversation.avatar &&
            !conversation.avatar.includes("default-avatar")
        );
        const initials = getInitials(name);

        if (chatHeaderEmpty) {
            chatHeaderEmpty.classList.add(
                "d-none"
            );
        }

        if (chatHeaderContent) {
            chatHeaderContent.classList.remove(
                "d-none"
            );
        }

        if (chatHeaderName) {
            chatHeaderName.textContent =
                name;
        }

        if (chatHeaderAvatar) {
            if (hasRealAvatar) {
                chatHeaderAvatar.innerHTML = `<img src="${escapeHtml(conversation.avatar)}" class="rounded-circle w-100 h-100" style="object-fit: cover;">`;
            } else {
                chatHeaderAvatar.textContent = initials;
            }
        }

        if (chatHeaderStatus) {
            chatHeaderStatus.textContent =
                conversation.is_group
                    ? "Nhóm học tập"
                    : "Đang trò chuyện";
        }

        if (chatInputContainer) {
            chatInputContainer.classList.remove(
                "d-none"
            );
        }

        if (infoEmpty) {
            infoEmpty.classList.add(
                "d-none"
            );
        }

        if (infoContent) {
            infoContent.classList.remove(
                "d-none"
            );
        }

        if (infoName) {
            infoName.textContent =
                name;
        }

        if (infoAvatar) {
            if (hasRealAvatar) {
                infoAvatar.innerHTML = `<img src="${escapeHtml(conversation.avatar)}" class="rounded-circle w-100 h-100" style="object-fit: cover;">`;
            } else {
                infoAvatar.textContent = initials;
            }
        }

        if (infoRole) {
            infoRole.textContent =
                conversation.is_group
                    ? "Nhóm học tập"
                    : "Thành viên";
        }

    }


    // =========================================================
    // LOAD MESSAGES
    // =========================================================

    async function loadMessages(
        conversationId
    ) {

        try {

            const response =
                await fetch(
                    `/api/chat/${conversationId}/messages`
                );


            if (!response.ok) {

                throw new Error(
                    "Không thể tải tin nhắn."
                );

            }


            const messages =
                await response.json();


            renderMessages(
                messages
            );

        }
        catch (error) {

            console.error(
                "Load messages error:",
                error
            );


            if (messageList) {

                messageList.innerHTML = `
                    <div class="message-empty">

                        <p>
                            Không thể tải tin nhắn.
                        </p>

                    </div>
                `;

            }

        }

    }


    // =========================================================
    // RENDER MESSAGES
    // =========================================================

    function renderMessages(
        messages
    ) {

        if (!messageList) {
            return;
        }


        messageList.innerHTML = "";


        if (!messages.length) {

            messageList.innerHTML = `
                <div class="message-empty">

                    <div class="message-empty-icon">
                        <i class="bi bi-chat-square-text"></i>
                    </div>

                    <h5>
                        Chưa có tin nhắn
                    </h5>

                    <p>
                        Hãy gửi tin nhắn đầu tiên.
                    </p>

                </div>
            `;

            return;

        }


        messages.forEach(
            function (message) {

                appendMessage(
                    message,
                    false
                );

            }
        );


        scrollToBottom();

    }


    // =========================================================
    // APPEND MESSAGE
    // =========================================================

    function appendMessage(
        message,
        scroll = true
    ) {

        if (!messageList) {
            return;
        }


        const mine =
            isCurrentUser(
                message.sender_id
            );


        const row =
            document.createElement(
                "div"
            );


        row.className =
            "message-row";


        if (mine) {

            row.classList.add(
                "mine"
            );

        }


        row.dataset.messageId =
            message.id;

        const senderName = message.sender_name || (mine ? "Bạn" : "Người dùng");
        const senderAvatar = message.sender_avatar;
        const hasSenderAvatar = Boolean(
            senderAvatar &&
            !senderAvatar.includes("default-avatar")
        );

        const avatarHtml = mine
            ? ""
            : hasSenderAvatar
                ? `<img src="${escapeHtml(senderAvatar)}" class="message-avatar rounded-circle" style="object-fit:cover;" title="${escapeHtml(senderName)}">`
                : `<div class="message-avatar" title="${escapeHtml(senderName)}">${escapeHtml(getInitials(senderName))}</div>`;

        row.innerHTML = `
            ${avatarHtml}

            <div class="message-content">

                <div class="message-bubble">

                    ${escapeHtml(
                        message.content ||
                        ""
                    )}

                </div>

                <div class="message-time">

                    ${formatMessageTime(
                        message.created_date
                    )}

                    ${
                        mine
                            ? " ✓✓"
                            : ""
                    }

                </div>

            </div>

        `;


        messageList.appendChild(
            row
        );


        if (scroll) {

            scrollToBottom();

        }

    }


    // =========================================================
    // SEND MESSAGE
    // =========================================================

    if (messageForm) {

        messageForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();


                if (!activeConversationId) {

                    return;

                }


                const content =
                    messageInput
                        ? messageInput.value.trim()
                        : "";


                if (!content) {

                    return;

                }


                socket.emit(
                    "send_message",
                    {
                        conversation_id:
                            activeConversationId,

                        content:
                            content
                    }
                );


                if (messageInput) {

                    messageInput.value =
                        "";

                }

            }
        );

    }


    // =========================================================
    // RECEIVE NEW MESSAGE
    // =========================================================

    socket.on(
        "new_message",
        function (message) {
            loadConversations();

            if (
                Number(message.conversation_id) ===
                Number(activeConversationId)
            ) {
                appendMessage(
                    message
                );

                socket.emit("read_conversation", {
                    conversation_id: activeConversationId
                });
            }
        }
    );

    socket.on(
        "conversation_created",
        function (data) {
            loadConversations();
            if (data && data.conversation_id) {
                socket.emit("join", {
                    conversation_id: data.conversation_id
                });
            }
        }
    );


    // =========================================================
    // MESSAGE EDITED
    // =========================================================

    socket.on(
        "message_edited",
        function (data) {

            const row =
                document.querySelector(
                    `[data-message-id="${data.id}"]`
                );


            if (!row) {
                return;
            }


            const bubble =
                row.querySelector(
                    ".message-bubble"
                );


            if (bubble) {

                bubble.textContent =
                    data.content;

            }

        }
    );


    // =========================================================
    // MESSAGE DELETED
    // =========================================================

    socket.on(
        "message_deleted",
        function (data) {

            const row =
                document.querySelector(
                    `[data-message-id="${data.id}"]`
                );


            if (row) {

                row.remove();

            }

        }
    );


    // =========================================================
    // HELPERS
    // =========================================================

    function scrollToBottom() {

        if (!messageList) {
            return;
        }


        messageList.scrollTop =
            messageList.scrollHeight;

    }


    function getInitials(name) {

        if (!name) {

            return "?";

        }


        const parts =
            name
                .trim()
                .split(/\s+/);


        if (parts.length === 1) {

            return parts[0]
                .substring(0, 2)
                .toUpperCase();

        }


        return (
            parts[0][0] +
            parts[parts.length - 1][0]
        ).toUpperCase();

    }


    function formatTime(
        dateString
    ) {

        if (!dateString) {

            return "";

        }


        const date =
            new Date(
                dateString
            );


        return date.toLocaleTimeString(
            "vi-VN",
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );

    }


    function formatMessageTime(
        dateString
    ) {

        return formatTime(
            dateString
        );

    }


    function escapeHtml(
        value
    ) {

        const div =
            document.createElement(
                "div"
            );


        div.textContent =
            value ?? "";


        return div.innerHTML;

    }


    function isCurrentUser(
        userId
    ) {

        return Number(userId) ===
            Number(window.CURRENT_USER_ID);

    }


    // =========================================================
    // INITIAL LOAD
    // =========================================================

    loadConversations();

});

