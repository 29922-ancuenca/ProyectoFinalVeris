// JS global del sitio

// =====================================================
// Modal global (reemplazo de alert/confirm nativos)
// app.js se carga al final del <body>, por lo que el modal ya existe.
// =====================================================
(function initVerisModal() {
		var modalEl = document.getElementById('verisModal');
		var hasBootstrapModal = !!(modalEl && window.bootstrap && window.bootstrap.Modal);

		// Fallback sin Bootstrap: usar <dialog> nativo
		var dialogEl = null;
		if (!hasBootstrapModal) {
			dialogEl = document.getElementById('verisDialog');
			if (!dialogEl && document.createElement) {
				dialogEl = document.createElement('dialog');
				dialogEl.id = 'verisDialog';
				dialogEl.style.maxWidth = '520px';
				dialogEl.innerHTML = "<form method='dialog' style='margin:0'>" +
					"<h5 id='verisDialogTitle' style='margin:0 0 12px 0'>Mensaje</h5>" +
					"<div id='verisDialogBody' style='margin:0 0 16px 0'></div>" +
					"<div style='display:flex; gap:8px; justify-content:flex-end'>" +
					"<button id='verisDialogCancel' value='cancel' type='submit'>Cancelar</button>" +
					"<button id='verisDialogOk' value='ok' type='submit'>Aceptar</button>" +
					"</div></form>";
				document.body.appendChild(dialogEl);
			}
		}

		var titleEl = hasBootstrapModal ? document.getElementById('verisModalTitle') : (dialogEl ? dialogEl.querySelector('#verisDialogTitle') : null);
		var bodyEl = hasBootstrapModal ? document.getElementById('verisModalBody') : (dialogEl ? dialogEl.querySelector('#verisDialogBody') : null);
		var cancelBtn = hasBootstrapModal ? document.getElementById('verisModalCancel') : (dialogEl ? dialogEl.querySelector('#verisDialogCancel') : null);
		var okBtn = hasBootstrapModal ? document.getElementById('verisModalOk') : (dialogEl ? dialogEl.querySelector('#verisDialogOk') : null);
		var modal = hasBootstrapModal ? window.bootstrap.Modal.getOrCreateInstance(modalEl) : null;

		function setText(el, text) {
			if (!el) return;
			el.textContent = String(text || '');
		}

		function show(opts) {
			opts = opts || {};
			setText(titleEl, opts.title || 'Mensaje');
			if (bodyEl) bodyEl.textContent = String(opts.message || '');

			var showCancel = !!opts.showCancel;
			if (cancelBtn) cancelBtn.style.display = showCancel ? '' : 'none';
			setText(okBtn, opts.okText || (showCancel ? 'Sí' : 'Aceptar'));
			setText(cancelBtn, opts.cancelText || 'Cancelar');
			if (hasBootstrapModal) {
				modal.show();
			} else if (dialogEl && dialogEl.showModal) {
				dialogEl.showModal();
			}
		}

		function alertModal(message, title) {
			return new Promise(function (resolve) {
				function cleanup() {
					okBtn && okBtn.removeEventListener('click', onOk);
					if (hasBootstrapModal) modalEl.removeEventListener('hidden.bs.modal', onHidden);
					if (!hasBootstrapModal && dialogEl) dialogEl.removeEventListener('close', onClose);
				}
				function onOk() {
					cleanup();
					if (hasBootstrapModal) modal.hide();
					else if (dialogEl && dialogEl.close) dialogEl.close('ok');
					resolve(true);
				}
				function onHidden() {
					cleanup();
					resolve(true);
				}
				function onClose() {
					cleanup();
					resolve(true);
				}
				okBtn && okBtn.addEventListener('click', onOk);
				if (hasBootstrapModal) modalEl.addEventListener('hidden.bs.modal', onHidden);
				else if (dialogEl) dialogEl.addEventListener('close', onClose);
				show({ title: title || 'Mensaje', message: message, showCancel: false, okText: 'Aceptar' });
			});
		}

		function confirmModal(message, title) {
			return new Promise(function (resolve) {
				function cleanup() {
					okBtn && okBtn.removeEventListener('click', onOk);
					cancelBtn && cancelBtn.removeEventListener('click', onCancel);
					if (hasBootstrapModal) modalEl.removeEventListener('hidden.bs.modal', onHidden);
					if (!hasBootstrapModal && dialogEl) dialogEl.removeEventListener('close', onClose);
				}
				function onOk() {
					cleanup();
					if (hasBootstrapModal) modal.hide();
					else if (dialogEl && dialogEl.close) dialogEl.close('ok');
					resolve(true);
				}
				function onCancel() {
					cleanup();
					if (hasBootstrapModal) modal.hide();
					else if (dialogEl && dialogEl.close) dialogEl.close('cancel');
					resolve(false);
				}
				function onHidden() {
					cleanup();
					resolve(false);
				}
				function onClose() {
					var ret = (dialogEl && dialogEl.returnValue) ? dialogEl.returnValue : 'cancel';
					cleanup();
					resolve(ret === 'ok');
				}
				okBtn && okBtn.addEventListener('click', onOk);
				cancelBtn && cancelBtn.addEventListener('click', onCancel);
				if (hasBootstrapModal) modalEl.addEventListener('hidden.bs.modal', onHidden);
				else if (dialogEl) dialogEl.addEventListener('close', onClose);
				show({ title: title || 'Confirmación', message: message, showCancel: true, okText: 'Sí', cancelText: 'Cancelar' });
			});
		}

		window.VerisModal = {
			alert: alertModal,
			confirm: confirmModal
		};
	})();

document.addEventListener("DOMContentLoaded", function () {
	// Si existen alertas danger/warning, mostrarlas en modal y quitar del DOM.
	// Solo aplica para el Administrador (rol=1) para no estorbar en flujos de paciente/médico.
	var role = (document.body && document.body.getAttribute) ? String(document.body.getAttribute('data-user-role') || '') : '';
	var isAdmin = role === '1';
	var blockingAlerts = isAdmin ? Array.prototype.slice.call(document.querySelectorAll('.alert.alert-danger, .alert.alert-warning')) : [];
	if (blockingAlerts.length && window.VerisModal && window.VerisModal.alert) {
		var first = blockingAlerts[0];
		var msg = first ? (first.textContent || '').trim() : '';
		// Limpiar todas las alertas bloqueantes para que no dupliquen el mensaje
		blockingAlerts.forEach(function (a) {
			if (a && a.parentNode) a.parentNode.removeChild(a);
		});
		if (msg) window.VerisModal.alert(msg, 'Acción no permitida');
	}

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

// Confirmación global para enlaces y formularios
document.addEventListener('click', function (e) {
	var a = e.target && e.target.closest ? e.target.closest('a[data-veris-confirm]') : null;
	if (!a) return;
	e.preventDefault();
	var msg = a.getAttribute('data-veris-confirm') || '¿Desea continuar?';
	var href = a.getAttribute('href') || '';
	var run = function () { if (href) window.location.href = href; };
	window.VerisModal.confirm(msg).then(function (ok) { if (ok) run(); });
});

document.addEventListener('submit', function (e) {
	var form = e.target;
	if (!form || !form.getAttribute) return;
	var msg = form.getAttribute('data-veris-confirm');
	if (!msg) return;
	e.preventDefault();
	var run = function () { form.submit(); };
	window.VerisModal.confirm(msg).then(function (ok) { if (ok) run(); });
});
