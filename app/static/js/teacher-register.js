(function () {
  const steps = Array.from(document.querySelectorAll('.reg-step'));
  const indicators = Array.from(document.querySelectorAll('[data-step-indicator]'));
  const btnBack = document.getElementById('btnBack');
  const btnNext = document.getElementById('btnNext');
  const btnSubmit = document.getElementById('btnSubmit');
  const stepCounter = document.getElementById('stepCounter');
  const total = steps.length;
  let current = 1;

  function showStep(n) {
    steps.forEach(s => s.classList.toggle('d-none', Number(s.dataset.step) !== n));

    indicators.forEach(ind => {
      const num = Number(ind.dataset.stepIndicator);
      const circle = ind.querySelector('.step-circle');
      const label = ind.querySelector('.step-label');
      circle.classList.remove('bg-primary', 'bg-success', 'bg-body-secondary', 'text-white', 'text-muted-ef');
      label.classList.remove('text-indigo', 'text-muted-ef');
      if (num < n) {
        circle.classList.add('bg-success', 'text-white');
        label.classList.add('text-indigo');
        circle.innerHTML = '<i class="bi bi-check-lg"></i>';
      } else if (num === n) {
        circle.classList.add('bg-primary', 'text-white');
        label.classList.add('text-indigo');
        circle.textContent = num;
      } else {
        circle.classList.add('bg-body-secondary', 'text-muted-ef');
        label.classList.add('text-muted-ef');
        circle.textContent = num;
      }
    });

    btnBack.disabled = n === 1;
    btnNext.classList.toggle('d-none', n === total);
    btnSubmit.classList.toggle('d-none', n !== total);
    stepCounter.textContent = `Bước ${n}/${total}`;

    if (n === total) populateSummary();
    current = n;
  }

  function currentStepEl(n) {
    return steps.find(s => Number(s.dataset.step) === n);
  }

  function validateStep(n) {
    const stepEl = currentStepEl(n);
    const requiredFields = stepEl.querySelectorAll('[required]');
    for (const f of requiredFields) {
      if (!f.checkValidity()) { f.reportValidity(); return false; }
    }
    if (n === 2) {
      const checked = stepEl.querySelectorAll('input[name="expertise"]:checked');
      if (checked.length === 0) {
        alert('Vui lòng chọn ít nhất 1 lĩnh vực chuyên môn');
        return false;
      }
    }
    return true;
  }

  btnNext.addEventListener('click', () => {
    if (!validateStep(current)) return;
    if (current < total) showStep(current + 1);
  });

  btnBack.addEventListener('click', () => {
    if (current > 1) showStep(current - 1);
  });

  function populateSummary() {
    const val = id => document.getElementById(id)?.value || '';
    const selText = id => {
      const el = document.getElementById(id);
      return el && el.selectedIndex >= 0 ? el.options[el.selectedIndex].text : '';
    };

    document.getElementById('sumName').textContent = val('fullName') || '—';
    document.getElementById('sumEmail').textContent = val('email') || '—';
    document.getElementById('sumDegree').textContent = selText('degree') || '—';
    document.getElementById('sumMajor').textContent = val('major') || '—';
    document.getElementById('sumExperience').textContent = selText('experience') || '—';

    const tags = Array.from(document.querySelectorAll('input[name="expertise"]:checked')).map(i => i.value);
    document.getElementById('sumExpertise').textContent = tags.length ? tags.join(', ') : '—';

    const setChk = (inputId, iconId) => {
      const input = document.getElementById(inputId);
      const icon = document.getElementById(iconId);
      const has = input && input.files && input.files.length > 0;
      icon.className = has ? 'bi bi-check-circle-fill text-success me-2' : 'bi bi-circle text-muted-ef me-2';
    };
    setChk('idCardFile', 'chkIdCard');
    setChk('degreeFile', 'chkDegree');
    setChk('cvFile', 'chkCv');
    setChk('videoFile', 'chkVideo');
  }

  document.querySelectorAll('.file-drop input[type="file"]').forEach(input => {
    input.addEventListener('change', () => {
      const wrap = input.closest('.file-drop');
      const label = wrap.querySelector('.file-drop-text');
      if (input.files && input.files.length > 0) {
        wrap.classList.add('file-drop-done');
        label.innerHTML = '<i class="bi bi-check-circle-fill text-success me-1"></i>' + input.files[0].name;
      } else {
        wrap.classList.remove('file-drop-done');
      }
    });
  });

  showStep(1);
})();