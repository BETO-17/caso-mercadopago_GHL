import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Container from '../../components/Container';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Alert from '../../components/Alert';

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [alert, setAlert] = useState(null);

  // Credenciales simuladas
  const VALID_EMAIL = 'usuario@hotmail.com';
  const VALID_PASSWORD = '123456';

  const handleLogin = (e) => {
    e.preventDefault();

    // Validar campos vacíos
    if (!email || !password) {
      setAlert({
        type: 'error',
        message: 'Por favor, completa todos los campos'
      });
      return;
    }

    // Validar credenciales
    if (email === VALID_EMAIL && password === VALID_PASSWORD) {
      // Guardar token de autenticación
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', email);

      // Mostrar alerta de éxito
      setAlert({
        type: 'success',
        message: '¡Inicio de sesión exitoso! Redirigiendo...'
      });

      // Redirigir al dashboard después de 1.5 segundos
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } else {
      // Mostrar alerta de error
      setAlert({
        type: 'error',
        message: 'Correo o contraseña incorrectos'
      });
    }
  };

  return (
    <div className="min-h-screen w-full bg-bg-main flex items-center justify-center p-6">
      {/* Alerta */}
      {alert && (
        <Alert
          message={alert.message}
          type={alert.type}
          duration={3000}
          onClose={() => setAlert(null)}
        />
      )}

      {/* Contenedor del formulario */}
      <Container className="w-full max-w-md" padding="p-10">
        <form onSubmit={handleLogin} className="space-y-6">
          {/* Título */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-semibold text-text-primary mb-2">
              ¡Hola de nuevo!
            </h1>
            <p className="text-lg text-gray-300 opacity-80">
              ¡Nos alegra mucho volverte a verte!
            </p>
          </div>

          {/* Campo de correo electrónico */}
          <Input
            type="email"
            label="Correo electrónico"
            placeholder="Ejem: Carlos@hotmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {/* Campo de contraseña */}
          <Input
            type="password"
            label="Contraseña"
            placeholder="************"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {/* Botón de ingreso */}
          <Button
            type="submit"
            className="w-full bg-gradient-button text-text-primary font-semibold py-4 rounded-lg hover:opacity-90 transition-opacity duration-300 mt-8"
          >
            Ingresar al sistema
          </Button>

          {/* Información de credenciales (solo para desarrollo) */}
          <div className="mt-6 p-4 bg-bg-main/50 rounded-lg border border-white/10">
            <p className="text-xs text-gray-400 text-center mb-2">Credenciales de prueba:</p>
            <p className="text-xs text-gray-300 text-center">Email: usuario@hotmail.com</p>
            <p className="text-xs text-gray-300 text-center">Contraseña: 123456</p>
          </div>
        </form>
      </Container>
    </div>
  );
}

export default Login;
