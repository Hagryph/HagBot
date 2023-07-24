(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const profileButton = document.getElementById('profile-button');
        const dropdownMenu = document.getElementById('dropdown-menu');

        profileButton.addEventListener('click', () => {
            dropdownMenu.classList.toggle('hidden');
        });

        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            if (item.id !== 'header') {
                item.addEventListener('click', () => {
                    const menuItemText = item.innerText.trim().toLowerCase().replace(/\s+/g, '_');
                    window.location.href = '/action/' + menuItemText;
                });
            }
        });
    });
})();