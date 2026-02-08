// JS global del sitio

document.addEventListener("DOMContentLoaded", function () {
	// Ocultar automáticamente mensajes flash (por ejemplo "Sesión cerrada")
	var alerts = document.querySelectorAll(".alert");
	if (!alerts.length) return;

	setTimeout(function () {
		alerts.forEach(function (alert) {
			// Animación simple de desvanecimiento
			alert.style.transition = "opacity 0.5s ease";
			alert.style.opacity = "0";

			// Eliminar del DOM después de la animación
			setTimeout(function () {
				if (alert && alert.parentNode) {
					alert.parentNode.removeChild(alert);
				}
			}, 600);
		});
	}, 3000); // 3 segundos visibles
});
