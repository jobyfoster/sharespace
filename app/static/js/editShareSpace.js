document.addEventListener("DOMContentLoaded", function() {
    var visibilitySelect = document.querySelector('select[name="visibility"]');
    var passwordContainer = document.getElementById('div_id_password');

    var passwordInput = document.getElementById('passwordinput');
    var togglePasswordButton = document.getElementById('togglePassword');


    if (visibilitySelect.value === 'password_protected') {
        passwordInput.disabled = false;
        passwordContainer.classList.remove("hidden")
    } else {
        passwordInput.disabled = true;
        passwordContainer.classList.add("hidden")
    }

    // Function to toggle the password field
    function togglePasswordField() {
        if (visibilitySelect.value === 'password_protected') {
            passwordInput.disabled = false;
            passwordContainer.classList.remove("hidden")
        } else {
            passwordInput.disabled = true;
            passwordContainer.classList.add("hidden")
        }
    }

    // Add event listener to visibility select dropdown
    visibilitySelect.addEventListener('change', togglePasswordField);

    togglePasswordButton.addEventListener('click', function(e) {
        // Prevent the button from submitting the form
        e.preventDefault();

        // Toggle the type attribute
        var type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Toggle the eye/eye-slash icon
        this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
    });
});