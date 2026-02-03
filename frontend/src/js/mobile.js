// Mobile Sidebar Toggle Script
(function() {
    function initMobileSidebars() {
        // Only run on mobile
        if (window.innerWidth > 768) return;
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.innerHTML = '☰';
        toggleBtn.setAttribute('aria-label', 'Toggle sidebar');
        document.body.appendChild(toggleBtn);
        
        // Find sidebar based on page
        const filterBar = document.querySelector('.filter-bar');
        const mapSidebar = document.querySelector('.map-sidebar');
        const collectionsSidebar = document.querySelector('.collections-sidebar');
        
        const sidebar = filterBar || mapSidebar || collectionsSidebar;
        
        if (!sidebar) {
            toggleBtn.style.display = 'none';
            return;
        }
        
        // Special handling for map sidebar
        if (mapSidebar) {
            toggleBtn.innerHTML = '🔍';
            toggleBtn.style.top = 'auto';
            toggleBtn.style.bottom = '70px';
        }
        
        // Toggle sidebar
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
            
            // Update button icon
            if (sidebar.classList.contains('active')) {
                toggleBtn.innerHTML = '✕';
            } else {
                if (mapSidebar) {
                    toggleBtn.innerHTML = '🔍';
                } else {
                    toggleBtn.innerHTML = '☰';
                }
            }
        });
        
        // Close sidebar when clicking overlay
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            
            if (mapSidebar) {
                toggleBtn.innerHTML = '🔍';
            } else {
                toggleBtn.innerHTML = '☰';
            }
        });
    }
    
    // Initialize on DOM load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileSidebars);
    } else {
        initMobileSidebars();
    }
    
    // Re-initialize on resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Remove existing elements
            const existingToggle = document.querySelector('.sidebar-toggle');
            const existingOverlay = document.querySelector('.sidebar-overlay');
            if (existingToggle) existingToggle.remove();
            if (existingOverlay) existingOverlay.remove();
            
            // Re-initialize
            initMobileSidebars();
        }, 250);
    });
})();