import React, { useState } from 'react';
import { PenTool, FileCheck, AlertTriangle, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import FileUpload from '@/components/FileUpload';
import CredentialsForm from '@/components/CredentialsForm';
import OTPModal from '@/components/OTPModal';
import { useToast } from '@/hooks/use-toast';
interface CredentialsData {
  cuil: string;
  password: string;
  pin: string;
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
  const [validationErrors, setValidationErrors] = useState<{
    files?: boolean;
    cuil?: boolean;
    password?: boolean;
    pin?: boolean;
  }>({});
  const {
    toast
  } = useToast();
  
  const cleanCUIL = (cuil: string): string => {
    return cuil.replace(/\D/g, '');
  };
  const validateCUIL = (cuil: string): boolean => {
   const cleaned=cleanCUIL(cuil);
    return cleaned.length==11;
    }

  const isFormValid = () => {
    return files.length > 0 && validateCUIL(credentials.cuil) && credentials.password.length >= 1 && credentials.pin.length >= 1;
  };
  const getValidationErrors = () => {
    const errors: typeof validationErrors = {};
    if (files.length === 0) {
      errors.files = true;
    }
    if (!validateCUIL(credentials.cuil)) {
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
  const handleInitialValidation = () => {
    const errors = getValidationErrors();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) {
      const missingFields = [];
      if (errors.files) missingFields.push('archivos PDF');
      if (errors.cuil) missingFields.push('CUIL');
      if (errors.password) missingFields.push('contraseña');
      if (errors.pin) missingFields.push('PIN');
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

    // 1. Aquí va el código para crear el FormData
    const formData = new FormData();
    formData.append('cuit', credentials.cuil);
    formData.append('password', credentials.password);
    formData.append('pin', credentials.pin);
    formData.append('otpCode', otp);
    files.forEach(file => {
        formData.append('files[]', file);
    });

    try {
        // 2. Aquí va la llamada fetch
        const response = await fetch('http://127.0.0.1:5000/firmar', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Error desconocido del servidor.');
        }

        const data = await response.json();
        toast({
            title: "Firma completada exitosamente",
            description: data.message || `Se procesaron ${files.length} archivo(s) para firma digital.`,
            variant: "default"
        });

    } catch (error) {
        console.error('Error al procesar la firma:', error);
        toast({
            title: "Error en el proceso",
            description: `Ocurrió un error: ${error.message}. Intente nuevamente.`,
            variant: "destructive"
        });
    } finally {
        setIsProcessing(false);
        setShowOTPModal(false);
    }
  };

  return <div className="min-h-screen bg-gradient-subtle">
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
                  <p>1. <strong>Cargue archivos PDF</strong> que desea firmar digitalmente (máximo 14MB cada uno)</p>
                  <p>2. <strong>Complete sus credenciales</strong> de la plataforma FirmAR.gob.ar</p>
                  <p>3. <strong>Haga clic en "Firmar"</strong> para procesar todos los documentos</p>
                </div>
              </div>
            </div>
          </Card>

          {/* File Upload Section */}
          <FileUpload files={files} onFilesChange={setFiles} />

          {/* Credentials Form */}
          <CredentialsForm credentials={credentials} onCredentialsChange={setCredentials} validationErrors={validationErrors} />

          {/* Status Summary */}
          

          {/* Action Button */}
          <div className="flex justify-center">
            <Button onClick={handleInitialValidation} disabled={isProcessing} size="lg" className="bg-gradient-primary hover:opacity-90 shadow-medium font-semibold px-8">
              <PenTool className="h-4 w-4 mr-2" />
              Firmar Documentos
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
      
      {/* OTP Modal */}
      <OTPModal isOpen={showOTPModal} onClose={() => setShowOTPModal(false)} onConfirm={handleFinalSign} isProcessing={isProcessing} />
    </div>;
};
export default Index;