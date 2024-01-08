// Waits for the entire HTML document to be fully loaded before running the script.
document.addEventListener('DOMContentLoaded', function() {
    // Selects the element with the class 'options-button'.
    var optionsButton = document.querySelector('.options-button');
    // Selects the element with the class 'options-dropdown'.
    var dropdownMenu = document.querySelector('.options-dropdown');

    // Adds an event listener for 'click' events on the options button.
    optionsButton.addEventListener('click', function() {
        // Toggles the 'active' class on the dropdown menu element.
        // This usually means showing or hiding the dropdown.
        dropdownMenu.classList.toggle('active');
    });
});
