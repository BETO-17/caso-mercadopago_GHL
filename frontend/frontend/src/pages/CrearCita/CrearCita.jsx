import { useState } from 'react';
import Container from '../../components/Container';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Alert from '../../components/Alert';

function CrearCita() {
  const [formData, setFormData] = useState({
    inicio: '',
    fin: '',
    nombre: '',
    contacto: ''
  });
  const [alert, setAlert] = useState(null);
  const [errors, setErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Limpiar error del campo cuando el usuario empieza a escribir
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.inicio.trim()) {
      newErrors.inicio = 'El campo inicio es obligatorio';
    }
    if (!formData.fin.trim()) {
      newErrors.fin = 'El campo fin es obligatorio';
    }
    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El campo nombre es obligatorio';
    }
    if (!formData.contacto.trim()) {
      newErrors.contacto = 'El campo contacto es obligatorio';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateForm()) {
      // Mostrar alerta de éxito
      setAlert({
        type: 'success',
        message: '¡Cita creada exitosamente!'
      });

      // Limpiar formulario después de 2 segundos
      setTimeout(() => {
        setFormData({
          inicio: '',
          fin: '',
          nombre: '',
          contacto: ''
        });
      }, 2000);
    } else {
      // Mostrar alerta de error
      setAlert({
        type: 'error',
        message: 'Por favor, completa todos los campos'
      });
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full min-h-screen bg-bg-main p-8">
      {/* Alerta */}
      {alert && (
        <Alert
          message={alert.message}
          type={alert.type}
          duration={3000}
          onClose={() => setAlert(null)}
        />
      )}

      {/* Títulos */}
      <div className="text-center mb-8">
        <h1 className="text-5xl font-semibold text-text-primary mb-4">
          Crear Cita
        </h1>
        <h2 className="text-6xl font-bold bg-gradient-button bg-clip-text text-transparent">
          Hola Mundo
        </h2>
      </div>

      {/* Contenedor del formulario */}
      <Container className="w-full max-w-2xl" padding="p-10">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Campo inicio */}
          <Input
            type="datetime-local"
            label="inicio"
            placeholder="Selecciona fecha y hora de inicio"
            value={formData.inicio}
            onChange={(e) => handleChange('inicio', e.target.value)}
            className={errors.inicio ? 'border-2 border-red-500' : ''}
          />
          {errors.inicio && (
            <p className="text-red-400 text-sm mt-1">{errors.inicio}</p>
          )}

          {/* Campo fin */}
          <Input
            type="datetime-local"
            label="fin"
            placeholder="Selecciona fecha y hora de fin"
            value={formData.fin}
            onChange={(e) => handleChange('fin', e.target.value)}
            className={errors.fin ? 'border-2 border-red-500' : ''}
          />
          {errors.fin && (
            <p className="text-red-400 text-sm mt-1">{errors.fin}</p>
          )}

          {/* Campo nombre */}
          <Input
            type="text"
            label="nombre"
            placeholder="Escribe el nombre"
            value={formData.nombre}
            onChange={(e) => handleChange('nombre', e.target.value)}
            className={errors.nombre ? 'border-2 border-red-500' : ''}
          />
          {errors.nombre && (
            <p className="text-red-400 text-sm mt-1">{errors.nombre}</p>
          )}

          {/* Campo contacto */}
          <Input
            type="tel"
            label="contacto"
            placeholder="Escribe el contacto"
            value={formData.contacto}
            onChange={(e) => handleChange('contacto', e.target.value)}
            className={errors.contacto ? 'border-2 border-red-500' : ''}
          />
          {errors.contacto && (
            <p className="text-red-400 text-sm mt-1">{errors.contacto}</p>
          )}

          {/* Botón de envío */}
          <div className="flex flex-col items-center gap-4 mt-8">
            <Button
              type="submit"
              className="w-full bg-gradient-button text-text-primary font-semibold py-4 rounded-lg hover:opacity-90 transition-opacity duration-300"
            >
              CREAR
            </Button>
            
            <p className="text-sm text-gray-400 opacity-80">
              Funcionalidad de navegación activa ✓
            </p>
          </div>
        </form>
      </Container>
    </div>
  );
}

export default CrearCita;
