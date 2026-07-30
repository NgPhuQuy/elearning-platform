// ===== Tab "Thông tin": thêm ô nhập kết quả học tập =====
function addOutcomeInput() {
    const btn = event.target.closest('button');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'outcomes';
    input.className = 'form-control mb-2';
    input.placeholder = 'Kết quả học tập khác...';
    btn.parentElement.insertBefore(input, btn);
}

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('categorySearch');
    const listContainer = document.getElementById('categoryList');

    if (!searchInput || !listContainer) return;

    function reorderCategories() {
        const items = Array.from(listContainer.querySelectorAll('.category-item'));
        items.sort((a, b) => {
            const aChecked = a.querySelector('.category-checkbox').checked;
            const bChecked = b.querySelector('.category-checkbox').checked;
            if (aChecked === bChecked) return 0;
            return aChecked ? -1 : 1;
        });
        items.forEach(item => listContainer.appendChild(item));
    }

    reorderCategories();

    listContainer.addEventListener('change', function (e) {
        if (e.target.classList.contains('category-checkbox')) {
            reorderCategories();
        }
    });

    searchInput.addEventListener('input', function () {
        const keyword = this.value.trim().toLowerCase();
        listContainer.querySelectorAll('.category-item').forEach(item => {
            const name = item.dataset.name;
            item.style.display = name.includes(keyword) ? '' : 'none';
        });
    });
});

// ===== Tab "Cài đặt": switch Miễn phí khóa/mở ô nhập giá =====
document.addEventListener('DOMContentLoaded', function () {
    const freeCheckbox = document.getElementById('freeCourse');
    const priceInput = document.getElementById('priceInput');

    if (!freeCheckbox || !priceInput) return;

    function syncPriceState() {
        if (freeCheckbox.disabled) return; // đã activate -> không cho đổi gì cả
        if (freeCheckbox.checked) {
            priceInput.value = '';
            priceInput.disabled = true;
        } else {
            priceInput.disabled = false;
        }
    }

    syncPriceState();
    freeCheckbox.addEventListener('change', syncPriceState);
});

