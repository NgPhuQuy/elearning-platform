document.addEventListener('DOMContentLoaded', function () {
    const questionList = document.getElementById('questionList');
    const btnAddQuestion = document.getElementById('btnAddQuestion');
    const questionsForm = document.getElementById('questionsForm');
    const questionsDataInput = document.getElementById('questionsDataInput');
    if (!questionList || !btnAddQuestion) return;

    const MAX_ANSWERS = 4;

    let questionTempCounter = 0;
    let answerTempCounter = 0;

    function answerRowTemplate() {
        answerTempCounter += 1;
        const row = document.createElement('div');
        row.className = 'd-flex align-items-center gap-2 answer-row';
        row.dataset.tempId = 'newa_' + answerTempCounter;
        row.innerHTML = `
      <input type="radio" class="answer-correct-radio">
      <input type="text" class="form-control form-control-sm answer-content" placeholder="Nội dung đáp án">
      <button type="button" class="btn btn-sm p-0 border-0 text-muted-ef btn-remove-answer">
        <i class="bi bi-x"></i>
      </button>
    `;
        return row;
    }

    function questionBlockTemplate() {
        questionTempCounter += 1;
        const block = document.createElement('div');
        block.className = 'border rounded-3 p-3 question-block';
        block.dataset.tempId = 'newq_' + questionTempCounter;
        block.innerHTML = `
      <div class="d-flex align-items-start gap-2 mb-2">
        <span class="fw-semibold small mt-2">Câu hỏi</span>
        <textarea class="form-control question-content" rows="2" placeholder="Nhập nội dung câu hỏi"></textarea>
        <button type="button" class="btn btn-sm p-0 border-0 text-danger btn-remove-question mt-2">
          <i class="bi bi-trash"></i>
        </button>
      </div>
      <div class="answer-list ms-4 d-flex flex-column gap-2"></div>
      <button type="button" class="btn btn-sm btn-outline-secondary mt-2 ms-4 btn-add-answer">
        <i class="bi bi-plus"></i> Thêm đáp án
      </button>
    `;
        return block;
    }

    // Ẩn/hiện nút "Thêm đáp án" của 1 câu hỏi tùy theo số đáp án hiện có
    function updateAddAnswerButtonState(questionBlock) {
        const answerList = questionBlock.querySelector('.answer-list');
        const addBtn = questionBlock.querySelector('.btn-add-answer');
        if (!answerList || !addBtn) return;
        const count = answerList.querySelectorAll('.answer-row').length;
        addBtn.disabled = count >= MAX_ANSWERS;
        addBtn.classList.toggle('d-none', count >= MAX_ANSWERS);
    }

    // Áp dụng giới hạn cho các câu hỏi đã render sẵn từ server khi load trang
    questionList.querySelectorAll('.question-block').forEach(updateAddAnswerButtonState);

    btnAddQuestion.addEventListener('click', function () {
        const block = questionBlockTemplate();
        questionList.appendChild(block);
        const answerList = block.querySelector('.answer-list');
        answerList.appendChild(answerRowTemplate());
        answerList.appendChild(answerRowTemplate());
        updateAddAnswerButtonState(block);
    });

    questionList.addEventListener('click', function (e) {
        const removeQ = e.target.closest('.btn-remove-question');
        if (removeQ) {
            removeQ.closest('.question-block').remove();
            return;
        }

        const addA = e.target.closest('.btn-add-answer');
        if (addA) {
            const questionBlock = addA.closest('.question-block');
            const answerList = questionBlock.querySelector('.answer-list');
            const currentCount = answerList.querySelectorAll('.answer-row').length;
            if (currentCount >= MAX_ANSWERS) {
                updateAddAnswerButtonState(questionBlock);
                return;
            }
            answerList.appendChild(answerRowTemplate());
            updateAddAnswerButtonState(questionBlock);
            return;
        }

        const removeA = e.target.closest('.btn-remove-answer');
        if (removeA) {
            const questionBlock = removeA.closest('.question-block');
            removeA.closest('.answer-row').remove();
            updateAddAnswerButtonState(questionBlock);
            return;
        }

        // ----- Chọn đáp án đúng: đảm bảo chỉ 1 radio được chọn trong cùng 1 câu hỏi -----
        const clickedRadio = e.target.closest('.answer-correct-radio');
        if (clickedRadio) {
            const questionBlock = clickedRadio.closest('.question-block');
            questionBlock.querySelectorAll('.answer-correct-radio').forEach(function (radio) {
                if (radio !== clickedRadio) radio.checked = false;
            });
            clickedRadio.checked = true;
        }
    });

    if (questionsForm && questionsDataInput) {
        questionsForm.addEventListener('submit', function () {
            const questionsData = [];
            questionList.querySelectorAll('.question-block').forEach(function (block) {
                const answers = [];
                block.querySelectorAll('.answer-row').forEach(function (row) {
                    answers.push({
                        id: row.dataset.answerId || null,
                        content: row.querySelector('.answer-content').value.trim(),
                        is_correct: row.querySelector('.answer-correct-radio').checked
                    });
                });
                questionsData.push({
                    id: block.dataset.questionId || null,
                    content: block.querySelector('.question-content').value.trim(),
                    answers: answers
                });
            });
            questionsDataInput.value = JSON.stringify(questionsData);
        });
    }
});