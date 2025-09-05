import React from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, Shield, User, Key, Smartphone } from 'lucide-react';
import { Button } from '@/components/ui/button';
interface CredentialsData {
  cuil: string;
  password: string;
  pin: string;
}
interface CredentialsFormProps {
  credentials: CredentialsData;
  onCredentialsChange: (credentials: CredentialsData) => void;
  validationErrors?: {
    cuil?: boolean;
    password?: boolean;
    pin?: boolean;
  };
}
const CredentialsForm: React.FC<CredentialsFormProps> = ({
  credentials,
  onCredentialsChange,
  validationErrors = {}
}) => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [showPin, setShowPin] = React.useState(false);
  const formatCUIL = (value: string) => {
    // Remove all non-numeric characters
    const numeric = value.replace(/\D/g, '');

    // Apply CUIL format: XX-XXXXXXXX-X
    if (numeric.length <= 2) {
      return numeric;
    } else if (numeric.length <= 10) {
      return `${numeric.slice(0, 2)}-${numeric.slice(2)}`;
    } else {
      return `${numeric.slice(0, 2)}-${numeric.slice(2, 10)}-${numeric.slice(10, 11)}`;
    }
  };
  const handleCUILChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCUIL(e.target.value);
    if (formatted.replace(/\D/g, '').length <= 11) {
      onCredentialsChange({
        ...credentials,
        cuil: formatted
      });
    }
  };
  const handleChange = (field: keyof CredentialsData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onCredentialsChange({
      ...credentials,
      [field]: value
    });
  };
  const validateCUIL = (cuil: string): boolean => {
    const numeric = cuil.replace(/\D/g, '');
    return numeric.length === 11;
  };
  const isValidForm = () => {
    return validateCUIL(credentials.cuil) && credentials.password.length >= 1 && credentials.pin.length >= 1;
  };
  return <Card className="p-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-3 bg-primary/10 rounded-full">
          <Shield className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            Credenciales FirmAR.gob.ar
          </h3>
          <p className="text-sm text-muted-foreground">
            Complete todos los campos para habilitar la firma
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* CUIL Field */}
        <div className="space-y-2">
          <Label htmlFor="cuil" className="text-sm font-medium text-foreground flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span>CUIL</span>
            {validationErrors.cuil && <span className="text-destructive">*</span>}
          </Label>
          <Input 
            id="cuil" 
            type="text" 
            placeholder="XX-XXXXXXXX-X" 
            value={credentials.cuil} 
            onChange={handleCUILChange} 
            className={`${(credentials.cuil && !validateCUIL(credentials.cuil)) || validationErrors.cuil ? 'border-destructive focus:ring-destructive' : ''}`} 
          />
          {validationErrors.cuil && (
            <p className="text-xs text-destructive font-medium">
              Complete el CUIL (11 dígitos)
            </p>
          )}
          {credentials.cuil && !validateCUIL(credentials.cuil) && !validationErrors.cuil && (
            <p className="text-xs text-destructive">
              El CUIL debe tener 11 dígitos
            </p>
          )}
        </div>

        {/* Password Field */}
        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-medium text-foreground flex items-center space-x-2">
            <Key className="h-4 w-4" />
            <span>Contraseña</span>
            {validationErrors.password && <span className="text-destructive">*</span>}
          </Label>
          <div className="relative">
            <Input 
              id="password" 
              type={showPassword ? 'text' : 'password'} 
              placeholder="Ingrese su contraseña" 
              value={credentials.password} 
              onChange={handleChange('password')} 
              className={`pr-10 ${validationErrors.password ? 'border-destructive focus:ring-destructive' : ''}`}
            />
            <Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3 hover:bg-transparent" onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? <EyeOff className="h-4 w-4 text-muted-foreground" /> : <Eye className="h-4 w-4 text-muted-foreground" />}
            </Button>
          </div>
          {validationErrors.password && (
            <p className="text-xs text-destructive font-medium">
              Complete la contraseña
            </p>
          )}
        </div>

        {/* PIN Field */}
        <div className="space-y-2">
          <Label htmlFor="pin" className="text-sm font-medium text-foreground flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>PIN</span>
            {validationErrors.pin && <span className="text-destructive">*</span>}
          </Label>
          <div className="relative">
            <Input 
              id="pin" 
              type={showPin ? 'text' : 'password'} 
              placeholder="Ingrese su PIN" 
              value={credentials.pin} 
              onChange={handleChange('pin')} 
              className={`pr-10 ${validationErrors.pin ? 'border-destructive focus:ring-destructive' : ''}`}
            />
            <Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3 hover:bg-transparent" onClick={() => setShowPin(!showPin)}>
              {showPin ? <EyeOff className="h-4 w-4 text-muted-foreground" /> : <Eye className="h-4 w-4 text-muted-foreground" />}
            </Button>
          </div>
          {validationErrors.pin && (
            <p className="text-xs text-destructive font-medium">
              Complete el PIN
            </p>
          )}
        </div>
      </div>

      {/* Validation Summary */}
      
    </Card>;
};
export default CredentialsForm;