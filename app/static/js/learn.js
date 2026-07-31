(function () {
    var video = document.getElementById("ef-lesson-video");
    if (!video) return;

    var statusBadge = document.getElementById("ef-lesson-status");
    var courseId = video.dataset.courseId;
    var lessonId = video.dataset.lessonId;
    var alreadyDone = video.dataset.completed === "true";

    if (alreadyDone) return;

    var sent = false;

    function markComplete() {
        if (sent) return;
        sent = true;

        fetch(`/learn/${courseId}/lessons/${lessonId}/complete`, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    if (statusBadge) {
                        statusBadge.classList.remove("bg-secondary");
                        statusBadge.classList.add("bg-success");
                        statusBadge.innerHTML = '<i class="bi bi-check-circle-fill"></i> Đã hoàn thành';
                    }
                    location.reload();
                } else if (data.error) {
                    sent = false;
                    alert(data.error);
                }
            })
            .catch(() => {
                sent = false;
            });
    }

    video.addEventListener("ended", markComplete);

    // Bắt cả trường hợp tua tới gần cuối mà không bắn "ended"
    video.addEventListener("timeupdate", function () {
        if (video.duration && video.currentTime >= video.duration - 0.5) {
            markComplete();
        }
    });
})();