// ===== Tab "Nội dung": quản lý chương / bài học =====
document.addEventListener('DOMContentLoaded', function () {
    const chapterList = document.getElementById('chapterList');
    const btnAddChapter = document.getElementById('btnAddChapter');
    if (!chapterList || !btnAddChapter) return;

    const editModalEl = document.getElementById('editModal');
    let editModal = null;
    if (editModalEl && window.bootstrap && window.bootstrap.Modal) {
        editModal = new bootstrap.Modal(editModalEl);
    }
    const editModalTitle = document.getElementById('editModalTitle');
    const editModalNameLabel = document.getElementById('editModalNameLabel');
    const editModalName = document.getElementById('editModalName');
    const editModalDescription = document.getElementById('editModalDescription');
    let editTarget = null;

    // ----- Modal chọn video (chỉ đính kèm, không submit ngay) -----
    const uploadVideoModalEl = document.getElementById('uploadVideoModal');
    let uploadVideoModal = null;
    if (uploadVideoModalEl && window.bootstrap && window.bootstrap.Modal) {
        uploadVideoModal = new bootstrap.Modal(uploadVideoModalEl);
    }
    const uploadVideoFileInput = document.getElementById('uploadVideoFileInput');
    const currentVideoNote = document.getElementById('currentVideoNote');
    const currentVideoLink = document.getElementById('currentVideoLink');
    const attachVideoBtn = document.getElementById('attachVideoBtn');
    let currentVideoLessonId = null;

    // ----- Modal chọn tài liệu (chỉ đính kèm, không submit ngay) -----
    const uploadDocModalEl = document.getElementById('uploadDocModal');
    let uploadDocModal = null;
    if (uploadDocModalEl && window.bootstrap && window.bootstrap.Modal) {
        uploadDocModal = new bootstrap.Modal(uploadDocModalEl);
    }
    const uploadDocFileInput = document.getElementById('uploadDocFileInput');
    const attachDocBtn = document.getElementById('attachDocBtn');
    let currentDocLessonId = null;

    const ALLOWED_VIDEO_EXT = ['mp4', 'mov', 'avi', 'mkv', 'webm'];
    const ALLOWED_DOC_EXT = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'];

    function getExt(filename) {
        const parts = filename.split('.');
        return parts.length > 1 ? parts.pop().toLowerCase() : '';
    }

    // Gán file đã chọn (từ modal) vào input ẩn tương ứng trong form chính, dùng DataTransfer
    function attachFileToHiddenInput(hiddenInput, file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        hiddenInput.files = dt.files;
    }

    function showPendingNote(row, text) {
        const note = row.querySelector('.pending-media-note');
        if (note) {
            note.textContent = text;
            note.classList.remove('d-none');
        }
    }

    let chapterCounter = chapterList.querySelectorAll('.chapter-block').length;
    let lessonTempCounter = 0; // đếm id tạm cho bài học MỚI (chưa có id thật trong DB)

    function lessonRowTemplate() {
        lessonTempCounter += 1;
        const tempId = 'new_' + lessonTempCounter;

        const row = document.createElement('div');
        // Dùng cùng cấu trúc "flex-column" như lesson đã có sẵn, vì có thêm dòng pending-media-note bên dưới
        row.className = 'd-flex flex-column gap-1 px-2 py-2 border-bottom lesson-row';
        row.dataset.tempId = tempId; // CHỈ dùng để nối file upload, KHÔNG gán vào data-lesson-id
        row.innerHTML = `
      <div class="d-flex align-items-center gap-2">
        <i class="bi bi-grip-vertical text-muted-ef"></i>
        <i class="bi bi-camera-video text-indigo lesson-type-icon"></i>
        <span class="small flex-grow-1 lesson-name">Bài học mới</span>
        <span class="small text-muted-ef lesson-description d-none"></span>
        <select class="form-select form-select-sm w-auto lesson-type-select" style="max-width:110px;">
          <option value="NONE" selected>Chưa chọn</option>
          <option value="VIDEO">Video</option>
          <option value="DOCUMENT">Doc</option>
        </select>

        <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-upload-video"
                title="Tải video" data-lesson-id="${tempId}" style="display:none;">
          <i class="bi bi-camera-video-fill"></i>
        </button>

        <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-upload-doc"
                title="Tải tài liệu" data-lesson-id="${tempId}" style="display:none;">
          <i class="bi bi-file-earmark-arrow-up-fill"></i>
        </button>

        <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-edit-lesson">
          <i class="bi bi-pencil"></i>
        </button>
        <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-remove-lesson">
          <i class="bi bi-x-lg"></i>
        </button>

        <input type="file" name="video_file_lesson_${tempId}" id="videoFileHidden${tempId}" class="d-none" accept="video/*">
        <input type="file" name="doc_file_lesson_${tempId}" id="docFileHidden${tempId}" class="d-none">
      </div>
      <span class="small text-warning pending-media-note d-none ms-4"></span>
    `;
        return row;
    }

    function chapterBlockTemplate(name) {
        const wrap = document.createElement('div');
        wrap.className = 'border rounded-3 mb-3 chapter-block';
        wrap.innerHTML = `
      <div class="d-flex align-items-center justify-content-between px-3 py-2 bg-slate-50 border-bottom">
        <div>
          <span class="small fw-semibold chapter-name">${name}</span>
          <span class="small text-muted-ef chapter-description d-none"></span>
        </div>
        <div class="d-flex align-items-center gap-3">
          <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-edit-chapter">
            <i class="bi bi-pencil"></i>
          </button>
          <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-remove-chapter">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
      <div class="p-2">
        <div class="lesson-list"></div>
        <button type="button" class="btn btn-sm btn-outline-secondary mt-2 d-flex align-items-center gap-1 btn-add-lesson">
          <i class="bi bi-plus"></i> Thêm bài học
        </button>
      </div>
    `;
        return wrap;
    }

    function updateLessonIcon(row) {
    const type = row.querySelector('.lesson-type-select').value;
    const icon = row.querySelector('.lesson-type-icon');
    let iconClass = 'bi-file-earmark-text';
    if (type === 'VIDEO') iconClass = 'bi-camera-video';
    else if (type === 'NONE') iconClass = 'bi-question-circle';
    icon.className = 'bi ' + iconClass + ' text-indigo lesson-type-icon';

    const uploadVideoBtn = row.querySelector('.btn-upload-video');
    const uploadDocBtn = row.querySelector('.btn-upload-doc');
    if (uploadVideoBtn) uploadVideoBtn.style.display = (type === 'VIDEO') ? '' : 'none';
    if (uploadDocBtn) uploadDocBtn.style.display = (type === 'DOCUMENT') ? '' : 'none';

    const videoViewLink = row.querySelector('.video-view-link');
    const docViewLink = row.querySelector('.doc-view-link');
    if (videoViewLink) videoViewLink.style.display = (type === 'VIDEO') ? '' : 'none';
    if (docViewLink) docViewLink.style.display = (type === 'DOCUMENT') ? '' : 'none';

    // ---- MỚI: xóa file đã chọn của loại KHÔNG còn được dùng ----
    const videoFileInput = row.querySelector('input[id^="videoFileHidden"]');
    const docFileInput = row.querySelector('input[id^="docFileHidden"]');
    const note = row.querySelector('.pending-media-note');

    if (type !== 'VIDEO' && videoFileInput) {
        videoFileInput.value = '';
    }
    if (type !== 'DOCUMENT' && docFileInput) {
        docFileInput.value = '';
    }
    // Nếu đổi type, dòng ghi chú "Đã chọn video/tài liệu: ..." của loại cũ không còn hợp lệ -> xóa
    if (note) {
        const noteText = note.textContent;
        const isVideoNote = noteText.includes('video');
        const isDocNote = noteText.includes('tài liệu');
        if ((type === 'VIDEO' && isDocNote) || (type === 'DOCUMENT' && isVideoNote) || type === 'NONE') {
            note.textContent = '';
            note.classList.add('d-none');
        }
    }
}

    function removeEmptyMsgs(scope) {
        const emptyLesson = scope.querySelector('.empty-lesson-msg');
        if (emptyLesson) emptyLesson.remove();
        const emptyChapter = chapterList.querySelector('.empty-chapter-msg');
        if (emptyChapter) emptyChapter.remove();
    }

    btnAddChapter.addEventListener('click', function () {
        chapterCounter += 1;
        removeEmptyMsgs(chapterList);
        const block = chapterBlockTemplate('Chương ' + chapterCounter);
        chapterList.appendChild(block);
    });

    chapterList.addEventListener('click', function (e) {
        const addLessonBtn = e.target.closest('.btn-add-lesson');
        if (addLessonBtn) {
            const chapterBlock = addLessonBtn.closest('.chapter-block');
            const lessonList = chapterBlock.querySelector('.lesson-list');
            removeEmptyMsgs(lessonList);
            lessonList.appendChild(lessonRowTemplate());
            return;
        }

        const removeChapterBtn = e.target.closest('.btn-remove-chapter');
        if (removeChapterBtn) {
            removeChapterBtn.closest('.chapter-block').remove();
            return;
        }

        const removeLessonBtn = e.target.closest('.btn-remove-lesson');
        if (removeLessonBtn) {
            removeLessonBtn.closest('.lesson-row').remove();
            return;
        }

        const editChapterBtn = e.target.closest('.btn-edit-chapter');
        if (editChapterBtn && editModal) {
            const chapterBlock = editChapterBtn.closest('.chapter-block');
            editTarget = {el: chapterBlock, type: 'chapter'};
            editModalTitle.textContent = 'Chỉnh sửa chương';
            editModalNameLabel.textContent = 'Tên chương';
            editModalName.value = chapterBlock.querySelector('.chapter-name').textContent.trim();
            editModalDescription.value = chapterBlock.querySelector('.chapter-description').textContent.trim();
            editModal.show();
            return;
        }

        const editLessonBtn = e.target.closest('.btn-edit-lesson');
        if (editLessonBtn && editModal) {
            const row = editLessonBtn.closest('.lesson-row');
            editTarget = {el: row, type: 'lesson'};
            editModalTitle.textContent = 'Chỉnh sửa bài học';
            editModalNameLabel.textContent = 'Tên bài học';
            editModalName.value = row.querySelector('.lesson-name').textContent.trim();
            editModalDescription.value = row.querySelector('.lesson-description').textContent.trim();
            editModal.show();
            return;
        }

        // ----- Bấm nút "Tải video" trên 1 bài học -> chỉ mở modal chọn file, chưa gửi -----
        const uploadVideoBtn = e.target.closest('.btn-upload-video');
        if (uploadVideoBtn && uploadVideoModal) {
            currentVideoLessonId = uploadVideoBtn.dataset.lessonId;
            const currentVideo = uploadVideoBtn.dataset.currentVideo || '';
            if (uploadVideoFileInput) uploadVideoFileInput.value = '';
            if (currentVideo && currentVideoNote && currentVideoLink) {
                currentVideoLink.href = currentVideo;
                currentVideoNote.style.display = '';
            } else if (currentVideoNote) {
                currentVideoNote.style.display = 'none';
            }
            uploadVideoModal.show();
            return;
        }

        // ----- Bấm nút "Tải tài liệu" trên 1 bài học -> chỉ mở modal chọn file, chưa gửi -----
        const uploadDocBtn = e.target.closest('.btn-upload-doc');
        if (uploadDocBtn && uploadDocModal) {
            currentDocLessonId = uploadDocBtn.dataset.lessonId;
            if (uploadDocFileInput) uploadDocFileInput.value = '';
            uploadDocModal.show();
        }
    });

    // ----- Nút "Đính kèm" trong modal video: gán file vào input ẩn, KHÔNG submit -----
    if (attachVideoBtn) {
        attachVideoBtn.addEventListener('click', function () {
            const file = uploadVideoFileInput.files && uploadVideoFileInput.files[0];
            if (!file) {
                alert('Vui lòng chọn file video.');
                return;
            }
            const ext = getExt(file.name);
            if (!ALLOWED_VIDEO_EXT.includes(ext)) {
                alert('File "' + file.name + '" không phải file video hợp lệ.\nChỉ chấp nhận: ' + ALLOWED_VIDEO_EXT.join(', '));
                return;
            }
            const hiddenInput = document.getElementById('videoFileHidden' + currentVideoLessonId);
            if (hiddenInput) {
                attachFileToHiddenInput(hiddenInput, file);
                showPendingNote(hiddenInput.closest('.lesson-row'), 'Đã chọn video: ' + file.name + ' (sẽ lưu khi bấm "Lưu thay đổi")');
            }
            attachVideoBtn.blur();
            if (uploadVideoModal) uploadVideoModal.hide();
        });
    }

    // ----- Nút "Đính kèm" trong modal tài liệu: gán file vào input ẩn, KHÔNG submit -----
    if (attachDocBtn) {
        attachDocBtn.addEventListener('click', function () {
            const file = uploadDocFileInput.files && uploadDocFileInput.files[0];
            if (!file) {
                alert('Vui lòng chọn file tài liệu.');
                return;
            }
            const ext = getExt(file.name);
            if (!ALLOWED_DOC_EXT.includes(ext)) {
                alert('File "' + file.name + '" không phải file tài liệu hợp lệ.\nChỉ chấp nhận: ' + ALLOWED_DOC_EXT.join(', '));
                return;
            }
            const hiddenInput = document.getElementById('docFileHidden' + currentDocLessonId);
            if (hiddenInput) {
                attachFileToHiddenInput(hiddenInput, file);
                showPendingNote(hiddenInput.closest('.lesson-row'), 'Đã chọn tài liệu: ' + file.name + ' (sẽ lưu khi bấm "Lưu thay đổi")');
            }
            attachDocBtn.blur();
            if (uploadDocModal) uploadDocModal.hide();
        });
    }

    chapterList.addEventListener('change', function (e) {
        if (e.target.classList.contains('lesson-type-select')) {
            updateLessonIcon(e.target.closest('.lesson-row'));
        }
    });

    const editModalSaveBtn = document.getElementById('editModalSave');
    if (editModalSaveBtn) {
        editModalSaveBtn.addEventListener('click', function () {
            if (!editTarget) return;
            const name = editModalName.value.trim();
            const description = editModalDescription.value.trim();
            if (!name) {
                editModalName.focus();
                return;
            }
            if (editTarget.type === 'chapter') {
                editTarget.el.querySelector('.chapter-name').textContent = name;
                editTarget.el.querySelector('.chapter-description').textContent = description;
            } else {
                editTarget.el.querySelector('.lesson-name').textContent = name;
                editTarget.el.querySelector('.lesson-description').textContent = description;
            }
            if (editModal) editModal.hide();
            editTarget = null;
        });
    }

    const courseForm = chapterList.closest('form');
    const chaptersDataInput = document.getElementById('chaptersDataInput');
    if (courseForm && chaptersDataInput) {
        courseForm.addEventListener('submit', function () {
            const chaptersData = [];
            chapterList.querySelectorAll('.chapter-block').forEach(function (chapterBlock) {
                const lessons = [];
                chapterBlock.querySelectorAll('.lesson-row').forEach(function (row) {
                    lessons.push({
                        id: row.dataset.lessonId || null,
                        temp_id: row.dataset.tempId || null, // dùng để nối file upload với lesson mới vừa tạo
                        name: row.querySelector('.lesson-name').textContent.trim(),
                        description: row.querySelector('.lesson-description').textContent.trim(),
                        type: row.querySelector('.lesson-type-select').value
                    });
                });
                chaptersData.push({
                    id: chapterBlock.dataset.chapterId || null,
                    name: chapterBlock.querySelector('.chapter-name').textContent.trim(),
                    description: chapterBlock.querySelector('.chapter-description').textContent.trim(),
                    lessons: lessons
                });
            });
            chaptersDataInput.value = JSON.stringify(chaptersData);
        });
    }
});

