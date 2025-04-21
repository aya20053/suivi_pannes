document.addEventListener('DOMContentLoaded', function () {
    const desktopLinks = document.querySelectorAll('.desktop-nav .nav-item');
    const mobileLinks = document.querySelectorAll('.mobile-nav .mobile-nav-item');
    const contentSections = document.querySelectorAll('#mainContent > section');

    // Récupérer le rôle depuis l'attribut data-user-role du body
    const userRole = document.body.getAttribute('data-user-role');
    console.log("Rôle utilisateur:", userRole);

    // Masquer ou afficher les liens de gestion des utilisateurs en fonction du rôle
    const manageUsersDesktopLink = document.getElementById('manage-users-link');
    const manageUsersMobileLink = document.getElementById('mobile-manage-users-link');

    [manageUsersDesktopLink, manageUsersMobileLink].forEach(link => {
        if (link) {
            link.style.display = (userRole === 'admin' || userRole === 'chef_admin') ? 'block' : 'none';
        }
    });

    // Fonction pour activer dynamiquement les liens
    function activateNav(link) {
        const navType = link.classList.contains('nav-item') ? '.nav-item' : '.mobile-nav-item';
        const allLinks = document.querySelectorAll(navType);

        allLinks.forEach(item => item.classList.remove('active'));
        link.classList.add('active');

        const pageName = link.getAttribute('data-navlink');
        contentSections.forEach(section => {
            if (section.getAttribute('data-page') === pageName) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    }

    desktopLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
                activateNav(this);
            }
        });
    });

    mobileLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
                activateNav(this);
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Sélectionner les liens de gestion des utilisateurs pour desktop et mobile
    const manageUsersDesktopLink = document.getElementById('manage-users-link');
    const manageUsersMobileLink = document.getElementById('mobile-manage-users-link');

    // Récupérer le rôle de l'utilisateur depuis l'attribut data-user-role du body
    const userRole = document.body.getAttribute('data-user-role');
    console.log("Rôle utilisateur:", userRole);

    // Vérification et affichage des liens uniquement pour le rôle 'chef_admin'
    if (userRole === 'chef_admin') {
        if (manageUsersDesktopLink) {
            manageUsersDesktopLink.style.display = 'block';
        }
        if (manageUsersMobileLink) {
            manageUsersMobileLink.style.display = 'block';
        }
    } else {
        if (manageUsersDesktopLink) {
            manageUsersDesktopLink.style.display = 'none';
        }
        if (manageUsersMobileLink) {
            manageUsersMobileLink.style.display = 'none';
        }
    }
});


console.log("Le script a démarré.");
let maVariable = 10;
console.log("La valeur de maVariable est :", maVariable);
if (maVariable > 5) {
    console.log("La condition est vraie.");
}