document.addEventListener('DOMContentLoaded', function () {
  // // Khi bấm nút mở AuthModal, tự chuyển sang tab Đăng nhập/Đăng ký tương ứng
  // var authModalEl = document.getElementById('authModal');
  // if (authModalEl) {
  //   authModalEl.addEventListener('show.bs.modal', function (event) {
  //     var trigger = event.relatedTarget;
  //     if (!trigger) return;
  //     var tab = trigger.getAttribute('data-tab');
  //     if (tab === 'register') {
  //       var tabEl = document.getElementById('register-tab');
  //       if (tabEl) new bootstrap.Tab(tabEl).show();
  //     } else {
  //       var tabEl2 = document.getElementById('login-tab');
  //       if (tabEl2) new bootstrap.Tab(tabEl2).show();
  //     }
  //   });
  // }

  // Kích hoạt mọi tooltip Bootstrap (nếu có)
  var tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach(function (el) { new bootstrap.Tooltip(el); });


  const params = new URLSearchParams(window.location.search);

    if (params.get("login") === "1") {
        const loginBtn = document.querySelector('[data-tab="login"]');

        if (loginBtn) {
            loginBtn.click();
        }
    }
});

document.querySelectorAll('.js-enroll-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
        const url = this.getAttribute('data-enroll-url');
        this.disabled = true;

        fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) {
                if (res.status === 401 || res.redirected) {
                    // chưa đăng nhập, backend đã redirect (nếu login_required trả redirect thay vì JSON)
                    window.location.href = res.url;
                    return null;
                }
                return res.json();
            })
            .then(function (data) {
                if (!data) return;
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert(data.error);
                    btn.disabled = false;
                }
            })
            .catch(function () {
                alert('Hệ thống lỗi, vui lòng thử lại sau!');
                btn.disabled = false;
            });
    });
});
