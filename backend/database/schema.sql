-- phpMyAdmin SQL Dump
-- version 4.6.4
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 05-12-2023 a las 01:14:53
-- Versión del servidor: 5.7.14
-- Versión de PHP: 5.6.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `veris`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `consultas`
--

CREATE TABLE `consultas` (
  `IdConsulta` int(11) NOT NULL,
  `IdMedico` int(11) NOT NULL,
  `IdPaciente` int(11) NOT NULL,
  `FechaConsulta` date NOT NULL,
  `HI` time NOT NULL,
  `HF` time NOT NULL,
  `Diagnostico` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `consultas`
--

INSERT INTO `consultas` (`IdConsulta`, `IdMedico`, `IdPaciente`, `FechaConsulta`, `HI`, `HF`, `Diagnostico`) VALUES
(1, 1, 1, '2023-01-10', '09:00:00', '10:00:00', 'Presion arterial alta'),
(2, 4, 2, '2023-02-15', '14:00:00', '15:00:00', 'Papiloma Humano'),
(3, 3, 3, '2023-03-20', '12:00:00', '13:00:00', 'Problemas cutaneos'),
(4, 4, 4, '2023-04-25', '16:00:00', '17:00:00', 'Examen ocular'),
(5, 3, 2, '2023-05-30', '10:00:00', '11:00:00', 'Chequeo ginecologico'),
(6, 3, 2, '2023-11-20', '08:00:00', '09:00:00', 'Mamografía'),
(7, 2, 2, '2023-11-22', '10:00:00', '11:00:00', 'Arritmias cardíacas'),
(8, 1, 4, '2023-11-17', '11:00:00', '12:00:00', 'Hipermetropía'),
(9, 4, 2, '2023-10-10', '15:00:00', '16:00:00', 'Acné'),
(10, 1, 1, '2023-09-11', '10:00:00', '11:00:00', 'Glaucoma'),
(11, 1, 4, '2023-08-07', '08:00:00', '09:00:00', 'Astigmatismo'),
(12, 2, 3, '2023-06-20', '11:00:00', '12:00:00', 'Hipertensión arterial'),
(13, 3, 3, '2023-11-07', '13:00:00', '14:00:00', 'Dermatitis atópica'),
(14, 2, 4, '2023-11-03', '08:00:00', '09:00:00', 'Colesterol Alto'),
(15, 4, 1, '2023-11-09', '14:00:00', '15:00:00', 'Acné');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `especialidades`
--

CREATE TABLE `especialidades` (
  `IdEsp` int(11) NOT NULL,
  `Descripcion` varchar(50) NOT NULL,
  `Dias` varchar(45) NOT NULL,
  `Franja_HI` time NOT NULL,
  `Franja_HF` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `especialidades`
--

INSERT INTO `especialidades` (`IdEsp`, `Descripcion`, `Dias`, `Franja_HI`, `Franja_HF`) VALUES
(1, 'Cardiologia', 'MJV', '08:00:00', '12:00:00'),
(2, 'Pediatria', 'LMXJV', '08:00:00', '18:00:00'),
(3, 'Dermatologia', 'MJ', '12:00:00', '18:00:00'),
(4, 'Ginecologia', 'LXV', '08:00:00', '18:00:00'),
(5, 'Oftalmologia', 'LV', '08:00:00', '12:00:00'),
(6, 'Proctologo', 'LM', '08:00:00', '12:00:00');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `medicamentos`
--

CREATE TABLE `medicamentos` (
  `IdMedicamento` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Tipo` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `medicamentos`
--

INSERT INTO `medicamentos` (`IdMedicamento`, `Nombre`, `Tipo`) VALUES
(1, 'Paracetamol', 'Analgesico'),
(2, 'Amoxicilina', 'Antibiotico'),
(3, 'Loratadina', 'Antihistaminico'),
(4, 'Omeprazol', 'Antiacido'),
(5, 'Aspirina', 'Antiinflamatorio');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `medicos`
--

CREATE TABLE `medicos` (
  `IdMedico` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Especialidad` int(11) NOT NULL,
  `IdUsuario` int(11) NOT NULL,
  `Foto` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `medicos`
--

INSERT INTO `medicos` (`IdMedico`, `Nombre`, `Especialidad`, `IdUsuario`, `Foto`) VALUES
(1, 'Oscar Lopez', 5, 8, 'kia.jpg'),
(2, 'Juan Garcia', 1, 2, 'ford.jpg'),
(3, 'Ana Perez', 4, 5, 'chevrolet.jpg'),
(4, 'Luis Quintana', 3, 9, 'toyota.jpg'),
(5, 'Julieta Armijos', 2, 10, 'BMW_Azul.jpg'),
(6, 'Dr. Manotas', 6, 11, 'kia.jpg');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pacientes`
--

CREATE TABLE `pacientes` (
  `IdPaciente` int(11) NOT NULL,
  `IdUsuario` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Cedula` int(10) UNSIGNED NOT NULL,
  `Edad` int(10) UNSIGNED NOT NULL,
  `Genero` varchar(50) NOT NULL,
  `Estatura (cm)` int(10) UNSIGNED NOT NULL,
  `Peso (kg)` float UNSIGNED NOT NULL,
  `Foto` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `pacientes`
--

INSERT INTO `pacientes` (`IdPaciente`, `IdUsuario`, `Nombre`, `Cedula`, `Edad`, `Genero`, `Estatura (cm)`, `Peso (kg)`, `Foto`) VALUES
(1, 3, 'Luis Torres', 1725001976, 20, 'Masculino', 198, 100, 'usu09.png'),
(2, 6, 'Ana Gomez', 1798456712, 70, 'Femenino', 150, 90, 'usu13.png'),
(3, 7, 'Oscar Uribe', 1725001984, 80, 'Masculino', 160, 105, 'usu01.png'),
(4, 4, 'Alex Marquez', 1723547158, 70, 'Masculino', 195, 120, 'usu15.png');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `recetas`
--

CREATE TABLE `recetas` (
  `IdReceta` int(11) NOT NULL,
  `IdConsulta` int(11) NOT NULL,
  `IdMedicamento` int(11) NOT NULL,
  `Cantidad` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `recetas`
--

INSERT INTO `recetas` (`IdReceta`, `IdConsulta`, `IdMedicamento`, `Cantidad`) VALUES
(1, 1, 1, 2),
(2, 2, 2, 1),
(3, 3, 3, 3),
(4, 4, 4, 1),
(5, 5, 5, 2),
(6, 6, 1, 3),
(7, 7, 1, 1),
(8, 8, 5, 2),
(9, 9, 1, 3),
(10, 10, 4, 2),
(11, 11, 5, 2),
(12, 12, 1, 3),
(13, 13, 3, 5),
(14, 14, 4, 5),
(15, 15, 2, 2);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `IdRol` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Accion` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`IdRol`, `Nombre`, `Accion`) VALUES
(1, 'Administrador', 'CRUD'),
(2, 'Medico', 'RU'),
(3, 'Paciente', 'RU');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `IdUsuario` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Password` varchar(64) NOT NULL,
  `Rol` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`IdUsuario`, `Nombre`, `Password`, `Rol`) VALUES
(1, 'ADM', '123', 1),
(2, 'jgarcia', '123', 2),
(3, 'ltorres', '123', 3),
(4, 'amarquez', '123', 3),
(5, 'aperez', '123', 2),
(6, 'agomez', '123', 3),
(7, 'ouribe', '123', 3),
(8, 'olopez', '123', 2),
(9, 'lquintana', '123', 2),
(10, 'jarmijos', '123', 2),
(11, 'xxx', '123', 2);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `consultas`
--
ALTER TABLE `consultas`
  ADD PRIMARY KEY (`IdConsulta`),
  ADD KEY `IdMedico_FK_idx` (`IdMedico`),
  ADD KEY `IdPaciente_idx` (`IdPaciente`);

--
-- Indices de la tabla `especialidades`
--
ALTER TABLE `especialidades`
  ADD PRIMARY KEY (`IdEsp`);

--
-- Indices de la tabla `medicamentos`
--
ALTER TABLE `medicamentos`
  ADD PRIMARY KEY (`IdMedicamento`);

--
-- Indices de la tabla `medicos`
--
ALTER TABLE `medicos`
  ADD PRIMARY KEY (`IdMedico`),
  ADD KEY `FK_IdUsuario_idx` (`IdUsuario`),
  ADD KEY `FK_Especialidad_idx` (`Especialidad`);

--
-- Indices de la tabla `pacientes`
--
ALTER TABLE `pacientes`
  ADD PRIMARY KEY (`IdPaciente`),
  ADD KEY `FK_IdUsuario_idx` (`IdUsuario`);

--
-- Indices de la tabla `recetas`
--
ALTER TABLE `recetas`
  ADD PRIMARY KEY (`IdReceta`),
  ADD KEY `FK_IdConsulta_idx` (`IdConsulta`),
  ADD KEY `FK_IdMedicamento_idx` (`IdMedicamento`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`IdRol`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`IdUsuario`),
  ADD KEY `fk_rol_idx` (`Rol`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `consultas`
--
ALTER TABLE `consultas`
  MODIFY `IdConsulta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;
--
-- AUTO_INCREMENT de la tabla `especialidades`
--
ALTER TABLE `especialidades`
  MODIFY `IdEsp` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
--
-- AUTO_INCREMENT de la tabla `medicamentos`
--
ALTER TABLE `medicamentos`
  MODIFY `IdMedicamento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
--
-- AUTO_INCREMENT de la tabla `medicos`
--
ALTER TABLE `medicos`
  MODIFY `IdMedico` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
--
-- AUTO_INCREMENT de la tabla `pacientes`
--
ALTER TABLE `pacientes`
  MODIFY `IdPaciente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
--
-- AUTO_INCREMENT de la tabla `recetas`
--
ALTER TABLE `recetas`
  MODIFY `IdReceta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;
--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `IdUsuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;
--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `consultas`
--
ALTER TABLE `consultas`
  ADD CONSTRAINT `IdMedico_FK` FOREIGN KEY (`IdMedico`) REFERENCES `medicos` (`IdMedico`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `IdPaciente` FOREIGN KEY (`IdPaciente`) REFERENCES `pacientes` (`IdPaciente`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `medicos`
--
ALTER TABLE `medicos`
  ADD CONSTRAINT `FK_Especialidad` FOREIGN KEY (`Especialidad`) REFERENCES `especialidades` (`IdEsp`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `IdUsuario_FK` FOREIGN KEY (`IdUsuario`) REFERENCES `usuarios` (`IdUsuario`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `pacientes`
--
ALTER TABLE `pacientes`
  ADD CONSTRAINT `FK_IdUsuario` FOREIGN KEY (`IdUsuario`) REFERENCES `usuarios` (`IdUsuario`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `recetas`
--
ALTER TABLE `recetas`
  ADD CONSTRAINT `FK_IdConsulta` FOREIGN KEY (`IdConsulta`) REFERENCES `consultas` (`IdConsulta`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `FK_IdMedicamento` FOREIGN KEY (`IdMedicamento`) REFERENCES `medicamentos` (`IdMedicamento`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Filtros para la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `fk_rol` FOREIGN KEY (`Rol`) REFERENCES `roles` (`IdRol`) ON DELETE CASCADE ON UPDATE CASCADE;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
