import React, { useState, useEffect } from 'react';
import { PenTool, FileCheck, AlertTriangle, Shield, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import FileUpload from '@/components/FileUpload';
import CredentialsForm from '@/components/CredentialsForm';
import OTPModal from '@/components/OTPModal';
import CompletionModal from '@/components/CompletionModal';
import UserValidationModal from '@/components/UserValidationModal';
import ProgressModal from '@/components/ProgressModal';
import { useToast } from '@/hooks/use-toast';

interface CredentialsData {
  cuil: string;
  password: string;
  pin: string;
}

interface UserData {
  cuil: string;
  responsable: string;
  path_carpetas: string;
}

const Index = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [credentials, setCredentials] = useState<CredentialsData>({
    cuil: '',
    password: '',
    pin: ''
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [showUserValidationModal, setShowUserValidationModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{
    files?: boolean;
    cuil?: boolean;
    password?: boolean;
    pin?: boolean;
  }>({});

  // Estados adicionales para la barra de progreso
  const [sessionId, setSessionId] = useState<string>('');
  const [currentFile, setCurrentFile] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [currentFileName, setCurrentFileName] = useState('');
  const [progressMessage, setProgressMessage] = useState('');
  const [progressInterval, setProgressInterval] = useState<NodeJS.Timeout | null>(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [successfullyProcessed, setSuccessfullyProcessed] = useState(0);

  // NUEVOS ESTADOS para validación de usuarios
  const [userValidated, setUserValidated] = useState(false);
  const [userValidationMessage, setUserValidationMessage] = useState('');
  const [userData, setUserData] = useState<UserData | null>(null);
  const [isValidatingUser, setIsValidatingUser] = useState(false);

  // Estado removido - no necesitamos mensajes persistentes

  const { toast } = useToast();

  const validateCUIL = (cuil: string): boolean => {
    const numeric = cuil.replace(/\D/g, '');
    return numeric.length === 11;
  };

  // NUEVA FUNCIÓN: Validar usuario cuando cambie el CUIL
  const validateUserByCUIL = async (cuil: string) => {
    if (!cuil || cuil.length < 8) {
      setUserValidated(false);
      setUserValidationMessage('');
      setUserData(null);
      return;
    }

    // Solo validar si el CUIL tiene formato válido
    if (!validateCUIL(cuil)) {
      setUserValidated(false);
      setUserValidationMessage('');
      setUserData(null);
      return;
    }

    setIsValidatingUser(true);
    setShowUserValidationModal(true); // MOSTRAR MODAL AL INICIAR VALIDACIÓN
    
    try {
      const response = await fetch('http://127.0.0.1:5000/validate-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cuil: cuil.replace(/\D/g, '') }),
      });

      const data = await response.json();

      if (data.valid) {
        setUserValidated(true);
        setUserValidationMessage(`Usuario autorizado: ${data.user_data.responsable}`);
        setUserData(data.user_data);

        
        // El modal permanece abierto mostrando el éxito
        toast({
          title: "Usuario autorizado",
          description: `Bienvenido ${data.user_data.responsable}`,
        });
      } else {
        setUserValidated(false);
        setUserValidationMessage(data.message);
        setUserData(null);

        
        // El modal permanece abierto mostrando el error
        toast({
          title: "Acceso denegado",
          description: data.message,
          variant: "destructive"
        });
      }
    } catch (error) {
      setUserValidated(false);
      setUserValidationMessage('Error de conexión con el servidor');
      setUserData(null);

      
      toast({
        title: "Error de conexión",
        description: "No se pudo validar el usuario",
        variant: "destructive"
      });
    } finally {
      setIsValidatingUser(false);
      // El modal se queda abierto hasta que el usuario haga clic en cerrar
    }
  };

  // MODIFICAR: La función isFormValid ahora incluye validación del usuario
  const isFormValid = () => {
    return files.length > 0 && 
           validateCUIL(credentials.cuil) && 
           credentials.password.length >= 1 && 
           credentials.pin.length >= 1 &&
           userValidated; // NUEVA CONDICIÓN
  };

  // MODIFICAR: getValidationErrors ahora incluye validación de usuario
  const getValidationErrors = () => {
    const errors: typeof validationErrors = {};
    if (files.length === 0) {
      errors.files = true;
    }
    if (!validateCUIL(credentials.cuil)) {
      errors.cuil = true;
    }
    if (!userValidated && credentials.cuil.length >= 8) {
      errors.cuil = true;
    }
    if (credentials.password.length < 1) {
      errors.password = true;
    }
    if (credentials.pin.length < 1) {
      errors.pin = true;
    }
    return errors;
  };

  // MODIFICAR: Manejar cambios en credenciales y validar usuario automáticamente
  const handleCredentialsChange = (newCredentials: CredentialsData) => {
    const oldCuil = credentials.cuil;
    setCredentials(newCredentials);
    
    // Si el CUIL cambió y tiene al menos 8 caracteres, validar usuario
    if (newCredentials.cuil !== oldCuil && newCredentials.cuil.length >= 8) {
      // Resetear estado de validación
      setUserValidated(false);
      setUserValidationMessage('');
      setUserData(null);

      
      // Validar después de un pequeño delay para evitar muchas llamadas
      setTimeout(() => {
        validateUserByCUIL(newCredentials.cuil);
      }, 500);
    }
    
    // Si el CUIL se borró o es muy corto, resetear validación
    if (newCredentials.cuil.length < 8) {
      setUserValidated(false);
      setUserValidationMessage('');
      setUserData(null);

      setShowUserValidationModal(false); // CERRAR MODAL SI CUIL ES MUY CORTO
    }
  };

  // Función para consultar progreso
  const checkProgress = async (sessionId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/progress/${sessionId}`);
      const data = await response.json();
      
      setCurrentFile(data.current);
      setTotalFiles(data.total);
      setCurrentFileName(data.current_file);
      setProgressMessage(data.message);
      
      if (data.status === 'completed') {
        setIsProcessing(false);
        setShowProgressModal(false); // CERRAR MODAL DE PROGRESO
        
        if (progressInterval) {
          clearInterval(progressInterval);
          setProgressInterval(null);
        }
        
        // Guardar el número de archivos procesados exitosamente
        setSuccessfullyProcessed(data.current || files.length);
        
        // Mostrar modal de finalización
        setShowCompletionModal(true);

        // Limpiar la sesión en el servidor
        fetch(`http://127.0.0.1:5000/cleanup/${sessionId}`, { method: 'DELETE' });
        
      } else if (data.status === 'error') {
        setIsProcessing(false);
        setShowProgressModal(false); // CERRAR MODAL DE PROGRESO EN ERROR
        
        if (progressInterval) {
          clearInterval(progressInterval);
          setProgressInterval(null);
        }
        
        toast({
          title: "Error en el proceso",
          description: data.message,
          variant: "destructive"
        });

        // Limpiar la sesión en el servidor
        fetch(`http://127.0.0.1:5000/cleanup/${sessionId}`, { method: 'DELETE' });
      }
    } catch (error) {
      console.error('Error checking progress:', error);
      toast({
        title: "Error de conexión",
        description: "No se pudo obtener el estado del proceso.",
        variant: "destructive"
      });
    }
  };

  const handleInitialValidation = () => {
    const errors = getValidationErrors();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) {
      const missingFields = [];
      if (errors.files) missingFields.push('archivos PDF');
      if (errors.cuil) missingFields.push('CUIL válido');
      if (errors.password) missingFields.push('contraseña');
      if (errors.pin) missingFields.push('PIN');
      
      // Mensaje específico si no está autorizado
      if (!userValidated && credentials.cuil.length >= 8) {
        toast({
          title: "Usuario no autorizado",
          description: "Debe ser un usuario autorizado para utilizar el sistema.",
          variant: "destructive"
        });
        return;
      }
      
      toast({
        title: "Formulario incompleto",
        description: `Complete los siguientes campos: ${missingFields.join(', ')}.`,
        variant: "destructive"
      });
      return;
    }

    // Clear errors and show OTP modal
    setValidationErrors({});
    setShowOTPModal(true);
  };

  const handleFinalSign = async (otp: string) => {
    setIsProcessing(true);
    setShowProgressModal(true); // MOSTRAR MODAL DE PROGRESO
    setTotalFiles(files.length);
    setCurrentFile(0);
    setProgressMessage('Preparando proceso...');

    const formData = new FormData();
    formData.append('cuit', credentials.cuil);
    formData.append('password', credentials.password);
    formData.append('pin', credentials.pin);
    formData.append('otpCode', otp);
    files.forEach(file => {
      formData.append('files[]', file);
    });

    try {
      const response = await fetch('http://127.0.0.1:5000/firmar', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Error desconocido del servidor.');
      }

      const data = await response.json();
      const newSessionId = data.session_id;
      setSessionId(newSessionId);

      // Iniciar polling del progreso cada segundo
      const interval = setInterval(() => {
        checkProgress(newSessionId);
      }, 1000);
      setProgressInterval(interval);

      toast({
        title: "Proceso iniciado",
        description: `Archivos serán guardados en: ${userData?.path_carpetas}`,
      });

    } catch (error: any) {
      console.error('Error al procesar la firma:', error);
      setIsProcessing(false);
      setShowProgressModal(false); // CERRAR MODAL SI HAY ERROR
      
      toast({
        title: "Error en el proceso",
        description: `Ocurrió un error: ${error.message}. Intente nuevamente.`,
        variant: "destructive"
      });
    } finally {
      setShowOTPModal(false);
    }
  };

  // Funciones para manejar el modal de finalización
  const handleFinishProcess = async () => {
    try {
      await fetch('http://127.0.0.1:5000/finish', { method: 'POST' });
      
      // Solo cerrar la pestaña del navegador (sin Electron)
      window.close();

    } catch (error) {
      console.error('Error al finalizar:', error);
      toast({
        title: "Error",
        description: "No se pudo finalizar correctamente el proceso.",
        variant: "destructive"
      });
    }
  };

  const handleLoadMoreFiles = async () => {
    try {
      await fetch('http://127.0.0.1:5000/reset', { method: 'POST' });
      
      // Limpiar todos los estados del frontend
      setFiles([]);
      setCredentials({ cuil: '', password: '', pin: '' });
      setIsProcessing(false);
      setShowOTPModal(false);
      setShowCompletionModal(false);
      setShowUserValidationModal(false); // CERRAR MODAL DE VALIDACIÓN
      setShowProgressModal(false); // CERRAR MODAL DE PROGRESO
      setSessionId('');
      setCurrentFile(0);
      setTotalFiles(0);
      setCurrentFileName('');
      setProgressMessage('');
      setValidationErrors({});
      setSuccessfullyProcessed(0);
      
      // RESETEAR estados de validación de usuario
      setUserValidated(false);
      setUserValidationMessage('');
      setUserData(null);

      
      if (progressInterval) {
        clearInterval(progressInterval);
        setProgressInterval(null);
      }
      
      toast({
        title: "Sistema reiniciado",
        description: "Puede cargar nuevos archivos para procesar.",
      });
      
    } catch (error) {
      console.error('Error al reiniciar:', error);
      toast({
        title: "Error",
        description: "No se pudo reiniciar el sistema correctamente.",
        variant: "destructive"
      });
    }
  };

  // Limpiar intervalo cuando el componente se desmonte
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="bg-gradient-primary shadow-medium">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-white/20 rounded-full">
              <PenTool className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">
                Firma Masiva Digital
              </h1>
              <p className="text-white/90 mt-2">
                Sistema de firma digital para múltiples documentos PDF
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Instructions Card */}
          <Card className="p-6 shadow-soft">
            <div className="flex items-start space-x-4">
              <div className="p-2 bg-secondary/10 rounded-full flex-shrink-0">
                <FileCheck className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground mb-2">
                  Instrucciones de uso
                </h2>
                <div className="text-sm text-muted-foreground space-y-2">
                  <p>1. <strong>Ingrese su CUIL</strong> para validar que está autorizado</p>
                  <p>2. <strong>Cargue archivos PDF</strong> que desea firmar digitalmente (máximo 14MB cada uno)</p>
                  <p>3. <strong>Complete sus credenciales</strong> de la plataforma FirmAR.gob.ar</p>
                  <p>4. <strong>Haga clic en "Firmar"</strong> para procesar todos los documentos</p>
                </div>
              </div>
            </div>
          </Card>

          {/* File Upload Section */}
          <FileUpload files={files} onFilesChange={setFiles} />

          {/* Credentials Form */}
          <CredentialsForm 
            credentials={credentials} 
            onCredentialsChange={handleCredentialsChange}
            validationErrors={validationErrors} 
          />

          

          {/* SIN mensajes de error persistentes - solo modal */}

          {/* Action Button - MODIFICADO para mostrar estado de validación */}
          <div className="flex justify-center">
            <Button 
              onClick={handleInitialValidation} 
              disabled={isProcessing || !userValidated || isValidatingUser} 
              size="lg" 
              className={`${
                userValidated && !isProcessing 
                  ? 'bg-gradient-primary hover:opacity-90' 
                  : 'bg-gray-400 cursor-not-allowed'
              } shadow-medium font-semibold px-8`}
            >
              <PenTool className="h-4 w-4 mr-2" />
              {isProcessing 
                ? 'Procesando...' 
                : isValidatingUser 
                  ? 'Validando usuario...'
                  : userValidated 
                    ? 'Firmar Documentos' 
                    : 'Usuario no autorizado'
              }
            </Button>
          </div>

          {/* Footer Info */}
          <Card className="p-4 bg-accent/50">
            <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
              <Shield className="h-4 w-4" />
              <span>Conexión segura • Sus credenciales se procesan de forma encriptada</span>
            </div>
          </Card>
        </div>
      </main>
      
      {/* CompletionModal */}
      <CompletionModal 
        isOpen={showCompletionModal}
        totalProcessed={successfullyProcessed}
        userPath={userData?.path_carpetas}
        onFinish={handleFinishProcess}
        onLoadMore={handleLoadMoreFiles}
      />
      
      {/* OTP Modal */}
      <OTPModal 
        isOpen={showOTPModal} 
        onClose={() => setShowOTPModal(false)} 
        onConfirm={handleFinalSign} 
        isProcessing={isProcessing} 
      />

      {/* Modal de Validación de Usuario */}
      <UserValidationModal
        isOpen={showUserValidationModal}
        isValidating={isValidatingUser}
        isValid={userValidated}
        message={userValidationMessage}
        userData={userData}
        onClose={() => setShowUserValidationModal(false)}
      />

      {/* Modal de Progreso */}
      <ProgressModal
        isOpen={showProgressModal}
        currentFile={currentFile}
        totalFiles={totalFiles}
        currentFileName={currentFileName}
        progressMessage={progressMessage}
        responsable={userData?.responsable}
      />
    </div>
  );
};

export default Index;