document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("enroll-btn");
  if (!btn) return;

  btn.addEventListener("click", function () {
    const courseId = btn.dataset.courseId;
    btn.disabled = true;

    fetch(`/courses/${courseId}/enroll`, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((res) => {
        const contentType = res.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
          window.location.href = "/?login=1";
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (!data) return;
        if (data.success) {
          window.location.href = data.redirect;
        } else {
          alert(data.error || "Đăng ký thất bại, vui lòng thử lại!");
          btn.disabled = false;
        }
      })
      .catch(() => {
        alert("Hệ thống lỗi, vui lòng thử lại sau!");
        btn.disabled = false;
      });
  });
});