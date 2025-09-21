import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import { Input } from './Input';
import { Modal } from './Modal';
import { Card } from './Card';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../hooks/useI18n';
import { RouteSelector } from './RouteSelector';

interface BulkRouteOperationsProps {
  isOpen: boolean;
  onClose: () => void;
  onOperationComplete: () => void;
}

interface ImportResult {
  success: boolean;
  imported_count: number;
  errors: string[];
  warnings: string[];
}

export const BulkRouteOperations: React.FC<BulkRouteOperationsProps> = ({
  isOpen,
  onClose,
  onOperationComplete,
}) => {
  const { t } = useI18n();
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [activeTab, setActiveTab] = useState<'import' | 'export'>('import');
  const [importFormat, setImportFormat] = useState<'csv' | 'geojson'>('csv');
  const [exportFormat, setExportFormat] = useState<'csv' | 'geojson' | 'json'>('csv');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importData, setImportData] = useState('');
  const [validateOnly, setValidateOnly] = useState(false);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [includeStops, setIncludeStops] = useState(true);
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selectedRouteIds, setSelectedRouteIds] = useState<number[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Read file content for preview
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setImportData(content);
      };
      reader.readAsText(file);
    }
  };

  const handleImport = async () => {
    if (!importData && !selectedFile) {
      showToast(t('bulk.import.no_data'), 'error');
      return;
    }

    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/admin/routes/bulk-import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          format: importFormat,
          data: importData,
          validate_only: validateOnly,
          overwrite_existing: overwriteExisting,
        }),
      });

      if (response.ok) {
        const result: ImportResult = await response.json();
        setImportResult(result);
        
        if (result.success) {
          showToast(
            validateOnly 
              ? t('bulk.import.validation_success')
              : t('bulk.import.success', { count: result.imported_count }),
            'success'
          );
          
          if (!validateOnly) {
            onOperationComplete();
          }
        } else {
          showToast(t('bulk.import.failed'), 'error');
        }
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Import failed');
      }
    } catch (error) {
      showToast(
        `${t('bulk.import.error')}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/admin/routes/bulk-export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          format: exportFormat,
          route_ids: selectedRouteIds.length > 0 ? selectedRouteIds : null,
          include_stops: includeStops,
          include_inactive: includeInactive,
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `routes_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast(t('bulk.export.success'), 'success');
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Export failed');
      }
    } catch (error) {
      showToast(
        `${t('bulk.export.error')}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'error'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const resetImport = () => {
    setSelectedFile(null);
    setImportData('');
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('bulk.operations')}
      size="lg"
    >
      <div className="space-y-6">
        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('import')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'import'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {t('bulk.import')}
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'export'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {t('bulk.export')}
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'import' && (
            <motion.div
              key="import"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-4"
            >
              {/* Import Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('bulk.import.format')}
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="csv"
                      checked={importFormat === 'csv'}
                      onChange={(e) => setImportFormat(e.target.value as 'csv')}
                      className="mr-2"
                    />
                    CSV
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="geojson"
                      checked={importFormat === 'geojson'}
                      onChange={(e) => setImportFormat(e.target.value as 'geojson')}
                      className="mr-2"
                    />
                    GeoJSON
                  </label>
                </div>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('bulk.import.file')}
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={importFormat === 'csv' ? '.csv' : '.geojson,.json'}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="secondary"
                  >
                    {t('bulk.import.select_file')}
                  </Button>
                  {selectedFile && (
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {selectedFile.name}
                    </span>
                  )}
                  {selectedFile && (
                    <Button
                      onClick={resetImport}
                      variant="ghost"
                      size="sm"
                    >
                      {t('common.clear')}
                    </Button>
                  )}
                </div>
              </div>

              {/* Data Preview */}
              {importData && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('bulk.import.preview')}
                  </label>
                  <textarea
                    value={importData.substring(0, 500) + (importData.length > 500 ? '...' : '')}
                    readOnly
                    className="w-full h-32 p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm font-mono"
                  />
                </div>
              )}

              {/* Import Options */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={validateOnly}
                    onChange={(e) => setValidateOnly(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {t('bulk.import.validate_only')}
                  </span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={overwriteExisting}
                    onChange={(e) => setOverwriteExisting(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {t('bulk.import.overwrite_existing')}
                  </span>
                </label>
              </div>

              {/* Import Results */}
              {importResult && (
                <Card className="p-4">
                  <h4 className="font-medium mb-2">
                    {validateOnly ? t('bulk.import.validation_results') : t('bulk.import.results')}
                  </h4>
                  
                  {importResult.success && (
                    <div className="text-green-600 dark:text-green-400 mb-2">
                      ✓ {validateOnly 
                        ? t('bulk.import.validation_passed')
                        : t('bulk.import.imported', { count: importResult.imported_count })
                      }
                    </div>
                  )}

                  {importResult.errors.length > 0 && (
                    <div className="mb-2">
                      <h5 className="font-medium text-red-600 dark:text-red-400 mb-1">
                        {t('bulk.import.errors')}:
                      </h5>
                      <ul className="text-sm text-red-600 dark:text-red-400 list-disc list-inside">
                        {importResult.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {importResult.warnings.length > 0 && (
                    <div>
                      <h5 className="font-medium text-yellow-600 dark:text-yellow-400 mb-1">
                        {t('bulk.import.warnings')}:
                      </h5>
                      <ul className="text-sm text-yellow-600 dark:text-yellow-400 list-disc list-inside">
                        {importResult.warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Card>
              )}

              {/* Import Action */}
              <div className="flex justify-end">
                <Button
                  onClick={handleImport}
                  disabled={!importData || isProcessing}
                  loading={isProcessing}
                >
                  {validateOnly ? t('bulk.import.validate') : t('bulk.import.start')}
                </Button>
              </div>
            </motion.div>
          )}

          {activeTab === 'export' && (
            <motion.div
              key="export"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              {/* Export Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('bulk.export.format')}
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={(e) => setExportFormat(e.target.value as 'csv')}
                      className="mr-2"
                    />
                    CSV
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="geojson"
                      checked={exportFormat === 'geojson'}
                      onChange={(e) => setExportFormat(e.target.value as 'geojson')}
                      className="mr-2"
                    />
                    GeoJSON
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={(e) => setExportFormat(e.target.value as 'json')}
                      className="mr-2"
                    />
                    JSON
                  </label>
                </div>
              </div>

              {/* Export Options */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeStops}
                    onChange={(e) => setIncludeStops(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {t('bulk.export.include_stops')}
                  </span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeInactive}
                    onChange={(e) => setIncludeInactive(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {t('bulk.export.include_inactive')}
                  </span>
                </label>
              </div>

              {/* Route Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('bulk.export.routes')}
                </label>
                <RouteSelector
                  selectedRouteIds={selectedRouteIds}
                  onSelectionChange={setSelectedRouteIds}
                  maxHeight="200px"
                />
              </div>

              {/* Export Action */}
              <div className="flex justify-end">
                <Button
                  onClick={handleExport}
                  disabled={isProcessing}
                  loading={isProcessing}
                >
                  {t('bulk.export.start')}
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Format Help */}
        <Card className="p-4 bg-blue-50 dark:bg-blue-900/20">
          <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
            {t('bulk.format_help.title')}
          </h4>
          <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <p><strong>CSV:</strong> {t('bulk.format_help.csv')}</p>
            <p><strong>GeoJSON:</strong> {t('bulk.format_help.geojson')}</p>
            <p><strong>JSON:</strong> {t('bulk.format_help.json')}</p>
          </div>
        </Card>
      </div>
    </Modal>
  );
};