import React from 'react';
import { CheckCircle, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface CompletionModalProps {
  isOpen: boolean;
  totalProcessed: number;
  userPath?: string; // se agrega el camino de las carpetas del usuario
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
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="p-8 max-w-md w-full mx-4 shadow-xl">
        <div className="text-center space-y-6">
          {/* Icon de éxito */}
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          
          {/* Título */}
          <div>
            <h2 className="text-2xl font-bold text-foreground mb-2">
              Proceso Completado
            </h2>
            <p className="text-muted-foreground">
              Se procesaron exitosamente {totalProcessed} archivo{totalProcessed !== 1 ? 's' : ''} para firma digital
            </p>
          </div>
          
          {/* Información adicional */}
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center justify-center space-x-2 text-green-700">
              <FileText className="w-4 h-4" />
            <span className="text-sm font-medium">
              {`Archivos guardados en ${userPath || 'carpeta del usuario'}`}
            </span>
            </div>
          </div>
          
          {/* Botones de acción */}
          <div className="space-y-3">
            <Button 
              onClick={onLoadMore}
              className="w-full bg-gradient-primary hover:opacity-90"
              size="lg"
            >
              <FileText className="w-4 h-4 mr-2" />
              Cargar más archivos
            </Button>
            
            <Button 
              onClick={onFinish}
              variant="outline"
              className="w-full"
              size="lg"
            >
              <X className="w-4 h-4 mr-2" />
              Finalizar
            </Button>
          </div>
          
          {/* Nota informativa */}
          <p className="text-xs text-muted-foreground">
            Al finalizar se cerrarán todas las ventanas y se detendrá el proceso
          </p>
        </div>
      </Card>
    </div>
  );
};

export default CompletionModal;