// ===== Preview ảnh khi chọn file (tạo mới hoặc sửa khóa học) =====
document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('imageInput');
    const previewWrap = document.getElementById('imagePreviewWrap');
    const previewImg = document.getElementById('imagePreview');

    if (!imageInput || !previewWrap || !previewImg) return;

    imageInput.addEventListener('change', function () {
        const file = this.files && this.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewWrap.style.display = '';
        };
        reader.readAsDataURL(file);
    });
});

// ===== Ẩn/hiện nút Lưu thay đổi / Công khai khóa học theo tab đang active =====
document.addEventListener('DOMContentLoaded', function () {
    const btnSaveOnly = document.getElementById('btnSaveOnly');
    const btnPublish = document.getElementById('btnPublish');
    if (!btnSaveOnly || !btnPublish) return; // khóa học đã activate hoặc đang tạo mới -> không có 2 nút này

    document.querySelectorAll('.nav-ef-tabs button[data-bs-toggle="tab"]').forEach(function (tabBtn) {
        tabBtn.addEventListener('shown.bs.tab', function (e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target === '#cc-settings') {
                btnSaveOnly.classList.add('d-none');
                btnPublish.classList.remove('d-none');
            } else {
                btnSaveOnly.classList.remove('d-none');
                btnPublish.classList.add('d-none');
            }
        });
    });
});

