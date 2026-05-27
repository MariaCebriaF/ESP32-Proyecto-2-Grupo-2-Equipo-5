import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Bot,
  Boxes,
  Calculator,
  CheckCircle2,
  CircleDot,
  ClipboardList,
  Cpu,
  Database,
  ListPlus,
  PackageSearch,
  Pill,
  RadioTower,
  RefreshCw,
  Search,
  Send,
  Server,
  Settings2,
  ShoppingCart,
  TrendingUp,
  Warehouse
} from 'lucide-react';
import './styles.css';

const emptyStorage = {
  tipo: 'Ibuprofeno',
  cod_barras: '847000100002',
  caducidad: '2027-08-15',
  cantidad: 1,
  posicion: ''
};

const emptyOrder = {
  tipo: 'Ibuprofeno',
  cantidad: 1
};

const medicineCatalog = [
  { tipo: 'Paracetamol', cod_barras: '847000100001', caducidad: '2027-05-01', pvpConIva: 2.8 },
  { tipo: 'Ibuprofeno', cod_barras: '847000100002', caducidad: '2027-08-15', pvpConIva: 3.5 },
  { tipo: 'Enantyum', cod_barras: '847000100003', caducidad: '2027-10-20', pvpConIva: 4.9 }
];

const salesData = [
  { label: 'L', value: 18 },
  { label: 'M', value: 24 },
  { label: 'X', value: 31 },
  { label: 'J', value: 27 },
  { label: 'V', value: 36 },
  { label: 'S', value: 22 }
];

const recentSales = [
  { id: 'V-1042', tipo: 'Ibuprofeno', units: 1, amount: '4,20 EUR' },
  { id: 'V-1041', tipo: 'Paracetamol', units: 2, amount: '7,80 EUR' },
  { id: 'V-1040', tipo: 'Enantyum', units: 1, amount: '5,60 EUR' }
];

const marginProducts = medicineCatalog.map(product => ({
  producto: product.tipo,
  pvpConIva: product.pvpConIva,
  iva: 0.04,
  margen: 0.279,
  categoria: 'Medicamento OTC'
}));

