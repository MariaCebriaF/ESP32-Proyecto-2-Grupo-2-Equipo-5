import express from 'express';
import mqtt from 'mqtt';

const app = express();
const port = Number(process.env.PORT || 8787);

const baseTopic = process.env.MQTT_BASE_TOPIC || 'giirob/pr2/grupo2equipo5';
const mqttUrl = process.env.MQTT_URL || 'mqtt://broker.hivemq.com:1883';
const pythonBridgeEnabled = process.env.PYTHON_BRIDGE_ENABLED === 'true';
const mqttOptions = {
  clientId: `web-demo-grupo2equipo5-${Math.random().toString(16).slice(2)}`,
  reconnectPeriod: 3000
};

if (process.env.MQTT_USERNAME) {
  mqttOptions.username = process.env.MQTT_USERNAME;
}

if (process.env.MQTT_PASSWORD) {
  mqttOptions.password = process.env.MQTT_PASSWORD;
}

const topics = {
  storageRegister: `${baseTopic}/almacen/registro`,
  storageStatus: `${baseTopic}/almacen/status`,
  storageCommand: `${baseTopic}/almacen/command`,
  orderRequest: `${baseTopic}/pedido/request`,
  orderStatus: `${baseTopic}/pedido/status`,
  orderCommand: `${baseTopic}/pedido/command`
};

const state = {
  connected: false,
  pythonBridgeEnabled,
  baseTopic,
  topics,
  rack: { x: 1, y: 1, maxX: 4, maxY: 3 },
  inventory: [
    {
      id: 'MED-001',
      tipo: 'Paracetamol',
      cod_barras: '847000100001',
      posicion: 'X01-Y01',
      caducidad: '2027-05-01',
      stock: 3,
      estado: 'disponible'
    },
    {
      id: 'MED-002',
      tipo: 'Ibuprofeno',
      cod_barras: '847000100002',
      posicion: 'X01-Y02',
      caducidad: '2027-08-15',
      stock: 2,
      estado: 'disponible'
    }
  ],
  events: []
};

const processedStorageEvents = new Set();
const processedOrderRequests = new Set();

app.use(express.json());

function addEvent(type, source, topic, payload) {
  state.events.unshift({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    time: new Date().toLocaleTimeString('es-ES', { hour12: false }),
    type,
    source,
    topic,
    payload
  });

  state.events = state.events.slice(0, 60);
}

function publishJson(topic, payload) {
  const message = JSON.stringify(payload);
  client.publish(topic, message);
  addEvent('publish', 'web', topic, payload);
}

function currentRackPosition() {
  return `X${String(state.rack.x).padStart(2, '0')}-Y${String(state.rack.y).padStart(2, '0')}`;
}

function advanceRack() {
  state.rack.y += 1;

  if (state.rack.y > state.rack.maxY) {
    state.rack.y = 1;
    state.rack.x += 1;
  }

  if (state.rack.x > state.rack.maxX) {
    state.rack.x = 1;
  }
}

function upsertInventoryFromStorage(payload) {
  if (payload.id_evento && processedStorageEvents.has(payload.id_evento)) {
    return;
  }

  if (payload.id_evento) {
    processedStorageEvents.add(payload.id_evento);
  }

  const existing = state.inventory.find(
    item => item.tipo.toLowerCase() === String(payload.tipo || '').toLowerCase()
      && item.posicion === payload.posicion
  );

  if (existing) {
    existing.stock += Number(payload.cantidad || 1);
    existing.caducidad = payload.caducidad || existing.caducidad;
    existing.cod_barras = payload.cod_barras || existing.cod_barras;
    existing.estado = 'disponible';
    return;
  }

  state.inventory.push({
    id: `MED-${String(state.inventory.length + 1).padStart(3, '0')}`,
    tipo: payload.tipo,
    cod_barras: payload.cod_barras,
    posicion: payload.posicion,
    caducidad: payload.caducidad,
    stock: Number(payload.cantidad || 1),
    estado: 'disponible'
  });
}

