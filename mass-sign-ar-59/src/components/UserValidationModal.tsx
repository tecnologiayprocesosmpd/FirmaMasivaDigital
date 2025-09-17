import React from 'react';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface UserValidationModalProps {
  isOpen: boolean;
  isValidating: boolean;
  isValid: boolean;
  message: string;
  userData?: {
    responsable: string;
    path_carpetas: string;
  };
  onClose: () => void;
}

const UserValidationModal: React.FC<UserValidationModalProps> = ({
  isOpen,
  isValidating,
  isValid,
  message,
  userData,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex items-center justify-center mb-4">
            {isValidating ? (
              <div className="flex items-center space-x-3">
                <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                <span className="text-lg font-semibold text-gray-700">Validando usuario...</span>
              </div>
            ) : isValid ? (
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-8 w-8 text-green-500" />
                <span className="text-lg font-semibold text-green-700">Usuario Autorizado</span>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <XCircle className="h-8 w-8 text-red-500" />
                <span className="text-lg font-semibold text-red-700">Acceso Denegado</span>
              </div>
            )}
          </div>

          <div className="text-center mb-6">
            <p className="text-gray-600 mb-2">{message}</p>
            {userData && (
              <div className="bg-green-50 p-3 rounded-lg mt-3">
                <p className="text-sm font-medium text-green-800">
                  Responsable: {userData.responsable}
                </p>
                <p className="text-sm text-green-600">
                  Carpeta: {userData.path_carpetas}
                </p>
              </div>
            )}
          </div>

          {!isValidating && (
            <div className="flex justify-center">
              <button
                onClick={onClose}
                className={`px-6 py-2 rounded-lg font-semibold ${
                  isValid
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-red-500 hover:bg-red-600 text-white'
                }`}
              >
                {isValid ? 'Continuar' : 'Entendido'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserValidationModal;