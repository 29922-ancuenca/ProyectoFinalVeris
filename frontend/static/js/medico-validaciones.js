(function () {
  'use strict';

  const PREFIX = 'Dr/a. ';

  function onlyLettersAndSpace(value) {
    return (value || '').replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s\.\/]/g, '');
  }

  function collapseSpaces(value) {
    return (value || '').trim().replace(/\s+/g, ' ');
  }

  function collapseSpacesKeepTrailing(value) {
    const raw = String(value || '');
    const hadTrailingSpace = /\s$/.test(raw);
    const collapsed = raw.replace(/\s+/g, ' ').replace(/^\s+/, '');
    if (!hadTrailingSpace) return collapsed;
    return collapsed.endsWith(' ') ? collapsed : (collapsed + ' ');
  }

  function toTitleCaseWord(word) {
    if (!word) return '';
    const lower = word.toLowerCase();
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  }

  function normalizeDoctorNombre(value, keepTrailingSpace) {
    let v = String(value || '');
    v = v.replace(/^Dr\/a\.\s*/i, '');
    v = onlyLettersAndSpace(v);
    v = keepTrailingSpace ? collapseSpacesKeepTrailing(v) : collapseSpaces(v);

    const parts = v.split(' ').filter(Boolean);
    if (parts.length > 2) v = parts.slice(0, 2).join(' ');

    const finalParts = v.split(' ').filter(Boolean).map(toTitleCaseWord);
    const normalized = PREFIX + finalParts.join(' ');
    if (keepTrailingSpace && /\s$/.test(v) && finalParts.length < 2) {
      return normalized + ' ';
    }
    return normalized;
  }

  function isValidDoctorNombre(value) {
    const v = String(value || '').trim();
    if (!v.startsWith(PREFIX)) return false;
    const body = v.slice(PREFIX.length).trim();
    const parts = body.split(' ').filter(Boolean);
    if (parts.length !== 2) return false;
    return parts.every(p => /^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$/.test(p) && p.length >= 2);
  }

  function setupDoctorNombreField(field, roleEl) {
    if (!field) return;

    // Evitar registrar listeners duplicados (en /register el usuario puede cambiar rol varias veces)
    if (field.dataset && field.dataset.doctorSetup === '1') {
      return;
    }
    if (field.dataset) field.dataset.doctorSetup = '1';

    function isDoctorRoleActive() {
      if (!roleEl) return true; // CRUD admin u otros formularios
      return String(roleEl.value || '').trim() === '2';
    }

    function ensurePrefix() {
      if (!isDoctorRoleActive()) return;
      if (!field.value) {
        field.value = PREFIX;
        return;
      }
      if (!String(field.value).startsWith(PREFIX)) {
        field.value = normalizeDoctorNombre(field.value, false);
      }
    }

    field.addEventListener('focus', ensurePrefix);
    field.addEventListener('input', function () {
      if (!isDoctorRoleActive()) return;
      // Evitar que borren el prefijo
      if (!String(field.value).startsWith(PREFIX)) {
        field.value = normalizeDoctorNombre(field.value, true);
      } else {
        // normalizar la parte del nombre
        field.value = normalizeDoctorNombre(field.value, true);
      }
    });

    field.addEventListener('blur', function () {
      if (!isDoctorRoleActive()) return;
      field.value = normalizeDoctorNombre(field.value, false);
    });

    ensurePrefix();
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Register
    const rol = document.getElementById('Rol');
    const nombrePerfil = document.getElementById('NombrePerfil');

    function applyRoleDoctor() {
      if (!rol || !nombrePerfil) return;
      if (rol.value === '2') {
        setupDoctorNombreField(nombrePerfil, rol);
      }
    }

    if (rol) {
      rol.addEventListener('change', applyRoleDoctor);
      applyRoleDoctor();
    }

    // CRUD Medico (admin)
    const nombreMedico = document.getElementById('Nombre');
    if (nombreMedico) {
      setupDoctorNombreField(nombreMedico, null);
    }

    document.querySelectorAll('form').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        const rolForm = form.querySelector('#Rol');
        const isDoctorRole = !rolForm || String(rolForm.value || '').trim() === '2';
        if (!isDoctorRole) return;

        // Validar solo si existe el campo de nombre de médico
        const n = form.querySelector('#NombrePerfil, #Nombre');
        if (n && !isValidDoctorNombre(n.value)) {
          e.preventDefault();
          alert('Nombre de médico inválido. Debe tener el formato: Dr/a. Nombre Apellido');
        }
      });
    });
  });
})();