function processOrder(payload) {
  if (payload.id_pedido && processedOrderRequests.has(payload.id_pedido)) {
    return;
  }

  if (payload.id_pedido) {
    processedOrderRequests.add(payload.id_pedido);
  }

  const item = state.inventory.find(
    candidate => candidate.tipo.toLowerCase() === String(payload.tipo || '').toLowerCase()
      && candidate.stock >= Number(payload.cantidad || 1)
  );

  if (!item) {
    publishJson(topics.orderStatus, {
      id_pedido: payload.id_pedido,
      estado: 'no_disponible',
      tipo: payload.tipo,
      mensaje: 'No hay stock disponible'
    });
    return;
  }

  item.stock -= Number(payload.cantidad || 1);
  item.estado = item.stock > 0 ? 'disponible' : 'agotado';

  publishJson(topics.orderStatus, {
    id_pedido: payload.id_pedido,
    estado: 'preparando',
    tipo: payload.tipo,
    posicion: item.posicion,
    robot: 'robot_pedidos',
    mensaje: `Enviar RoboDK a ${item.posicion}`
  });
}

function parsePayload(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

const client = mqtt.connect(mqttUrl, mqttOptions);

client.on('connect', () => {
  state.connected = true;
  client.subscribe(Object.values(topics));
  addEvent('status', 'mqtt', 'conexion', { estado: 'conectado', broker: mqttUrl });
});

client.on('reconnect', () => {
  state.connected = false;
});

client.on('offline', () => {
  state.connected = false;
  addEvent('status', 'mqtt', 'conexion', { estado: 'offline' });
});

client.on('error', error => {
  state.connected = false;
  addEvent('error', 'mqtt', 'conexion', { mensaje: error.message });
});

client.on('message', (topic, buffer) => {
  const payload = parsePayload(buffer.toString());
  addEvent('receive', 'mqtt', topic, payload);

  if (topic === topics.storageRegister && typeof payload === 'object') {
    upsertInventoryFromStorage(payload);
  }

  if (topic === topics.orderRequest && typeof payload === 'object') {
    if (!pythonBridgeEnabled) {
      processOrder(payload);
    }
  }
});

app.get('/api/state', (_req, res) => {
  res.json(state);
});

app.post('/api/storage/register', (req, res) => {
  const payload = {
    id_evento: `WEB-ALM-${Date.now()}`,
    device_id: 'web-demo-almacen',
    tipo: req.body.tipo,
    cod_barras: req.body.cod_barras,
    posicion: req.body.posicion || currentRackPosition(),
    caducidad: req.body.caducidad,
    cantidad: Number(req.body.cantidad || 1)
  };

  upsertInventoryFromStorage(payload);

  if (!req.body.posicion) {
    advanceRack();
  }

  publishJson(topics.storageRegister, payload);
  publishJson(topics.storageStatus, {
    id_evento: payload.id_evento,
    estado: 'registrado',
    mensaje: `Medicamento guardado en ${payload.posicion}`
  });

  res.json({ ok: true, payload, rack: state.rack });
});

app.post('/api/orders/request', (req, res) => {
  const payload = {
    id_pedido: `WEB-PED-${Date.now()}`,
    device_id: 'web-demo-pedido',
    tipo: req.body.tipo,
    cantidad: Number(req.body.cantidad || 1)
  };

  publishJson(topics.orderRequest, payload);

  if (!pythonBridgeEnabled) {
    processOrder(payload);
  } else {
    addEvent('status', 'python', topics.orderRequest, {
      estado: 'delegado',
      mensaje: 'Pedido enviado al puente Python/SQLite/RoboDK'
    });
  }

  res.json({ ok: true, payload });
});

app.post('/api/rack', (req, res) => {
  const x = Number(req.body.x);
  const y = Number(req.body.y);

  if (!Number.isInteger(x) || !Number.isInteger(y) || x < 1 || y < 1 || x > state.rack.maxX || y > state.rack.maxY) {
    res.status(400).json({ ok: false, error: 'Posicion fuera de rango' });
    return;
  }

  state.rack.x = x;
  state.rack.y = y;
  client.publish(topics.storageCommand, `set_pos ${x} ${y}`);
  addEvent('publish', 'web', topics.storageCommand, `set_pos ${x} ${y}`);

  res.json({ ok: true, rack: state.rack });
});

app.listen(port, '127.0.0.1', () => {
  console.log(`API demo medicamentos en http://127.0.0.1:${port}`);
});
