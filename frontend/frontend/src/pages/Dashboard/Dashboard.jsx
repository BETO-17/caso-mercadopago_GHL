import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import InstalarCredenciales from '../InstalarCredenciales/InstalarCredenciales';
import CrearCita from '../CrearCita/CrearCita';
import CrearContacto from '../CrearContacto/CrearContacto';

function Dashboard() {
  return (
    <div className="flex w-full min-h-screen bg-bg-main">
      <Sidebar />
      <main className="flex-1 ml-60 min-h-screen flex flex-col bg-bg-main">
        <Routes>
          <Route path="/" element={<Navigate to="instalar-credenciales" replace />} />
          <Route path="instalar-credenciales" element={<InstalarCredenciales />} />
          <Route path="crear-cita" element={<CrearCita />} />
          <Route path="crear-contacto" element={<CrearContacto />} />
        </Routes>
      </main>
    </div>
  );
}

export default Dashboard;
