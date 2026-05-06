-- Esquema PostgreSQL existente del proyecto.
-- Este archivo queda como referencia documental; mqtt_robodk_bridge.py no lo ejecuta.

CREATE TABLE Medicamento (
  id_medicamento VARCHAR PRIMARY KEY,
  cod_barras INT NOT NULL,
  nombre VARCHAR NOT NULL,
  caducidad DATE NOT NULL,
  descripcion VARCHAR,
  stock INT NOT NULL,
  estado VARCHAR NOT NULL,
  pos VARCHAR,
  precio_venta FLOAT NOT NULL,
  seguro_SS BOOLEAN NOT NULL
);

CREATE TABLE Cliente (
  DNI VARCHAR PRIMARY KEY,
  num_seguridad_social VARCHAR NOT NULL,
  fecha_nacimiento DATE NOT NULL,
  telefono INT NOT NULL,
  descuento_SS INT NOT NULL
);

CREATE TABLE Venta (
  DNI VARCHAR NOT NULL,
  id_medicamento VARCHAR NOT NULL,
  fecha_venta DATE NOT NULL,
  precio_total FLOAT NOT NULL,
  PRIMARY KEY (DNI, id_medicamento, fecha_venta),
  FOREIGN KEY (DNI) REFERENCES Cliente(DNI),
  FOREIGN KEY (id_medicamento) REFERENCES Medicamento(id_medicamento)
);

CREATE TABLE Caja_Grande (
  id_caja VARCHAR PRIMARY KEY,
  fecha_hora_entrada TIMESTAMP NOT NULL,
  estado VARCHAR NOT NULL,
  num_medicamentos INT NOT NULL
);

CREATE TABLE Cinta_Transportadora (
  id_cinta VARCHAR PRIMARY KEY,
  nombre VARCHAR NOT NULL,
  estado_parada BOOLEAN NOT NULL,
  longitud_m INT NOT NULL
);

CREATE TABLE Sensor (
  id_sensor VARCHAR PRIMARY KEY,
  nombre VARCHAR NOT NULL,
  tipo VARCHAR NOT NULL,
  estado_activo BOOLEAN NOT NULL,
  id_cinta VARCHAR,
  FOREIGN KEY (id_cinta) REFERENCES Cinta_Transportadora(id_cinta)
);

CREATE TABLE Robot (
  id_robot VARCHAR PRIMARY KEY,
  nombre VARCHAR NOT NULL,
  modelo VARCHAR NOT NULL,
  rol VARCHAR NOT NULL
);

CREATE TABLE Herramienta (
  id_herramienta VARCHAR PRIMARY KEY,
  nombre VARCHAR NOT NULL,
  id_robot VARCHAR,
  FOREIGN KEY (id_robot) REFERENCES Robot(id_robot)
);

CREATE TABLE Contiene (
  id_medicamento VARCHAR NOT NULL,
  id_caja VARCHAR NOT NULL,
  PRIMARY KEY (id_medicamento, id_caja),
  FOREIGN KEY (id_medicamento) REFERENCES Medicamento(id_medicamento),
  FOREIGN KEY (id_caja) REFERENCES Caja_Grande(id_caja)
);