function App() {
  const [state, setState] = useState(null);
  const [storage, setStorage] = useState(emptyStorage);
  const [order, setOrder] = useState(emptyOrder);
  const [rackDraft, setRackDraft] = useState({ x: 1, y: 1 });
  const [selectedView, setSelectedView] = useState('Inventario');

  async function refresh() {
    const response = await fetch('/api/state');
    const data = await response.json();
    setState(data);
    setRackDraft({ x: data.rack.x, y: data.rack.y });
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 1500);
    return () => clearInterval(timer);
  }, []);

  const currentPosition = useMemo(() => {
    if (!state) return 'X--Y--';
    return `X${String(state.rack.x).padStart(2, '0')}-Y${String(state.rack.y).padStart(2, '0')}`;
  }, [state]);

  const totalStock = useMemo(() => {
    if (!state) return 0;
    return state.inventory.reduce((sum, item) => sum + Number(item.stock || 0), 0);
  }, [state]);

  const lowStock = useMemo(() => {
    if (!state) return 0;
    return state.inventory.filter(item => Number(item.stock || 0) <= 1).length;
  }, [state]);

  async function submitStorage(event) {
    event.preventDefault();
    await fetch('/api/storage/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(storage)
    });
    setStorage(current => ({ ...current, posicion: '' }));
    refresh();
  }

  async function submitOrder(event) {
    event.preventDefault();
    await fetch('/api/orders/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    });
    refresh();
  }

  async function syncRack(event) {
    event.preventDefault();
    await fetch('/api/rack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rackDraft)
    });
    refresh();
  }

  if (!state) {
    return <div className="loading">Cargando demo...</div>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Pill size={19} /></div>
          <div>
            <strong>PR2 Med</strong>
            <span>Grupo 2 Equipo 5</span>
          </div>
        </div>

        <nav>
          {[
            ['Inventario', Database],
            ['Alta', ListPlus],
            ['Pedidos', PackageSearch],
            ['Eventos', Activity]
          ].map(([label, Icon]) => (
            <button
              className={selectedView === label ? 'nav-item active' : 'nav-item'}
              key={label}
              onClick={() => setSelectedView(label)}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-status">
          <span className={state.connected ? 'dot online' : 'dot'} />
          <div>
            <strong>{state.connected ? 'MQTT conectado' : 'MQTT sin conexion'}</strong>
            <span>{state.baseTopic}</span>
          </div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div className="title-block">
            <span className="breadcrumb">Dashboard / Farmacia automatizada</span>
            <h1>Buenos dias</h1>
            <p>Control de ventas, inventario y control del server con MQTT</p>
          </div>
          <div className="topbar-actions">
            <label className="search-box">
              <Search size={16} />
              <input placeholder="Buscar medicamento o posicion..." />
            </label>
            <div className={state.connected ? 'connection-pill connected' : 'connection-pill'}>
              <RadioTower size={17} />
              {state.connected ? 'HiveMQ conectado' : 'MQTT desconectado'}
            </div>
            <button className="icon-button" onClick={refresh} title="Actualizar estado">
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        <section className="metric-row">
          <Metric icon={ShoppingCart} label="Ventas hoy" value="128" helper="+12% vs ayer" tone="teal" />
          <Metric icon={Boxes} label="Stock total" value={totalStock} helper={`${state.inventory.length} medicamentos`} tone="mint" />
          <Metric icon={Warehouse} label="Siguiente posicion" value={currentPosition} helper="cursor ESP32" tone="dark" />
          <Metric icon={CheckCircle2} label="Alertas stock" value={lowStock} helper="stock <= 1" tone="amber" />
        </section>

        <section className="dashboard-grid">
          <div className="main-column">
            <section className="system-flow">
              <FlowStep icon={Cpu} label="ESP32 alta" value="registro MQTT" />
              <FlowStep icon={RadioTower} label="Broker MQTT" value="broker.hivemq.com" active={state.connected} />
              <FlowStep icon={Server} label="Backend web" value="Postgres ready" />
              <FlowStep icon={Bot} label="RoboDK" value="siguiente fase" />
            </section>

            <div className="analytics-grid">
              <Panel title="Ventas e inventario" icon={TrendingUp} className="sales-panel">
                <SalesOverview />
              </Panel>
              <Panel title="Mapa de estanteria" icon={Warehouse} className="rack-map-panel">
                <RackMap rack={state.rack} />
              </Panel>
            </div>

            <Panel title="Rentabilidad de farmacia" icon={Calculator} className="profit-panel">
              <ProfitSimulator />
            </Panel>

            <Panel title="Inventario" icon={Database} className="inventory-panel">
              <InventoryTable items={state.inventory} />
            </Panel>
          </div>

          <aside className="right-column">
            <Panel title="Alta de medicamento" icon={ListPlus} className="accent-panel teal-panel">
              <form className="form-stack" onSubmit={submitStorage}>
                <Field label="Tipo">
                  <MedicineButtons
                    selected={storage.tipo}
                    onSelect={medicine => setStorage({
                      ...storage,
                      tipo: medicine.tipo,
                      cod_barras: medicine.cod_barras,
                      caducidad: medicine.caducidad
                    })}
                  />
                </Field>
                <Field label="Codigo de barras">
                  <input value={storage.cod_barras} onChange={event => setStorage({ ...storage, cod_barras: event.target.value })} />
                </Field>
                <div className="two-col">
                  <Field label="Caducidad">
                    <input type="date" value={storage.caducidad} onChange={event => setStorage({ ...storage, caducidad: event.target.value })} />
                  </Field>
                  <Field label="Cantidad">
                    <input type="number" min="1" value={storage.cantidad} onChange={event => setStorage({ ...storage, cantidad: event.target.value })} />
                  </Field>
                </div>
                <Field label="Posicion manual">
                  <input placeholder={currentPosition} value={storage.posicion} onChange={event => setStorage({ ...storage, posicion: event.target.value })} />
                </Field>
                <button className="primary-button" type="submit">
                  <Send size={16} />
                  Registrar alta
                </button>
              </form>
            </Panel>

            <Panel title="Solicitud de medicamento" icon={PackageSearch} className="accent-panel amber-panel">
              <form className="form-stack" onSubmit={submitOrder}>
                <Field label="Tipo solicitado">
                  <MedicineButtons
                    selected={order.tipo}
                    onSelect={medicine => setOrder({ ...order, tipo: medicine.tipo })}
                  />
                </Field>
                <Field label="Cantidad">
                  <input type="number" min="1" value={order.cantidad} onChange={event => setOrder({ ...order, cantidad: event.target.value })} />
                </Field>
                <button className="primary-button amber" type="submit">
                  <PackageSearch size={16} />
                  Solicitar al sistema
                </button>
              </form>
            </Panel>

            <Panel title="Sincronizacion RoboDK" icon={Settings2} className="rack-panel">
              <form className="rack-sync" onSubmit={syncRack}>
                <div className="rack-position">{currentPosition}</div>
                <div className="two-col">
                  <Field label="X">
                    <input type="number" min="1" max={state.rack.maxX} value={rackDraft.x} onChange={event => setRackDraft({ ...rackDraft, x: event.target.value })} />
                  </Field>
                  <Field label="Y">
                    <input type="number" min="1" max={state.rack.maxY} value={rackDraft.y} onChange={event => setRackDraft({ ...rackDraft, y: event.target.value })} />
                  </Field>
                </div>
                <button className="secondary-button" type="submit">Ajustar contador ESP32</button>
              </form>
            </Panel>

            <Panel title="Eventos en vivo" icon={Activity} className="events-panel">
              <EventList events={state.events} />
            </Panel>
          </aside>
        </section>
      </main>
    </div>
  );
}

function FlowStep({ icon: Icon, label, value, active = false }) {
  return (
    <div className={active ? 'flow-step active' : 'flow-step'}>
      <span className="flow-icon"><Icon size={18} /></span>
      <div>
        <strong>{label}</strong>
        <span>{value}</span>
      </div>
      <CircleDot size={16} className="flow-dot" />
    </div>
  );
}

function Metric({ icon: Icon, label, value, helper, tone = 'teal' }) {
  return (
    <div className={`metric ${tone}`}>
      <div className="metric-icon"><Icon size={20} /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {helper && <small>{helper}</small>}
      </div>
    </div>
  );
}

function Panel({ title, icon: Icon, children, className = '' }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-title">
        <Icon size={17} />
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function MedicineButtons({ selected, onSelect }) {
  return (
    <div className="medicine-buttons">
      {medicineCatalog.map(medicine => (
        <button
          className={selected === medicine.tipo ? 'medicine-option active' : 'medicine-option'}
          key={medicine.tipo}
          onClick={() => onSelect(medicine)}
          type="button"
        >
          <Pill size={15} />
          {medicine.tipo}
        </button>
      ))}
    </div>
  );
}

function SalesOverview() {
  const max = Math.max(...salesData.map(day => day.value));

  return (
    <div className="sales-overview">
      <div className="sales-total">
        <span>Ingresos simulados</span>
        <strong>1.284 EUR</strong>
        <small>Datos mock, listo para Postgres</small>
      </div>
      <div className="bar-chart">
        {salesData.map(day => (
          <div className="bar-item" key={day.label}>
            <div className="bar-track">
              <span style={{ height: `${(day.value / max) * 100}%` }} />
            </div>
            <small>{day.label}</small>
          </div>
        ))}
      </div>
      <div className="sales-list">
        {recentSales.map(sale => (
          <div className="sale-row" key={sale.id}>
            <span><ClipboardList size={14} /> {sale.id}</span>
            <strong>{sale.tipo}</strong>
            <small>{sale.units} ud. · {sale.amount}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProfitSimulator() {
  const [monthlyCosts, setMonthlyCosts] = useState({
    facturacion: 30000,
    local: 2200,
    personal: 5600,
    suministros: 900,
    otros: 500,
    stockRate: 0.68,
    margenMedio: 0.279
  });

  const computed = useMemo(() => {
    const fixedCosts = Number(monthlyCosts.local) + Number(monthlyCosts.personal) + Number(monthlyCosts.suministros) + Number(monthlyCosts.otros);
    const stockCost = Number(monthlyCosts.facturacion) * Number(monthlyCosts.stockRate);
    const grossProfit = Number(monthlyCosts.facturacion) * Number(monthlyCosts.margenMedio);
    const netProfit = grossProfit - fixedCosts;
    const breakEven = fixedCosts / Number(monthlyCosts.margenMedio || 1);

    return { fixedCosts, stockCost, grossProfit, netProfit, breakEven };
  }, [monthlyCosts]);

  function updateCost(key, value) {
    setMonthlyCosts(current => ({ ...current, [key]: Number(value) }));
  }

  return (
    <div className="profit-grid">
      <div className="profit-summary">
        <div>
          <span>Beneficio neto estimado</span>
          <strong>{formatEuro(computed.netProfit)}</strong>
          <small>Modelo mensual simulado</small>
        </div>
        <div className="profit-ring">
          <span>{Math.round((computed.netProfit / Number(monthlyCosts.facturacion)) * 100)}%</span>
        </div>
      </div>

      <div className="cost-controls">
        <CostInput label="Facturacion mensual" value={monthlyCosts.facturacion} onChange={value => updateCost('facturacion', value)} />
        <CostInput label="Local" value={monthlyCosts.local} onChange={value => updateCost('local', value)} />
        <CostInput label="Personal" value={monthlyCosts.personal} onChange={value => updateCost('personal', value)} />
        <CostInput label="Suministros" value={monthlyCosts.suministros} onChange={value => updateCost('suministros', value)} />
        <CostInput label="Otros" value={monthlyCosts.otros} onChange={value => updateCost('otros', value)} />
      </div>

      <div className="profit-kpis">
        <div><span>Costes fijos</span><strong>{formatEuro(computed.fixedCosts)}</strong></div>
        <div><span>Compra stock</span><strong>{formatEuro(computed.stockCost)}</strong></div>
        <div><span>Margen bruto</span><strong>{formatEuro(computed.grossProfit)}</strong></div>
        <div><span>Punto equilibrio</span><strong>{formatEuro(computed.breakEven)}</strong></div>
      </div>

      <div className="margin-table">
        {marginProducts.map(product => {
          const pvpSinIva = product.pvpConIva / (1 + product.iva);
          const beneficioBruto = pvpSinIva * product.margen;
          const costeCompra = pvpSinIva - beneficioBruto;

          return (
            <div className="margin-row" key={product.producto}>
              <strong>{product.producto}</strong>
              <span>{product.categoria}</span>
              <code>{formatEuro(beneficioBruto)} beneficio</code>
              <small>PVP sin IVA {formatEuro(pvpSinIva)} · coste {formatEuro(costeCompra)}</small>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CostInput({ label, value, onChange }) {
  return (
    <label className="cost-input">
      <span>{label}</span>
      <input type="number" min="0" value={value} onChange={event => onChange(event.target.value)} />
    </label>
  );
}

function formatEuro(value) {
  return `${Number(value || 0).toLocaleString('es-ES', { maximumFractionDigits: 0 })} EUR`;
}

function RackMap({ rack }) {
  const cells = [];
  for (let x = 1; x <= rack.maxX; x++) {
    for (let y = 1; y <= rack.maxY; y++) {
      const active = x === Number(rack.x) && y === Number(rack.y);
      cells.push({ x, y, active, label: `X${String(x).padStart(2, '0')}-Y${String(y).padStart(2, '0')}` });
    }
  }

  return (
    <div className="rack-map">
      {cells.map(cell => (
        <div className={cell.active ? 'rack-cell active' : 'rack-cell'} key={cell.label}>
          {cell.label}
        </div>
      ))}
    </div>
  );
}

function InventoryTable({ items }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Codigo</th>
            <th>Posicion</th>
            <th>Caducidad</th>
            <th>Stock</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={`${item.tipo}-${item.posicion}`}>
              <td>{item.tipo}</td>
              <td>{item.cod_barras}</td>
              <td><code>{item.posicion}</code></td>
              <td>{item.caducidad}</td>
              <td>{item.stock}</td>
              <td><span className={`status-chip ${item.estado}`}>{item.estado}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EventList({ events }) {
  return (
    <div className="event-list">
      {events.length === 0 && <p className="empty">Sin eventos todavia.</p>}
      {events.map(event => (
        <article className="event-row" key={event.id}>
          <time>{event.time}</time>
          <span className={`event-kind ${event.type}`}>{event.type}</span>
          <div>
            <strong>{event.topic}</strong>
            <pre>{typeof event.payload === 'string' ? event.payload : JSON.stringify(event.payload, null, 2)}</pre>
          </div>
        </article>
      ))}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
