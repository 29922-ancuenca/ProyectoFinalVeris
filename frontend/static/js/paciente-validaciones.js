(function () {
  'use strict';

  function onlyLettersAndSpace(value) {
    // Incluye tildes y ñ
    return (value || '').replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, '');
  }

  function collapseSpaces(value) {
    return (value || '').trim().replace(/\s+/g, ' ');
  }

  function collapseSpacesKeepTrailing(value) {
    const raw = String(value || '');
    const hadTrailingSpace = /\s$/.test(raw);
    const collapsed = raw.replace(/\s+/g, ' ').replace(/^\s+/, '');
    if (!hadTrailingSpace) return collapsed;
    // Permite que el usuario escriba "Nombre " antes de empezar el apellido
    return collapsed.endsWith(' ') ? collapsed : (collapsed + ' ');
  }

  function toTitleCaseWord(word) {
    if (!word) return '';
    const lower = word.toLowerCase();
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  }

  function normalizePacienteNombre(value, keepTrailingSpace) {
    let v = onlyLettersAndSpace(value);
    v = keepTrailingSpace ? collapseSpacesKeepTrailing(v) : collapseSpaces(v);
    const parts = v.split(' ').filter(Boolean);
    // Solo Nombre Apellido
    if (parts.length > 2) {
      v = parts.slice(0, 2).join(' ');
    }
    const finalParts = v.split(' ').filter(Boolean).map(toTitleCaseWord);
    const normalized = finalParts.join(' ');
    if (keepTrailingSpace && /\s$/.test(v) && finalParts.length < 2) {
      return normalized + ' ';
    }
    return normalized;
  }

  function isValidPacienteNombre(value) {
    const v = collapseSpaces(onlyLettersAndSpace(value));
    const parts = v.split(' ').filter(Boolean);
    if (parts.length !== 2) return false;
    return parts.every(p => /^[A-Za-zÁÉÍÓÚáéíóúÑñ]+$/.test(p) && p.length >= 2);
  }

  // =====================================================
  // CÉDULA ECUATORIANA - MODULO 10
  // =====================================================
  function validarCedulaJS(cedula) {
    if (!cedula) return false;
    const c = String(cedula).trim();
    if (c.length !== 10) return false;
    if (!/^\d{10}$/.test(c)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) {
      const digit = parseInt(c[i], 10);
      if (i % 2 === 0) {
        const mul = digit * 2;
        sum += (mul > 9) ? (mul - 9) : mul;
      } else {
        sum += digit;
      }
    }

    const last = parseInt(c[9], 10);
    const mod = sum % 10;

    return (mod === 0 && last === 0) || ((10 - mod) === last);
  }

  function asNumber(value) {
    if (value === '' || value === null || value === undefined) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function setRangeAttributes(input, min, max, step) {
    if (!input) return;
    if (min !== null && min !== undefined) input.setAttribute('min', String(min));
    if (max !== null && max !== undefined) input.setAttribute('max', String(max));
    if (step !== null && step !== undefined) input.setAttribute('step', String(step));
  }

  function setupPacienteForm(form) {
    if (!form) return;

    // En /register existen ambos sets de campos (paciente/médico) en el DOM.
    // Solo debemos aplicar normalización/validación de Paciente cuando el rol sea Paciente (3).
    const rol = form.querySelector('#Rol');
    function isPacienteRoleActive() {
      if (!rol) return true; // CRUD admin u otros formularios
      return String(rol.value || '').trim() === '3';
    }

    const nombre = form.querySelector('#NombrePerfil, #Nombre');
    const cedula = form.querySelector('#Cedula');
    const edad = form.querySelector('#Edad');
    const genero = form.querySelector('#Genero');
    const estatura = form.querySelector('#Estatura_cm');
    const peso = form.querySelector('#Peso_kg');

    if (nombre) {
      nombre.addEventListener('input', function () {
        if (!isPacienteRoleActive()) return;
        const cursor = nombre.selectionStart;
        const normalized = normalizePacienteNombre(nombre.value, true);
        nombre.value = normalized;
        try { nombre.setSelectionRange(cursor, cursor); } catch (e) {}
      });
      nombre.addEventListener('blur', function () {
        if (!isPacienteRoleActive()) return;
        nombre.value = normalizePacienteNombre(nombre.value, false);
      });
    }

    if (cedula) {
      cedula.setAttribute('maxlength', '10');
      cedula.setAttribute('inputmode', 'numeric');
      cedula.addEventListener('input', function () {
        cedula.value = String(cedula.value || '').replace(/\D/g, '').slice(0, 10);
      });
    }

    setRangeAttributes(edad, 0, 120, 1);
    setRangeAttributes(estatura, 30, 250, 0.01);
    setRangeAttributes(peso, 0, 300, 0.01);

    form.addEventListener('submit', function (e) {
      if (!isPacienteRoleActive()) return;
      // Solo validar si están presentes los campos del paciente
      if (nombre && !isValidPacienteNombre(nombre.value)) {
        e.preventDefault();
        alert('Nombre inválido. Debe ser solo letras y con formato: Nombre Apellido');
        return;
      }

      if (cedula) {
        const c = String(cedula.value || '').trim();

        // Evitar overflow de la columna `Cedula` (INT UNSIGNED)
        if (/^\d{10}$/.test(c)) {
          const asNum = Number(c);
          if (Number.isFinite(asNum) && asNum > 4294967295) {
            e.preventDefault();
            alert('Cédula inválida o fuera de rango. Ingrese una cédula ecuatoriana válida.');
            return;
          }
        }

        if (!validarCedulaJS(c)) {
          e.preventDefault();
          alert('Cédula inválida. Ingrese una cédula ecuatoriana válida.');
          return;
        }
      }

      if (edad) {
        const n = asNumber(edad.value);
        if (n === null || n < 0 || n > 120) {
          e.preventDefault();
          alert('Edad inválida. Debe estar entre 0 y 120.');
          return;
        }
      }

      if (estatura && estatura.value !== '') {
        const n = asNumber(estatura.value);
        if (n === null || n < 30 || n > 250) {
          e.preventDefault();
          alert('Estatura inválida. Debe estar entre 30 y 250 cm.');
          return;
        }
      }

      if (peso && peso.value !== '') {
        const n = asNumber(peso.value);
        if (n === null || n < 0 || n > 300) {
          e.preventDefault();
          alert('Peso inválido. Debe estar entre 0 y 300 kg.');
          return;
        }
      }

      if (genero) {
        const g = String(genero.value || '').trim();
        if (g !== 'Masculino' && g !== 'Femenino') {
          e.preventDefault();
          alert('Género inválido. Seleccione Masculino o Femenino.');
          return;
        }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Register y CRUD
    const forms = document.querySelectorAll('form');
    forms.forEach(setupPacienteForm);
  });
})();
