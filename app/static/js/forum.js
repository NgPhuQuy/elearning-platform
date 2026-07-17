function showReply(id) {

    let form = document.getElementById(
        "reply-" + id
    );

    form.style.display =
        form.style.display === "block"
        ? "none"
        : "block";
}


/* =========================
   POST REACTION
========================= */

function reactPost(postId, type) {

    fetch(
        `/forum/${postId}/react`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },

            body: `type=${type}`
        }
    )
    .then(res => res.json())
    .then(data => {

        document.getElementById(
            "post-react-count"
        ).innerHTML =
            data.count + " reactions";

        let likeBtn =
            document.querySelector(
                `.reaction-menu[data-post="${postId}"] .like-btn`
            );

        if (!likeBtn)
            return;
        if (data.active) {

            likeBtn.classList.add(
                "active-react"
            );

            likeBtn.dataset.current =
                data.type;

            likeBtn.innerHTML =
                data.icon;

        }
        else {

            likeBtn.classList.remove(
                "active-react"
            );

            likeBtn.dataset.current =
                "";

            likeBtn.innerHTML =
                "👍";
        }
    });
}


document
.querySelectorAll(".reaction-option")
.forEach(btn => {

    btn.addEventListener(
        "click",
        function () {

            let postId =
                this.dataset.post;

            let type =
                this.dataset.type;

            reactPost(
                postId,
                type
            );

        }
    );

});



/* =========================
   COMMENT REACTION
========================= */

function reactComment(commentId, type) {

    fetch(
        `/comment/${commentId}/react`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },

            body: `type=${type}`
        }
    )
    .then(res => res.json())
    .then(data => {

        document.getElementById(
            `comment-react-${commentId}`
        ).innerHTML =
            data.count + " reactions";

        let likeBtn =
            document.querySelector(
                `.comment-reaction-menu[data-comment-id="${commentId}"] .comment-like-btn`
            );

        if (!likeBtn)
            return;

        if (data.active) {

            likeBtn.classList.add(
                "active-react"
            );

            likeBtn.dataset.current =data.type;
            likeBtn.innerHTML =data.icon;

        }
        else {

            likeBtn.classList.remove(
                "active-react"
            );
            likeBtn.dataset.current = "";
            likeBtn.innerHTML ="👍";
        }

    });
}

document
.querySelectorAll(".comment-reaction-option")
.forEach(btn => {

    btn.addEventListener(
        "click",
        function () {

            reactComment(
                this.dataset.comment,
                this.dataset.type
            );

        }
    );

});

document
.querySelectorAll(".comment-reaction-menu")
.forEach(menu => {

    const popup =
        menu.querySelector(
            ".comment-reaction-popup"
        );

    let showTimer;
    let hideTimer;

    menu.addEventListener(
        "mouseenter",
        () => {

            clearTimeout(hideTimer);

            showTimer =
                setTimeout(() => {

                    popup.classList.add(
                        "show-popup"
                    );

                }, 500);
        }
    );

    menu.addEventListener(
        "mouseleave",
        () => {

            clearTimeout(showTimer);

            hideTimer =
                setTimeout(() => {

                    popup.classList.remove(
                        "show-popup"
                    );

                }, 300);
        }
    );

});


/* =========================
   IMAGE MODAL
========================= */

function openImageModal(imageUrl) {

    document
        .getElementById("modalImage")
        .src = imageUrl;

    let modal =
        new bootstrap.Modal(
            document.getElementById(
                "imageModal"
            )
        );

    modal.show();
}

document.querySelectorAll(".reaction-menu")
.forEach(menu => {

    const popup =
        menu.querySelector(".reaction-popup");

    let showTimer;
    let hideTimer;

    menu.addEventListener("mouseenter", () => {

        clearTimeout(hideTimer);

        showTimer = setTimeout(() => {
            popup.classList.add("show-popup");
        }, 500);

    });

    menu.addEventListener("mouseleave", () => {

        clearTimeout(showTimer);

        hideTimer = setTimeout(() => {
            popup.classList.remove("show-popup");
        }, 300);

    });

});

function toggleReaction(btn, postId){

    const current =
        btn.dataset.current;

    if(current){
        reactPost(postId, current);
    }else{
        reactPost(postId, "LIKE");
    }
}

function toggleCommentReaction(btn, commentId){

    const current =
        btn.dataset.current;

    if(current){
        reactComment(commentId, current);
    }else{
        reactComment(commentId, "LIKE");
    }
}

document
.querySelectorAll(".comment-reaction-menu")
.forEach(menu => {

    const popup =
        menu.querySelector(
            ".comment-reaction-popup"
        );

    let showTimer;
    let hideTimer;

    menu.addEventListener(
        "mouseenter",
        () => {

            clearTimeout(hideTimer);

            showTimer = setTimeout(() => {
                popup.classList.add(
                    "show-popup"
                );
            }, 500);

        }
    );

    menu.addEventListener(
        "mouseleave",
        () => {

            clearTimeout(showTimer);

            hideTimer = setTimeout(() => {
                popup.classList.remove(
                    "show-popup"
                );
            }, 300);

        }
    );

});