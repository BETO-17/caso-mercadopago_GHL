import { useState } from 'react';
import Container from '../../components/Container';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Alert from '../../components/Alert';

function CrearContacto() {
  const [formData, setFormData] = useState({
    nombre: '',
    apellidos: '',
    email: '',
    telefono: ''
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

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El campo nombre es obligatorio';
    }
    if (!formData.apellidos.trim()) {
      newErrors.apellidos = 'El campo apellidos es obligatorio';
    }
    if (!formData.email.trim()) {
      newErrors.email = 'El campo email es obligatorio';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'El formato del email no es válido';
    }
    if (!formData.telefono.trim()) {
      newErrors.telefono = 'El campo teléfono es obligatorio';
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
        message: '¡Contacto creado exitosamente!'
      });

      // Limpiar formulario después de 2 segundos
      setTimeout(() => {
        setFormData({
          nombre: '',
          apellidos: '',
          email: '',
          telefono: ''
        });
      }, 2000);
    } else {
      // Mostrar alerta de error
      setAlert({
        type: 'error',
        message: 'Por favor, completa todos los campos correctamente'
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
          Crear Contacto
        </h1>
        <h2 className="text-6xl font-bold bg-gradient-button bg-clip-text text-transparent">
          Hola Mundo
        </h2>
      </div>

      {/* Contenedor del formulario */}
      <Container className="w-full max-w-2xl" padding="p-10">
        <form onSubmit={handleSubmit} className="space-y-6">
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

          {/* Campo apellidos */}
          <Input
            type="text"
            label="apellidos"
            placeholder="Escribe los apellidos"
            value={formData.apellidos}
            onChange={(e) => handleChange('apellidos', e.target.value)}
            className={errors.apellidos ? 'border-2 border-red-500' : ''}
          />
          {errors.apellidos && (
            <p className="text-red-400 text-sm mt-1">{errors.apellidos}</p>
          )}

          {/* Campo email */}
          <Input
            type="email"
            label="email"
            placeholder="ejemplo@correo.com"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className={errors.email ? 'border-2 border-red-500' : ''}
          />
          {errors.email && (
            <p className="text-red-400 text-sm mt-1">{errors.email}</p>
          )}

          {/* Campo teléfono */}
          <Input
            type="tel"
            label="teléfono"
            placeholder="+51 999 999 999"
            value={formData.telefono}
            onChange={(e) => handleChange('telefono', e.target.value)}
            className={errors.telefono ? 'border-2 border-red-500' : ''}
          />
          {errors.telefono && (
            <p className="text-red-400 text-sm mt-1">{errors.telefono}</p>
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

export default CrearContacto;
