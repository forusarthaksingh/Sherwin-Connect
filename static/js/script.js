function showSection(section) {
    document.getElementById('inbox').style.display = section === 'inbox' ? 'block' : 'none';
    document.getElementById('compose').style.display = section === 'compose' ? 'block' : 'none';
  }
  
  document.getElementById("toggleSidebar").addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    sidebar.style.display = sidebar.style.display === "none" ? "block" : "none";
  });
  
  function toggleProfile() {
    const dropdown = document.getElementById('profileDropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
  }

  function showSection(section) {
    document.getElementById('inbox').style.display = (section === 'inbox') ? 'block' : 'none';
    document.getElementById('compose').style.display = (section === 'compose') ? 'block' : 'none';
  }

  document.getElementById("composeBtn").addEventListener("click", () => {
    const form = document.getElementById("composeForm");
    form.style.display = form.style.display === "none" ? "block" : "none";
  });

  document.addEventListener("DOMContentLoaded", function () {
    const composeBtn = document.getElementById("composeBtn");
    const composeForm = document.getElementById("composeForm");
  
    if (composeBtn && composeForm) {
      composeBtn.addEventListener("click", () => {
        composeForm.style.display = composeForm.style.display === "none" ? "block" : "none";
        composeBtn.textContent = composeForm.style.display === "block" ? "×" : "+";
      });
    }
  });
  
  
  