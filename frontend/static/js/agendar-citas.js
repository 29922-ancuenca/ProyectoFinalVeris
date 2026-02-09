// =========================================================
// SCRIPT PARA AGENDAR CITAS - CALENDARIO INTERACTIVO (Flask)
// =========================================================

var datosResumenCita = {
  especialidad: '',
  medico: '',
  fecha: '',
  horario: ''
};

function seleccionarFecha(fecha) {
  var fechaObj = new Date(fecha + 'T00:00:00');
  var fechaLimite = new Date('2030-12-31T00:00:00');

  if (fechaObj > fechaLimite) {
    mostrarAlerta('No se pueden agendar citas posteriores al 31 de diciembre de 2030.', 'warning');
    return;
  }

  document.getElementById('fechaSeleccionada').value = fecha;
  document.getElementById('formAgendar').submit();
}

function cambiarMes(incremento) {
  var mesActual = parseInt(document.getElementById('mesActual').value);
  var anioActual = parseInt(document.getElementById('anioActual').value);

  mesActual += incremento;

  if (mesActual > 12) { mesActual = 1; anioActual++; }
  else if (mesActual < 1) { mesActual = 12; anioActual--; }

  if (anioActual > 2030) {
    mostrarAlerta('No se pueden agendar citas posteriores al año 2030.', 'warning');
    return;
  }

  var hoy = new Date();
  var mesHoy = hoy.getMonth() + 1;
  var anioHoy = hoy.getFullYear();

  if (anioActual < anioHoy || (anioActual === anioHoy && mesActual < mesHoy)) {
    mostrarAlerta('No se pueden agendar citas en fechas pasadas.', 'warning');
    return;
  }

  document.getElementById('mesActual').value = mesActual;
  document.getElementById('anioActual').value = anioActual;
  document.getElementById('formAgendar').submit();
}

function seleccionarHorario(boton, hora) {
  document.querySelectorAll('.agendar-horario-btn').forEach(function (btn) {
    btn.classList.remove('seleccionado');
  });

  boton.classList.add('seleccionado');
  datosResumenCita.horario = hora;
  document.getElementById('horarioSeleccionado').value = hora;
  document.getElementById('btnConfirmar').disabled = false;
}

function obtenerDatosResumen() {
  var selectEspecialidad = document.getElementById('idEspecialidad');
  if (selectEspecialidad && selectEspecialidad.selectedIndex > 0) {
    datosResumenCita.especialidad = selectEspecialidad.options[selectEspecialidad.selectedIndex].text;
  }

  var selectMedico = document.getElementById('idMedico');
  if (selectMedico && selectMedico.selectedIndex > 0) {
    datosResumenCita.medico = selectMedico.options[selectMedico.selectedIndex].text;
  }

  var inputFecha = document.getElementById('fechaSeleccionada');
  if (inputFecha && inputFecha.value) {
    datosResumenCita.fecha = formatearFechaSinDia(inputFecha.value);
  }
}

function formatearFechaSinDia(fechaStr) {
  var partes = fechaStr.split('-');
  var year = partes[0];
  var month = partes[1];
  var day = partes[2];

  var meses = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
  ];

  var nombreMes = meses[parseInt(month, 10) - 1];
  return day + ' de ' + nombreMes + ' de ' + year;
}

function mostrarModalConfirmacion() {
  obtenerDatosResumen();

  if (!datosResumenCita.horario) {
    mostrarAlerta('Por favor, seleccione un horario antes de confirmar la cita.', 'warning');
    return false;
  }

  document.getElementById('modalEspecialidad').textContent = datosResumenCita.especialidad || '-';
  document.getElementById('modalMedico').textContent = datosResumenCita.medico || '-';
  document.getElementById('modalFecha').textContent = datosResumenCita.fecha || '-';
  document.getElementById('modalHorario').textContent =
    datosResumenCita.horario + ' - ' + calcularHoraFin30m(datosResumenCita.horario);

  var modal = new bootstrap.Modal(document.getElementById('modalConfirmarCita'));
  modal.show();

  return false;
}

function calcularHoraFin30m(horaInicio) {
  if (!horaInicio) return '';

  var partes = horaInicio.split(':');
  var hora = parseInt(partes[0], 10);
  var minutos = parseInt(partes[1], 10);

  minutos += 30;
  if (minutos >= 60) {
    minutos -= 60;
    hora = (hora + 1) % 24;
  }

  var hh = (hora < 10 ? '0' : '') + hora;
  var mm = (minutos < 10 ? '0' : '') + minutos;
  return hh + ':' + mm;
}

function confirmarCita() {
  var modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarCita'));
  if (modal) modal.hide();

  document.getElementById('formConfirmar').submit();
}

function mostrarAlerta(mensaje, tipo) {
  // Mantenerlo simple para este proyecto
  alert(mensaje);
}

document.addEventListener('DOMContentLoaded', function () {
  var formConfirmar = document.getElementById('formConfirmar');
  if (formConfirmar) {
    formConfirmar.addEventListener('submit', function (e) {
      e.preventDefault();
      mostrarModalConfirmacion();
    });
  }

  var btnConfirmarModal = document.getElementById('btnConfirmarModal');
  if (btnConfirmarModal) {
    btnConfirmarModal.addEventListener('click', function () {
      confirmarCita();
    });
  }
});
