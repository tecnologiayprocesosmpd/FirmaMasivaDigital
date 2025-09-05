import React, { useCallback, useState } from 'react';
import { Upload, X, FileText, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: string;
}

interface FileUploadProps {
  onFilesChange: (files: File[]) => void;
  files: File[];
}

const FileUpload: React.FC<FileUploadProps> = ({ onFilesChange, files }) => {
  const [dragActive, setDragActive] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file: File): boolean => {
    const maxSize = 14 * 1024 * 1024; // 14MB
    if (file.type !== 'application/pdf') {
      alert('Solo se permiten archivos PDF');
      return false;
    }
    if (file.size > maxSize) {
      alert('El archivo excede el tamaño máximo de 14MB');
      return false;
    }
    return true;
  };

  const handleFiles = useCallback((fileList: FileList) => {
    const validFiles: File[] = [];
    
    Array.from(fileList).forEach(file => {
      if (validateFile(file)) {
        // Check if file already exists
        const fileExists = files.some(existingFile => 
          existingFile.name === file.name && existingFile.size === file.size
        );
        if (!fileExists) {
          validFiles.push(file);
        }
      }
    });

    if (validFiles.length > 0) {
      onFilesChange([...files, ...validFiles]);
    }
  }, [files, onFilesChange]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
      e.dataTransfer.clearData();
    }
  }, [handleFiles]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const removeFile = useCallback((index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  }, [files, onFilesChange]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Upload Panel */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Cargar Archivos PDF</h3>
        
        <div
          className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200 ${
            dragActive 
              ? 'border-primary bg-accent' 
              : 'border-border hover:border-primary/50 hover:bg-accent/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="fileInput"
            multiple
            accept=".pdf,application/pdf"
            onChange={handleInputChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="flex flex-col items-center space-y-3">
            <div className="p-3 bg-primary/10 rounded-full">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground mb-1">
                Arrastra archivos PDF aquí
              </p>
              <p className="text-sm text-muted-foreground">
                Máximo 14MB por archivo
              </p>
            </div>
            <Button variant="secondary" size="sm">
              Seleccionar Archivos
            </Button>
          </div>
        </div>
      </Card>

      {/* Loaded Files Panel */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-foreground">
            Archivos Cargados ({files.length})
          </h4>
          {files.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onFilesChange([])}
              className="text-destructive hover:text-destructive"
            >
              Limpiar Todo
            </Button>
          )}
        </div>
        
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center bg-accent/30 rounded-lg border-2 border-dashed border-border">
            <FileText className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              No hay archivos cargados
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 bg-accent/50 rounded-lg border"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="p-2 bg-primary/10 rounded">
                    <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-foreground truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <CheckCircle className="h-4 w-4 text-success" />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="text-destructive hover:text-destructive p-1 h-6 w-6"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default FileUpload;