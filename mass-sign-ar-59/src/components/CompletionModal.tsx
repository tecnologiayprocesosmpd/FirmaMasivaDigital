import React from 'react';
import { CheckCircle, X, FolderOpen, Download } from 'lucide-react';

interface CompletionModalProps {
  isOpen: boolean;
  totalProcessed: number;
  userPath?: string;
  onFinish: () => void;
  onLoadMore: () => void;
}

const CompletionModal: React.FC<CompletionModalProps> = ({
  isOpen,
  totalProcessed,
  userPath,
  onFinish,
  onLoadMore
}) => {
  
  // Función para abrir la carpeta a través del backend
  const abrirCarpeta = async () => {
    if (!userPath) {
      alert('No se pudo determinar la ruta de la carpeta');
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/abrir-carpeta", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ 
          ruta: userPath 
        })
      });

      const resultado = await response.json();
      
      if (!resultado.success) {
        throw new Error(resultado.error || 'Error al abrir carpeta');
      }
      
      console.log('Carpeta abierta exitosamente');
      
    } catch (error) {
      console.error('Error al abrir carpeta:', error);
      alert('No se pudo abrir la carpeta: ' + error.message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Proceso Completado
              </h2>
            </div>
          </div>
          <button
            onClick={onFinish}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="text-center mb-6">
          <p className="text-gray-600 mb-4">
            Se procesaron exitosamente {totalProcessed} archivos para firma digital
          </p>

          {/* Botón clickeable para abrir carpeta */}
          {userPath && (
            <button
              onClick={abrirCarpeta}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 hover:bg-green-100 
                         border border-green-200 rounded-lg transition-colors duration-200
                         text-green-700 hover:text-green-800 font-medium cursor-pointer
                         hover:shadow-md transform hover:scale-105"
            >
              <FolderOpen className="w-4 h-4" />
              <span>Archivos guardados en {userPath}</span>
            </button>
          )}
          
          {userPath && (
            <p className="text-xs text-gray-500 mt-2">
              Haz clic para abrir la carpeta
            </p>
          )}
        </div>

        {/* Botones de acción */}
        <div className="space-y-3">
          <button
            onClick={onLoadMore}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 
                       bg-blue-600 hover:bg-blue-700 text-white font-medium 
                       rounded-lg transition-colors duration-200"
          >
            <Download className="w-4 h-4" />
            Cargar más archivos
          </button>

          <button
            onClick={onFinish}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 
                       bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium 
                       rounded-lg transition-colors duration-200 border"
          >
            <X className="w-4 h-4" />
            Finalizar
          </button>
        </div>

        {/* Nota informativa */}
        <p className="text-xs text-gray-500 text-center mt-4">
          Al finalizar se cerrarán todas las ventanas y se detendrá el proceso
        </p>
      </div>
    </div>
  );
};

export default CompletionModal;