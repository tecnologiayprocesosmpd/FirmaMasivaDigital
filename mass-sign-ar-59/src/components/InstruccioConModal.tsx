import React, { useState } from 'react';
import { FileCheck, X, User, Upload, Shield, PenTool, CheckCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const InstruccionesModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-full">
                <FileCheck className="h-6 w-6 text-blue-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-800">
                Instrucciones de Uso - Firma Digital
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Pasos */}
          <div className="space-y-6">
            
            {/* Paso 1 */}
            <Card className="p-6 border-l-4 border-l-blue-500">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-blue-100 rounded-full flex-shrink-0">
                  <User className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    1. Ingrese su CUIL
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Complete su CUIL en el formato XX-XXXXXXXX-X para validar que está autorizado a usar el sistema.
                  </p>
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="flex items-center space-x-2 text-sm text-blue-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>El sistema validará automáticamente sus permisos</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Paso 2 */}
            <Card className="p-6 border-l-4 border-l-green-500">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-green-100 rounded-full flex-shrink-0">
                  <Upload className="w-6 h-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    2. Cargue archivos PDF
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Seleccione los documentos PDF que desea firmar digitalmente.
                  </p>
                  <div className="bg-green-50 p-3 rounded-lg space-y-2">
                    <div className="flex items-center space-x-2 text-sm text-green-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Máximo 14MB por archivo</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-green-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Solo archivos PDF válidos</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-green-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Puede cargar múltiples archivos a la vez</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Paso 3 */}
            <Card className="p-6 border-l-4 border-l-orange-500">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-orange-100 rounded-full flex-shrink-0">
                  <Shield className="w-6 h-6 text-orange-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    3. Complete sus credenciales
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Ingrese sus credenciales de la plataforma FirmAR.gob.ar
                  </p>
                  <div className="bg-orange-50 p-3 rounded-lg space-y-2">
                    <div className="flex items-center space-x-2 text-sm text-orange-800">
                      <CheckCircle className="w-4 h-4" />
                      <span><strong>CUIL:</strong> Su número de identificación</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-orange-800">
                      <CheckCircle className="w-4 h-4" />
                      <span><strong>Contraseña:</strong> Su clave de FirmAR</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-orange-800">
                      <CheckCircle className="w-4 h-4" />
                      <span><strong>PIN:</strong> Su código PIN de seguridad</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Paso 4 */}
            <Card className="p-6 border-l-4 border-l-purple-500">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-purple-100 rounded-full flex-shrink-0">
                  <PenTool className="w-6 h-6 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    4. Firme sus documentos
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Una vez completados todos los campos, haga clic en "Firmar Documentos"
                  </p>
                  <div className="bg-purple-50 p-3 rounded-lg space-y-2">
                    <div className="flex items-center space-x-2 text-sm text-purple-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Se procesarán todos los archivos automáticamente</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-purple-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Podrá ver el progreso en tiempo real</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-purple-800">
                      <CheckCircle className="w-4 h-4" />
                      <span>Los archivos firmados se guardarán automáticamente</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

          </div>

          {/* Información adicional */}
          <Card className="mt-6 p-4 bg-gray-50">
            <div className="flex items-center space-x-2 mb-2">
              <Shield className="w-5 h-5 text-gray-600" />
              <h4 className="font-semibold text-gray-800">Información Adicional</h4>
            </div>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Sus credenciales se procesan de forma encriptada</li>
              <li>• Solo usuarios autorizados pueden acceder al sistema</li>
              <li>• Ante cualquier inconveniente comunicarse con el área de sistemas</li>           
            </ul>
          </Card>

          {/* Botón cerrar */}
          <div className="flex justify-center mt-6">
            <Button 
              onClick={onClose}
              className="px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Entendido
            </Button>
          </div>

        </div>
      </div>
    </div>
  );
};

// Componente principal que incluye el botón y el modal
const InstruccionesConModal = () => {
  const [modalAbierto, setModalAbierto] = useState(false);

  return (
    <>
      {/* Reemplazar la Card de instrucciones existente con este botón */}
      <Card className="p-6 shadow-soft">
        <div className="flex items-center justify-between">
          <div className="flex items-start space-x-4">
            <div className="p-2 bg-secondary/10 rounded-full flex-shrink-0">
              <FileCheck className="h-5 w-5 text-secondary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Instrucciones de uso
              </h2>
              <p className="text-sm text-muted-foreground">
                Aprenda cómo usar el sistema de firma digital paso a paso
              </p>
            </div>
          </div>
          <Button 
            onClick={() => setModalAbierto(true)}
            variant="outline"
            className="flex-shrink-0"
          >
            Ver Instrucciones
          </Button>
        </div>
      </Card>

      {/* Modal */}
      <InstruccionesModal 
        isOpen={modalAbierto} 
        onClose={() => setModalAbierto(false)} 
      />
    </>
  );
};

export default InstruccionesConModal;