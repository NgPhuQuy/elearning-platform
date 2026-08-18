document.addEventListener('DOMContentLoaded', function () {
    const questionList = document.getElementById('questionList');
    const btnAddQuestion = document.getElementById('btnAddQuestion');
    const questionsForm = document.getElementById('questionsForm');
    const questionsDataInput = document.getElementById('questionsDataInput');

    const passScore = document.getElementById('passScore');
    const passScoreInput = document.getElementById('passScoreInput');
    const passScoreValue = document.getElementById('passScoreValue');
    const footerPassScore = document.getElementById('footerPassScore');
    const questionCount = document.getElementById('questionCount');

    if (!questionList || !btnAddQuestion) return;

    const MAX_ANSWERS = 4;
    const MIN_ANSWERS = 2;

    let questionTempCounter = 0;
    let answerTempCounter = 0;


    // =========================================================
    // SCORE
    // =========================================================

    function updatePassScore() {
        if (!passScore) return;

        const value = parseInt(passScore.value, 10) || 0;

        if (passScoreValue) {
            passScoreValue.textContent = value;
        }

        if (footerPassScore) {
            footerPassScore.textContent = value;
        }

        if (passScoreInput) {
            passScoreInput.value = value;
        }
    }

    if (passScore) {
        passScore.addEventListener('input', updatePassScore);
        updatePassScore();
    }


    // =========================================================
    // QUESTION COUNT
    // =========================================================

    function updateQuestionCount() {
        if (!questionCount) return;

        const blocks = questionList.querySelectorAll('.question-block');
        questionCount.textContent = blocks.length;

        updateQuestionNumbers();
    }


    function updateQuestionNumbers() {
        const blocks = questionList.querySelectorAll('.question-block');

        blocks.forEach(function (block, index) {
            const number = block.querySelector('.question-number');

            if (number) {
                number.textContent = index + 1;
            }

            const questionInput = block.querySelector('.question-content');

            if (questionInput) {
                questionInput.placeholder =
                    `Nhập câu hỏi số ${index + 1}...`;
            }
        });
    }


    // =========================================================
    // ANSWER TEMPLATE
    // =========================================================

    function getAnswerLabel(index) {
        return ['A', 'B', 'C', 'D'][index] || '';
    }


    function answerRowTemplate() {
        answerTempCounter += 1;

        const row = document.createElement('div');

        row.className = 'answer-row';
        row.dataset.tempId = 'newa_' + answerTempCounter;

        row.innerHTML = `
            <input
                type="radio"
                class="answer-correct-radio"
            >

            <span class="answer-label"></span>

            <input
                type="text"
                class="answer-content"
                placeholder=""
            >

            <button
                type="button"
                class="btn-remove-answer"
                title="Xóa đáp án"
            >
                <i class="bi bi-x-lg"></i>
            </button>
        `;

        return row;
    }


    // =========================================================
    // UPDATE ANSWER LABELS
    // =========================================================

    function updateAnswerLabels(questionBlock) {
        const rows = questionBlock.querySelectorAll('.answer-row');

        rows.forEach(function (row, index) {
            const label = row.querySelector('.answer-label');
            const input = row.querySelector('.answer-content');

            const answerLabel = getAnswerLabel(index);

            if (label) {
                label.textContent = answerLabel;
            }

            if (input) {
                input.placeholder = `Đáp án ${answerLabel}...`;
            }
        });
    }


    // =========================================================
    // ADD ANSWER BUTTON
    // =========================================================

    function updateAddAnswerButtonState(questionBlock) {
        const answerList = questionBlock.querySelector('.answer-list');
        const addBtn = questionBlock.querySelector('.btn-add-answer');

        if (!answerList || !addBtn) return;

        const count = answerList.querySelectorAll('.answer-row').length;

        if (count >= MAX_ANSWERS) {
            addBtn.disabled = true;
            addBtn.classList.add('d-none');
        } else {
            addBtn.disabled = false;
            addBtn.classList.remove('d-none');
        }

        updateAnswerLabels(questionBlock);
    }


    // =========================================================
    // QUESTION TEMPLATE
    // =========================================================

    function questionBlockTemplate() {
        questionTempCounter += 1;

        const block = document.createElement('div');

        block.className = 'question-block';

        block.dataset.tempId = 'newq_' + questionTempCounter;

        block.innerHTML = `
            <div class="question-header">

                <span class="question-number">
                    1
                </span>

                <textarea
                    class="question-content"
                    rows="1"
                    placeholder="Nhập câu hỏi..."
                ></textarea>

                <button
                    type="button"
                    class="btn-remove-question"
                    title="Xóa câu hỏi"
                >
                    <i class="bi bi-trash"></i>
                </button>

            </div>

            <div class="question-body">

                <div class="answer-list"></div>

                <button
                    type="button"
                    class="btn-add-answer"
                >
                    <i class="bi bi-plus-lg"></i>
                    Thêm đáp án
                </button>

            </div>
        `;

        return block;
    }


    // =========================================================
    // INIT EXISTING QUESTIONS
    // =========================================================

    questionList
        .querySelectorAll('.question-block')
        .forEach(function (block) {

            const answerList =
                block.querySelector('.answer-list');

            if (!answerList) return;

            updateAnswerLabels(block);
            updateAddAnswerButtonState(block);
        });

    updateQuestionCount();


    // =========================================================
    // ADD QUESTION
    // =========================================================

    btnAddQuestion.addEventListener('click', function () {

        const block = questionBlockTemplate();

        questionList.appendChild(block);

        const answerList =
            block.querySelector('.answer-list');

        // Mỗi câu hỏi mới bắt đầu bằng 2 đáp án
        answerList.appendChild(answerRowTemplate());
        answerList.appendChild(answerRowTemplate());

        updateAnswerLabels(block);
        updateAddAnswerButtonState(block);
        updateQuestionCount();

        // Focus vào câu hỏi mới
        const questionInput =
            block.querySelector('.question-content');

        if (questionInput) {
            questionInput.focus();
        }
    });


    // =========================================================
    // CLICK EVENTS
    // =========================================================

    questionList.addEventListener('click', function (e) {

        // -----------------------------------------------------
        // REMOVE QUESTION
        // -----------------------------------------------------

        const removeQuestion =
            e.target.closest('.btn-remove-question');

        if (removeQuestion) {

            const block =
                removeQuestion.closest('.question-block');

            if (block) {
                block.remove();
            }

            updateQuestionCount();

            return;
        }


        // -----------------------------------------------------
        // ADD ANSWER
        // -----------------------------------------------------

        const addAnswer =
            e.target.closest('.btn-add-answer');

        if (addAnswer) {

            const questionBlock =
                addAnswer.closest('.question-block');

            if (!questionBlock) return;

            const answerList =
                questionBlock.querySelector('.answer-list');

            if (!answerList) return;

            const currentCount =
                answerList.querySelectorAll('.answer-row').length;

            if (currentCount >= MAX_ANSWERS) {
                updateAddAnswerButtonState(questionBlock);
                return;
            }

            answerList.appendChild(answerRowTemplate());

            updateAddAnswerButtonState(questionBlock);

            return;
        }


        // -----------------------------------------------------
        // REMOVE ANSWER
        // -----------------------------------------------------

        const removeAnswer =
            e.target.closest('.btn-remove-answer');

        if (removeAnswer) {

            const questionBlock =
                removeAnswer.closest('.question-block');

            const answerList =
                questionBlock?.querySelector('.answer-list');

            const answerRow =
                removeAnswer.closest('.answer-row');

            if (!questionBlock || !answerList || !answerRow) {
                return;
            }

            const currentCount =
                answerList.querySelectorAll('.answer-row').length;

            // Không cho xóa nếu đang còn đúng 2 đáp án
            if (currentCount <= MIN_ANSWERS) {
                return;
            }

            answerRow.remove();

            updateAddAnswerButtonState(questionBlock);

            return;
        }
    });


    // =========================================================
    // CORRECT ANSWER
    // =========================================================

    questionList.addEventListener('change', function (e) {

        const clickedRadio =
            e.target.closest('.answer-correct-radio');

        if (!clickedRadio) return;

        const questionBlock =
            clickedRadio.closest('.question-block');

        if (!questionBlock) return;

        questionBlock
            .querySelectorAll('.answer-correct-radio')
            .forEach(function (radio) {

                if (radio !== clickedRadio) {
                    radio.checked = false;
                }

            });

        clickedRadio.checked = true;
    });


    // =========================================================
    // SUBMIT
    // =========================================================

    if (questionsForm && questionsDataInput) {

        questionsForm.addEventListener('submit', function () {

            const questionsData = [];

            questionList
                .querySelectorAll('.question-block')
                .forEach(function (block) {

                    const questionContent =
                        block
                            .querySelector('.question-content')
                            ?.value
                            .trim() || '';

                    const answers = [];

                    block
                        .querySelectorAll('.answer-row')
                        .forEach(function (row) {

                            const contentInput =
                                row.querySelector('.answer-content');

                            const correctRadio =
                                row.querySelector('.answer-correct-radio');

                            answers.push({
                                id: row.dataset.answerId || null,

                                content:
                                    contentInput
                                        ? contentInput.value.trim()
                                        : '',

                                is_correct:
                                    correctRadio
                                        ? correctRadio.checked
                                        : false
                            });
                        });

                    questionsData.push({

                        id:
                            block.dataset.questionId ||
                            null,

                        content:
                            questionContent,

                        answers:
                            answers
                    });
                });


            // Gửi dữ liệu câu hỏi cho backend
            questionsDataInput.value =
                JSON.stringify(questionsData);


            // Đồng thời gửi điểm đạt
            updatePassScore();
        });
    }
});