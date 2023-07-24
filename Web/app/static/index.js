(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const images = document.querySelectorAll('.image-container img');

        // The function that makes the images visible
        function handleScroll() {
            images.forEach(image => {
                // Check if the image is in view
                const imageTop = image.getBoundingClientRect().top;
                const imageBottom = image.getBoundingClientRect().bottom;
                const isInView = imageTop > 0 && imageBottom < window.innerHeight;

                // If the image is in view, add the "visible" class
                if (isInView) {
                    image.classList.add('visible');
                }
            });
        }

        // Call the function when the user scrolls
        window.addEventListener('scroll', handleScroll);
    });
})();