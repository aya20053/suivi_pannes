fetch('/api/user-role')
  .then(response => response.json())
  .then(data => {
    if (data.role === 'super_admin') {
      const menu = document.getElementById('menu');

      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = "/gestion-utilisateurs";
      a.textContent = "Gestion des utilisateurs";

      li.appendChild(a);
      menu.appendChild(li);
    }
  });
