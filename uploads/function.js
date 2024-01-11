document.querySelectorAll('.project').forEach(project => {
    let currentIndex = 0;
    const images = Array.from(project.querySelectorAll('.slideshow img'));

    function showImage(index) {
        images.forEach((image, i) => {
            image.style.display = i === index ? 'block' : 'none';
        });
    }

    setInterval(function() {
        showImage(currentIndex);
        currentIndex = (currentIndex + 1) % images.length;
    }, 2300);
});


const ligthModeToggle = document.getElementById('darkModeToggle');
const body = document.body;

ligthModeToggleModeToggle.addEventListener('change', () => {
    body.classList.toggle('light-mode', ligthModeToggle.checked);
});

