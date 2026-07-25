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

  if (!searchInput || !listContainer) return; // trang không có phần chọn danh mục thì bỏ qua

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

// ===== Tab "Nội dung": quản lý chương / bài học (chỉ chạy khi đang sửa khóa học đã có) =====
document.addEventListener('DOMContentLoaded', function () {
  const chapterList = document.getElementById('chapterList');
  const btnAddChapter = document.getElementById('btnAddChapter');
  if (!chapterList || !btnAddChapter) return; // an toàn: không có thì thôi, không phá phần khác

  const editModalEl = document.getElementById('editModal');
  let editModal = null;
  // Khởi tạo modal an toàn - không phụ thuộc getOrCreateInstance (chỉ có ở Bootstrap 5.2+)
  if (editModalEl && window.bootstrap && window.bootstrap.Modal) {
    editModal = new bootstrap.Modal(editModalEl);
  }
  const editModalTitle = document.getElementById('editModalTitle');
  const editModalNameLabel = document.getElementById('editModalNameLabel');
  const editModalName = document.getElementById('editModalName');
  const editModalDescription = document.getElementById('editModalDescription');
  let editTarget = null; // { el, type: 'chapter' | 'lesson' }

  let chapterCounter = chapterList.querySelectorAll('.chapter-block').length;

  function lessonRowTemplate() {
    const row = document.createElement('div');
    row.className = 'd-flex align-items-center gap-2 px-2 py-2 border-bottom lesson-row';
    row.innerHTML = `
      <i class="bi bi-grip-vertical text-muted-ef"></i>
      <i class="bi bi-camera-video text-indigo lesson-type-icon"></i>
      <span class="small flex-grow-1 lesson-name">Bài học mới</span>
      <span class="small text-muted-ef lesson-description d-none"></span>
      <select class="form-select form-select-sm w-auto lesson-type-select" style="max-width:110px;">
        <option value="VIDEO" selected>Video</option>
        <option value="DOCUMENT">Doc</option>
      </select>
      <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-edit-lesson">
        <i class="bi bi-pencil"></i>
      </button>
      <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-remove-lesson">
        <i class="bi bi-x-lg"></i>
      </button>
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
    icon.className = 'bi ' + (type === 'VIDEO' ? 'bi-camera-video' : 'bi-file-earmark-text') + ' text-indigo lesson-type-icon';
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
      editTarget = { el: chapterBlock, type: 'chapter' };
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
      editTarget = { el: row, type: 'lesson' };
      editModalTitle.textContent = 'Chỉnh sửa bài học';
      editModalNameLabel.textContent = 'Tên bài học';
      editModalName.value = row.querySelector('.lesson-name').textContent.trim();
      editModalDescription.value = row.querySelector('.lesson-description').textContent.trim();
      editModal.show();
      return;
    }
  });

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
});