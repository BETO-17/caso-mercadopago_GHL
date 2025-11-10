import { NavLink, useNavigate } from 'react-router-dom';

function Sidebar() {
  const navigate = useNavigate();
  const baseButtonClasses = "flex items-center justify-center px-6 py-4 border-2 rounded-[10px] text-text-primary text-base font-medium text-center transition-all duration-300 cursor-pointer no-underline min-h-[60px]";
  const inactiveClasses = "border-white/30 bg-transparent hover:border-white hover:-translate-y-0.5";
  const activeClasses = "bg-gradient-button border-transparent shadow-[0_4px_12px_rgba(11,169,217,0.3)]";

  const handleLogout = () => {
    // Limpiar autenticación del localStorage
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('userEmail');
    
    // Redirigir al login
    navigate('/login');
  };

  return (
    <aside className="fixed left-0 top-0 w-60 h-screen bg-bg-sidebar p-8 px-6 z-[100]">
      <nav className="flex flex-col gap-6">
        <NavLink 
          to="/dashboard/instalar-credenciales" 
          className={({ isActive }) => `${baseButtonClasses} ${isActive ? activeClasses : inactiveClasses}`}
        >
          iniciar credenciales
        </NavLink>
        
        <NavLink 
          to="/dashboard/crear-cita" 
          className={({ isActive }) => `${baseButtonClasses} ${isActive ? activeClasses : inactiveClasses}`}
        >
          crear cita
        </NavLink>
        
        <NavLink 
          to="/dashboard/crear-contacto" 
          className={({ isActive }) => `${baseButtonClasses} ${isActive ? activeClasses : inactiveClasses}`}
        >
          crear contacto
        </NavLink>
        
        <button 
          onClick={handleLogout}
          className={`${baseButtonClasses} ${inactiveClasses} hover:bg-red-500/10 hover:border-red-400`}
        >
          cerrar sesión
        </button>
      </nav>
    </aside>
  );
}

export default Sidebar;
