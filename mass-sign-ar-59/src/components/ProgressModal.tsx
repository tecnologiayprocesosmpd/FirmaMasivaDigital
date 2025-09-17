import React from 'react';
import { FileText, Clock } from 'lucide-react';

interface ProgressModalProps {
  isOpen: boolean;
  currentFile: number;
  totalFiles: number;
  currentFileName: string;
  progressMessage: string;
  responsable?: string;
}

const ProgressModal: React.FC<ProgressModalProps> = ({
  isOpen,
  currentFile,
  totalFiles,
  currentFileName,
  progressMessage,
  responsable
}) => {
  if (!isOpen) return null;

  const progressPercentage = totalFiles > 0 ? Math.round((currentFile / totalFiles) * 100) : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-full">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Procesando Documentos</h3>
                {responsable && (
                  <p className="text-sm text-gray-600">Usuario: {responsable}</p>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>{currentFile} de {totalFiles} archivos</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Progreso</span>
              <span className="text-sm font-bold text-blue-600">{progressPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500 ease-in-out shadow-sm"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          {/* Current Status */}
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <p className="text-sm font-medium text-blue-800 mb-1">Estado actual:</p>
            <p className="text-sm text-blue-700">{progressMessage}</p>
          </div>

          {/* Current File */}
          {currentFileName && (
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-800 mb-1">Archivo en proceso:</p>
              <p className="text-sm text-gray-600 truncate" title={currentFileName}>
                {currentFileName}
              </p>
            </div>
          )}

          {/* Warning */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Por favor, no cierre esta ventana hasta completar el proceso
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressModal;