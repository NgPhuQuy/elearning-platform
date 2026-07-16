function showReply(id) {

    let form = document.getElementById(
        "reply-" + id
    );

    if (form.style.display === "none") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}



document.querySelectorAll(".react-form")
.forEach(form => {

    form.addEventListener(
        "submit",
        function (e) {

            e.preventDefault();

            let postId =
                this.dataset.post;

            let type =
                this.querySelector(
                    "input[name='type']"
                ).value;

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

                document
                    .getElementById(
                        "post-react-count"
                    )
                    .innerHTML =
                    data.count + " reactions";


                document
                    .querySelectorAll(
                        `.react-form[data-post="${postId}"] .react-btn`
                    )
                    .forEach(btn =>
                        btn.classList.remove(
                            "active-react"
                        )
                    );


                if (data.active) {
                    this.querySelector(
                        ".react-btn"
                    ).classList.add(
                        "active-react"
                    );
                }

            });

        }
    );

});



document.querySelectorAll(".comment-react-form").forEach(form => {

    form.addEventListener("submit",function (e) {

            e.preventDefault();

            let commentId =this.dataset.commentId;

            let type =this.querySelector("input[name='type']").value;

            fetch(`/comment/${commentId}/react`,
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

                document.getElementById(`comment-react-${data.comment_id}`)
                 .innerHTML =data.count +" reactions";


                document.querySelectorAll(`.comment-react-form[data-comment-id="${commentId}"] .react-btn-small`)
                    .forEach(btn =>
                        btn.classList.remove(
                            "active-react"
                        )
                    );


                if (data.active) {
                    this.querySelector(
                        ".react-btn-small"
                    ).classList.add(
                        "active-react"
                    );
                }

            });

        }
    );

});

function openImageModal(imageUrl){

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