document.addEventListener('DOMContentLoaded', function() {
    var optionsButton = document.querySelector('.options-button');
    var dropdownMenu = document.querySelector('.options-dropdown');

    optionsButton.addEventListener('click', function() {
        dropdownMenu.classList.toggle('active');
    });
});