// ===== Xóa chương / bài học bằng AJAX (thay cho <form> con đã bị xóa khỏi HTML) =====
document.addEventListener('click', async (e) => {
    // --- Xóa chương ---
    const delChapterBtn = e.target.closest('.btn-delete-chapter');
    if (delChapterBtn) {
        if (!confirm('Xóa chương này và toàn bộ bài học bên trong?')) return;

        const url = delChapterBtn.dataset.deleteUrl;
        const courseId = delChapterBtn.dataset.courseId;

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ course_id: courseId })
            });
            if (!res.ok) throw new Error('Request failed: ' + res.status);

            // Xóa khối chương khỏi giao diện, không reload trang
            delChapterBtn.closest('.chapter-block').remove();
        } catch (err) {
            console.error(err);
            alert('Xóa chương thất bại, thử lại.');
        }
        return;
    }

    // --- Xóa bài học ---
    const delLessonBtn = e.target.closest('.btn-delete-lesson');
    if (delLessonBtn) {
        if (!confirm('Xóa bài học này?')) return;

        const url = delLessonBtn.dataset.deleteUrl;
        const courseId = delLessonBtn.dataset.courseId;

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ course_id: courseId })
            });
            if (!res.ok) throw new Error('Request failed: ' + res.status);

            delLessonBtn.closest('.lesson-row').remove();
        } catch (err) {
            console.error(err);
            alert('Xóa bài học thất bại, thử lại.');
        }
        return;
    }
});