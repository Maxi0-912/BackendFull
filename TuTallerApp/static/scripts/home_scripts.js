// ============================================
// FUNCIÓN PARA EL MENÚ DE PERFIL
// ============================================
function togglePerfilMenu() {
    const menu = document.getElementById('perfilMenu');
    const btn = document.querySelector('.perfil-btn');
    
    menu.classList.toggle('show');
    btn.classList.toggle('active');
}

// Cerrar el menú si se hace clic fuera de él
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.perfil-dropdown');
    const menu = document.getElementById('perfilMenu');
    
    if (dropdown && !dropdown.contains(event.target)) {
        menu?.classList.remove('show');
        document.querySelector('.perfil-btn')?.classList.remove('active');
    }
});

// ============================================
// FUNCIÓN PARA EL MODAL DE EDITAR PERFIL
// ============================================
function abrirModalPerfil() {
    document.getElementById('modalEditarPerfil').classList.add('show');
    // Cerrar el menú dropdown al abrir el modal
    document.getElementById('perfilMenu').classList.remove('show');
    document.querySelector('.perfil-btn').classList.remove('active');
}

function cerrarModalPerfil() {
    document.getElementById('modalEditarPerfil').classList.remove('show');
}

// Cerrar modal al hacer clic fuera del contenido
document.addEventListener('click', function(event) {
    const modal = document.getElementById('modalEditarPerfil');
    if (event.target === modal) {
        cerrarModalPerfil();
    }
});

// Cerrar modal con la tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cerrarModalPerfil();
    }
});

// ============================================
// SLIDER DE IMÁGENES (solo en home)
// ============================================
const slider = document.querySelector('.slider');

// Solo ejecutar si el slider existe en la página
if (slider) {
    const images = slider.querySelectorAll('img');
    let currentIndex = 0;
    
    setInterval(() => {
        currentIndex = (currentIndex + 1) % images.length;
        slider.scrollTo({
            left: slider.offsetWidth * currentIndex,
            behavior: 'smooth'
        });
    }, 4000);
}