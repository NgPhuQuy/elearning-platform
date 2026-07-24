document.addEventListener('DOMContentLoaded', function () {
    const registerForm = document.getElementById('registerForm');
    const agreeTerms = document.getElementById('agreeTerms');
    const registerBtn = document.getElementById('registerBtn');
    const registerSpinner = document.getElementById('registerSpinner');
    const serverErrorBox = document.getElementById('registerServerError');

    const password = document.getElementById('register_password');
    const confirmPassword = document.getElementById('register_confirm');

    // 1. Mở / Khóa nút Đăng ký theo checkbox Điều khoản
    if (agreeTerms && registerBtn) {
        agreeTerms.addEventListener('change', function () {
            registerBtn.disabled = !this.checked;
        });
    }

    // 2. Kiểm tra Mật khẩu trùng khớp (xanh/đỏ)
    function checkPasswordMatch() {
        const passVal = password.value;
        const confirmVal = confirmPassword.value;

        if (confirmVal === '') {
            confirmPassword.setCustomValidity('');
            confirmPassword.classList.remove('is-invalid', 'is-valid');
            return;
        }

        if (passVal === '' || passVal !== confirmVal) {
            confirmPassword.setCustomValidity('Mật khẩu không khớp!');
            confirmPassword.classList.add('is-invalid');
            confirmPassword.classList.remove('is-valid');
        } else {
            confirmPassword.setCustomValidity('');
            confirmPassword.classList.remove('is-invalid');
            confirmPassword.classList.add('is-valid');
        }
    }

    if (password && confirmPassword) {
        password.addEventListener('input', checkPasswordMatch);
        confirmPassword.addEventListener('input', checkPasswordMatch);
    }

    function showServerError(message) {
        serverErrorBox.textContent = message;
        serverErrorBox.classList.remove('d-none');
    }

    function hideServerError() {
        serverErrorBox.classList.add('d-none');
        serverErrorBox.textContent = '';
    }

    function setLoading(isLoading) {
        registerBtn.disabled = isLoading || !agreeTerms.checked;
        registerBtn.querySelector('.btn-text').classList.toggle('d-none', isLoading);
        registerSpinner.classList.toggle('d-none', !isLoading);
    }

    // 3. Xử lý submit bằng AJAX
    if (registerForm) {
        registerForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            hideServerError();
            checkPasswordMatch();

            if (!registerForm.checkValidity()) {
                registerForm.classList.add('was-validated');
                return;
            }

            setLoading(true);

            try {
                const formData = new FormData(registerForm);
                const response = await fetch(registerForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                const data = await response.json();

                if (data.success) {
                    window.location.href = data.redirect || '/';
                } else {
                    showServerError(data.error || 'Đã có lỗi xảy ra, vui lòng thử lại.');
                }
            } catch (err) {
                showServerError('Không thể kết nối tới máy chủ. Vui lòng kiểm tra mạng và thử lại.');
            } finally {
                setLoading(false);
            }
        }, false);
    }
});

document.querySelectorAll('[data-tab]').forEach(function (btn) {
    btn.addEventListener('click', function () {
        const tabName = this.getAttribute('data-tab');
        const tabTrigger = document.getElementById(tabName + '-tab');
        if (tabTrigger) {
            const tab = new bootstrap.Tab(tabTrigger);
            tab.show();
        }
    });
});