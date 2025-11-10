function InstalarCredenciales() {
  const handleGHLRedirect = () => {
    // Aquí pondrás tu link de GHL
    const ghlLink = 'TU_LINK_GHL_AQUI';
    window.location.href = ghlLink;
  };

  const handleMPRedirect = () => {
    // Aquí pondrás tu link de MercadoPago
    const mpLink = 'TU_LINK_MP_AQUI';
    window.location.href = mpLink;
  };

  return (
    <div className="flex items-center justify-center gap-16 w-full h-full p-12">
      <div className="flex-1 flex flex-col items-center justify-between max-w-[400px] h-[500px] p-8">
        <h2 className="text-[1.8rem] font-semibold text-text-primary text-center mb-auto pt-4">
          logearse con GHL
        </h2>
        <button 
          className="px-12 py-5 text-lg font-medium text-text-primary bg-white/5 border-2 border-white rounded-[10px] cursor-pointer transition-all duration-300 min-w-[200px] mt-auto hover:bg-white/10 hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(255,255,255,0.2)]"
          onClick={handleGHLRedirect}
        >
          redirigir
        </button>
      </div>

      <div className="w-0.5 h-[400px] bg-gradient-to-b from-transparent via-white/30 to-transparent"></div>

      <div className="flex-1 flex flex-col items-center justify-between max-w-[400px] h-[500px] p-8">
        <h2 className="text-[1.8rem] font-semibold text-text-primary text-center mb-auto pt-4">
          logearse con MP
        </h2>
        <button 
          className="px-12 py-5 text-lg font-medium text-text-primary bg-white/5 border-2 border-white rounded-[10px] cursor-pointer transition-all duration-300 min-w-[200px] mt-auto hover:bg-white/10 hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(255,255,255,0.2)]"
          onClick={handleMPRedirect}
        >
          redirigir
        </button>
      </div>
    </div>
  );
}

export default InstalarCredenciales;
