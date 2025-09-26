import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Smartphone, PenTool } from 'lucide-react';

interface OTPModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (otp: string) => void;
  isProcessing?: boolean;
}

const OTPModal: React.FC<OTPModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isProcessing = false
}) => {
  const [otp, setOtp] = useState('');

  // Limpiar el campo OTP cada vez que se abre el modal
  useEffect(() => {
    if (isOpen) {
      setOtp('');
    }
  }, [isOpen]);

  const handleOTPChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(value);
  };

  const handleConfirm = () => {
    if (otp.length === 6) {
      onConfirm(otp);
    }
  };

  // Manejar Enter en el input
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && otp.length === 6 && !isProcessing) {
      handleConfirm();
    }
  };

  const handleClose = () => {
    if (!isProcessing) {
      setOtp('');
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <div className="p-2 bg-primary/10 rounded-full">
              <Smartphone className="h-5 w-5 text-primary" />
            </div>
            <span>Código de Verificación</span>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Ingrese el código OTP de 6 dígitos obtenido en su aplicación autenticadora
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="modal-otp" className="text-sm font-medium">
              Código OTP
            </Label>
            <Input
              id="modal-otp"
              type="text"
              placeholder="123456"
              value={otp}
              onChange={handleOTPChange}
              onKeyPress={handleKeyPress}
              maxLength={6}
              className="text-center text-lg tracking-wider font-mono"
              autoFocus
              disabled={isProcessing}
              autoComplete="off"        // ← Esto elimina las sugerencias
              name="otp-unique"         // ← Nombre único para evitar historial
            />
            <p className="text-xs text-muted-foreground text-center">
              {otp.length}/6 dígitos
            </p>    
          </div>

          <div className="flex space-x-3 pt-4">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isProcessing}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={otp.length !== 6 || isProcessing}
              className="flex-1 bg-gradient-primary hover:opacity-90"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                  Firmando...
                </>
              ) : (
                <>
                  <PenTool className="h-4 w-4 mr-2" />
                  Firmar Ahora
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OTPModal;