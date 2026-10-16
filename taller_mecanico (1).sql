-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 16-10-2026 a las 01:11:11
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `taller_mecanico`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `clientes`
--

CREATE TABLE `clientes` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `ap_pat` varchar(100) NOT NULL,
  `ap_mat` varchar(100) NOT NULL,
  `telefono` varchar(40) NOT NULL DEFAULT '',
  `direccion` varchar(255) NOT NULL DEFAULT '',
  `rfc` varchar(20) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `clientes`
--

INSERT INTO `clientes` (`id`, `nombre`, `ap_pat`, `ap_mat`, `telefono`, `direccion`, `rfc`) VALUES
(1, 'Hermione', 'Potter', 'Sullivan', '123456789', 'Alamedas 123', 'EJEMPLO123'),
(2, 'juan', '', '', '123456789', 'calle sultan', '123456789');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `piezas`
--

CREATE TABLE `piezas` (
  `id` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `categoria` varchar(80) NOT NULL DEFAULT 'General',
  `stock` int(11) NOT NULL DEFAULT 0,
  `precio_unitario` decimal(10,2) NOT NULL DEFAULT 0.00,
  `descripcion` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `piezas`
--

INSERT INTO `piezas` (`id`, `nombre`, `categoria`, `stock`, `precio_unitario`, `descripcion`) VALUES
(1, 'Bujias', 'General', 12, 55.00, 'folio 123456789');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reparaciones`
--

CREATE TABLE `reparaciones` (
  `id` int(11) NOT NULL,
  `vehiculo_id` int(11) NOT NULL,
  `asunto` varchar(255) NOT NULL,
  `fecha_entrada` date NOT NULL,
  `fecha_salida` date DEFAULT NULL,
  `pieza_id` int(11) DEFAULT NULL,
  `costo` decimal(10,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'Pendiente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `reparaciones`
--

INSERT INTO `reparaciones` (`id`, `vehiculo_id`, `asunto`, `fecha_entrada`, `fecha_salida`, `pieza_id`, `costo`, `estado`) VALUES
(1, 1, 'Cambio de bujias', '2026-10-15', '2026-11-15', 1, 500.00, 'En proceso'),
(2, 1, 'Cambio de bujias', '2026-10-15', '2026-11-15', 1, 500.00, 'En proceso');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reparacion_piezas`
--

CREATE TABLE `reparacion_piezas` (
  `reparacion_id` int(11) NOT NULL,
  `pieza_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(10,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `telefono` varchar(40) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `perfil` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `telefono`, `username`, `password_hash`, `perfil`) VALUES
(1, 'omar', '123456789', 'omarCamel', 'pbkdf2_sha256$b3ee88410d9c82a890cb46529ef1a66e$7cd19286c9c6f16effe98e32bc386c30da6c5a208c32423f57e0e6f7766bbf7a', 'admin'),
(2, 'Juan', '123456789', 'del', 'pbkdf2_sha256$4e9f2a6741bfe9c4ba82129254e7ef4d$b5e2466b0dc4e9f1304de7573735676340fcce37cd07640c5ad733279a81c291', 'encargado');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vehiculos`
--

CREATE TABLE `vehiculos` (
  `id` int(11) NOT NULL,
  `cliente_id` int(11) NOT NULL,
  `matricula` varchar(30) NOT NULL,
  `marca` varchar(80) NOT NULL,
  `modelo` varchar(80) NOT NULL,
  `anio` smallint(6) NOT NULL,
  `color` varchar(60) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `vehiculos`
--

INSERT INTO `vehiculos` (`id`, `cliente_id`, `matricula`, `marca`, `modelo`, `anio`, `color`) VALUES
(1, 1, 'A-700', 'Honda', 'Civic', 2014, 'Rojo');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_cliente_nombre` (`nombre`,`ap_pat`,`ap_mat`);

--
-- Indices de la tabla `piezas`
--
ALTER TABLE `piezas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_pieza_datos` (`nombre`,`categoria`);

--
-- Indices de la tabla `reparaciones`
--
ALTER TABLE `reparaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_reparacion_vehiculo` (`vehiculo_id`),
  ADD KEY `fk_reparacion_pieza` (`pieza_id`);

--
-- Indices de la tabla `reparacion_piezas`
--
ALTER TABLE `reparacion_piezas`
  ADD PRIMARY KEY (`reparacion_id`,`pieza_id`),
  ADD KEY `fk_reparacion_pieza_pieza` (`pieza_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indices de la tabla `vehiculos`
--
ALTER TABLE `vehiculos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `matricula` (`matricula`),
  ADD KEY `fk_vehiculo_cliente` (`cliente_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `clientes`
--
ALTER TABLE `clientes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `piezas`
--
ALTER TABLE `piezas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `reparaciones`
--
ALTER TABLE `reparaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `vehiculos`
--
ALTER TABLE `vehiculos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `reparaciones`
--
ALTER TABLE `reparaciones`
  ADD CONSTRAINT `fk_reparacion_pieza` FOREIGN KEY (`pieza_id`) REFERENCES `piezas` (`id`),
  ADD CONSTRAINT `fk_reparacion_vehiculo` FOREIGN KEY (`vehiculo_id`) REFERENCES `vehiculos` (`id`);

--
-- Filtros para la tabla `reparacion_piezas`
--
ALTER TABLE `reparacion_piezas`
  ADD CONSTRAINT `fk_reparacion_pieza_pieza` FOREIGN KEY (`pieza_id`) REFERENCES `piezas` (`id`),
  ADD CONSTRAINT `fk_reparacion_pieza_reparacion` FOREIGN KEY (`reparacion_id`) REFERENCES `reparaciones` (`id`);

--
-- Filtros para la tabla `vehiculos`
--
ALTER TABLE `vehiculos`
  ADD CONSTRAINT `fk_vehiculo_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
