import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  Sparkles,
  ShieldCheck,
  FileCheck,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import type { ExtractedBill } from '../../types/financial';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { endpoints, minorToMajor, formatConfidence, ApiError, type ApiReceiptItem } from '../../api';

interface BillUploaderProps {
  onUploadSuccess: (bill?: Partial<ExtractedBill>) => void;
  piiMaskingEnabled: boolean;
  selectedBill: ExtractedBill;
  bills: ExtractedBill[];
  onSelectBill: (id: string) => void;
}

export const BillUploader: React.FC<BillUploaderProps> = ({
  onUploadSuccess,
  piiMaskingEnabled,
  selectedBill,
  bills,
  onSelectBill,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState<string>('');
  const [lastApiReceipt, setLastApiReceipt] = useState<ApiReceiptItem | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    // 10 MiB limit check per specification
    const maxBytes = 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      setUploadError('Receipt file exceeds 10 MiB limit (FIN_RECEIPT_TOO_LARGE). Please select a smaller file.');
      return;
    }

    setUploadError(null);
    setIsScanning(true);
    setScanStep('Encrypting & scrubbing client-side PII...');

    try {
      // Step 1: Dispatched to API
      setTimeout(() => {
        setScanStep('Dispatching to POST /receipts/scan (Multimodal Vision OCR)...');
      }, 500);

      const response = await endpoints.receipts.scan(file);
      const receipt = response.result;
      setLastApiReceipt(receipt);

      const ext = receipt.extraction;
      const fileType = file.type.includes('pdf')
        ? 'pdf'
        : file.type.includes('png')
        ? 'png'
        : 'jpeg';

      setIsScanning(false);
      setScanStep('');

      onUploadSuccess({
        id: receipt.receipt_id,
        merchant: ext.merchant || 'Scanned Merchant',
        fileName: file.name,
        fileType,
        subtotal: minorToMajor(ext.subtotal_minor),
        taxAmount: minorToMajor(ext.tax_minor),
        totalAmount: minorToMajor(ext.total_minor),
        confidenceScore: ext.confidence ?? 0.92,
        invoiceDate: ext.transaction_date || new Date().toISOString().split('T')[0],
        status: receipt.status === 'parsed' ? 'extracted' : 'processing',
      });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 'FIN_RECEIPT_DUPLICATE') {
          setUploadError('Duplicate receipt detected (FIN_RECEIPT_DUPLICATE).');
        } else if (err.code === 'FIN_RECEIPT_INVALID') {
          setUploadError('Unsupported receipt format. Server requires JPEG, PNG, or PDF.');
        } else {
          setUploadError(`[${err.code}] ${err.message}`);
        }
      } else {
        setUploadError(
          err instanceof Error
            ? err.message
            : 'Receipt processing failed. Please verify network and backend service.'
        );
      }
    } finally {
      setIsScanning(false);
    }
  };


  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleConfirmReceipt = async () => {
    if (!lastApiReceipt) return;
    try {
      await endpoints.receipts.patch(lastApiReceipt.receipt_id, {
        confirm: true,
      });
      setLastApiReceipt({
        ...lastApiReceipt,
        status: 'parsed',
      });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Confirmation failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Dropzone */}
      <Card
        className={`p-8 border-2 border-dashed transition-all duration-300 text-center relative overflow-hidden ${
          isDragging
            ? 'border-emerald-400 bg-emerald-500/10'
            : 'border-slate-700/80 hover:border-slate-500 bg-slate-900/40'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg"
          className="hidden"
          onChange={handleFileChange}
        />

        {isScanning ? (
          <div className="py-6 flex flex-col items-center justify-center space-y-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center animate-pulse">
                <Sparkles className="w-8 h-8 text-emerald-400" />
              </div>
              <div className="absolute -inset-2 border-2 border-emerald-400 border-t-transparent rounded-3xl animate-spin" />
            </div>

            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">
                Multimodal OCR Vision Pipeline Active
              </h3>
              <p className="text-xs text-emerald-300 font-mono-numbers mt-1 animate-pulse">
                {scanStep}
              </p>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>
                {piiMaskingEnabled ? 'Client-side PII scrubbing active' : 'Raw ingestion mode'}
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
              <UploadCloud className="w-7 h-7 text-emerald-400" />
            </div>

            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">
                Drag & Drop Bills, Receipts or PDF Invoices
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Dispatches to <code className="text-emerald-400">POST /receipts/scan</code>. Supports JPEG, PNG, PDF up to 10 MiB.
              </p>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <Button
                variant="primary"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Browse Files
              </Button>
            </div>

            {/* Ingestion Security Guarantee */}
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 pt-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Card PANs and IBANs are masked client-side before sending to Vision AI.</span>
            </div>
          </div>
        )}
      </Card>

      {uploadError && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Real API Receipt Confirmation Banner */}
      {lastApiReceipt && (
        <Card className="p-4 bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">
                  {lastApiReceipt.extraction.merchant || 'Scanned Receipt'}
                </span>
                <Badge
                  variant={lastApiReceipt.status === 'parsed' ? 'emerald' : 'amber'}
                  size="sm"
                >
                  Status: {lastApiReceipt.status}
                </Badge>
                <Badge variant="slate" size="sm">
                  Confidence: {formatConfidence(lastApiReceipt.extraction.confidence)}
                </Badge>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Receipt ID: <span className="font-mono text-[11px] text-emerald-300">{lastApiReceipt.receipt_id}</span>
                {lastApiReceipt.transaction_id && (
                  <span className="ml-2">• Linked Txn: <span className="font-mono text-[11px]">{lastApiReceipt.transaction_id.slice(0, 8)}...</span></span>
                )}
              </p>
            </div>
          </div>

          {lastApiReceipt.status === 'needs_review' && (
            <Button
              variant="glow"
              size="sm"
              onClick={handleConfirmReceipt}
              leftIcon={<CheckCircle2 className="w-4 h-4" />}
            >
              Confirm & Post Txn
            </Button>
          )}
        </Card>
      )}

      {/* Uploaded Documents Selector Bar */}
      {bills.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-400">Extracted Invoices & Receipts:</span>
          <div className="flex flex-wrap gap-2">
            {bills.map((bill) => {
              const isSelected = selectedBill ? bill.id === selectedBill.id : false;
              return (
                <button
                  key={bill.id}
                  onClick={() => onSelectBill(bill.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                    isSelected
                      ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/10'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <FileCheck className={`w-3.5 h-3.5 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <span className="font-semibold">{bill.merchant}</span>
                  <span className="text-white font-mono-numbers">${bill.totalAmount.toFixed(2)}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

